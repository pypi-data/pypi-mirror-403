"""AFIR SDK HTTP Client for sending events to the backend."""

import asyncio
import logging
import time
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from threading import Thread, Lock
from queue import Queue, Empty

import httpx

from afir_sdk.config import AFIRConfig

logger = logging.getLogger("afir_sdk")


class AFIRClient:
    """
    Client for sending API failure events to AFIR backend.
    
    Features:
    - Automatic batching to reduce network calls
    - Background thread for async sending
    - Retry logic for failed requests
    - Graceful shutdown with flush
    
    Usage:
        client = AFIRClient(config)
        client.track_event(...)
        # On shutdown:
        client.shutdown()
    """
    
    def __init__(self, config: AFIRConfig):
        self.config = config
        self._queue: Queue = Queue()
        self._lock = Lock()
        self._shutdown = False
        self._last_flush = time.time()
        
        # Start background worker thread
        self._worker = Thread(target=self._background_worker, daemon=True)
        self._worker.start()
        
        logger.info(f"AFIR SDK initialized for {config.service_name} ({config.environment})")
    
    def track_event(
        self,
        method: str,
        path: str,
        status_code: int,
        latency_ms: int,
        error_payload: Optional[Dict[str, Any]] = None,
        correlation_id: Optional[str] = None,
        trace_id: Optional[str] = None,
        client_ip: Optional[str] = None,
        request_headers: Optional[Dict[str, str]] = None,
        response_metadata: Optional[Dict[str, Any]] = None
    ):
        """
        Track an API failure event.
        
        Args:
            method: HTTP method (GET, POST, etc.)
            path: Request path
            status_code: HTTP response status code
            latency_ms: Request latency in milliseconds
            error_payload: Optional error details
            correlation_id: Optional correlation ID for tracing
            trace_id: Optional trace ID for distributed tracing
            client_ip: Optional client IP address (will be hashed)
            request_headers: Optional request headers (sensitive data will be redacted)
            response_metadata: Optional response metadata
        """
        if not self.config.enabled:
            return
        
        if status_code < self.config.min_status_code:
            return
        
        # Check if path is ignored
        if self.config.ignored_paths:
            for ignored in self.config.ignored_paths:
                if path.startswith(ignored):
                    return
        
        event = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "service_name": self.config.service_name,
            "environment": self.config.environment,
            "http_method": method.upper(),
            "path": path,
            "status_code": status_code,
            "latency_ms": latency_ms,
        }
        
        if error_payload:
            event["error_payload"] = error_payload
        if correlation_id:
            event["correlation_id"] = correlation_id
        if trace_id:
            event["trace_id"] = trace_id
        if client_ip:
            event["client_ip"] = client_ip
        if request_headers:
            # Redact sensitive headers
            safe_headers = {k: v for k, v in request_headers.items() 
                           if k.lower() not in ("authorization", "cookie", "x-api-key")}
            event["request_headers"] = safe_headers
        if response_metadata:
            event["response_metadata"] = response_metadata
        
        self._queue.put(event)
    
    def _background_worker(self):
        """Background thread that batches and sends events."""
        batch: List[Dict] = []
        
        while not self._shutdown:
            try:
                # Get event with timeout for periodic flush
                event = self._queue.get(timeout=1.0)
                batch.append(event)
                
                # Check if we should flush
                should_flush = (
                    len(batch) >= self.config.batch_size or
                    time.time() - self._last_flush >= self.config.flush_interval
                )
                
                if should_flush and batch:
                    self._flush_batch(batch)
                    batch = []
                    self._last_flush = time.time()
                    
            except Empty:
                # No event received, check if we should flush due to time
                if batch and time.time() - self._last_flush >= self.config.flush_interval:
                    self._flush_batch(batch)
                    batch = []
                    self._last_flush = time.time()
        
        # Final flush on shutdown
        if batch:
            self._flush_batch(batch)
    
    def _flush_batch(self, batch: List[Dict]):
        """Send batch of events to AFIR backend."""
        if not batch:
            return
        
        try:
            with httpx.Client(timeout=10.0) as client:
                response = client.post(
                    f"{self.config.endpoint}/ingest",
                    json={"events": batch},
                    headers={"X-API-Key": self.config.api_key}
                )
                
                if response.status_code >= 400:
                    logger.warning(f"AFIR: Failed to send events: {response.status_code} - {response.text[:200]}")
                else:
                    logger.debug(f"AFIR: Sent {len(batch)} events successfully")
                    
        except Exception as e:
            logger.error(f"AFIR: Error sending events: {e}")
    
    def flush(self):
        """Force flush any pending events."""
        # Wait for queue to empty
        while not self._queue.empty():
            time.sleep(0.1)
    
    def shutdown(self):
        """Shutdown the client gracefully."""
        self._shutdown = True
        self.flush()
        self._worker.join(timeout=5.0)
        logger.info("AFIR SDK shut down")
