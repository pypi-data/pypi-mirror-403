"""FastAPI middleware for automatic API failure tracking."""

import time
from typing import Callable, Optional

from afir_sdk.client import AFIRClient
from afir_sdk.config import AFIRConfig


def create_middleware(config: AFIRConfig) -> Callable:
    """
    Create a FastAPI/Starlette middleware for automatic API failure tracking.
    
    Usage:
        from fastapi import FastAPI
        from afir_sdk.middleware.fastapi import create_middleware
        from afir_sdk import AFIRConfig
        
        config = AFIRConfig(
            api_key="your-api-key",
            service_name="my-api",
            environment="prod"
        )
        
        app = FastAPI()
        app.middleware("http")(create_middleware(config))
    
    Args:
        config: AFIR SDK configuration
    
    Returns:
        ASGI middleware function
    """
    client = AFIRClient(config)
    
    async def middleware(request, call_next):
        start_time = time.time()
        
        # Skip ignored paths early
        path = request.url.path
        if config.ignored_paths:
            for ignored in config.ignored_paths:
                if path.startswith(ignored):
                    return await call_next(request)
        
        # Get correlation ID from headers if present
        correlation_id = request.headers.get("X-Correlation-ID") or request.headers.get("X-Request-ID")
        trace_id = request.headers.get("X-Trace-ID")
        
        # Get client IP (handle proxies)
        client_ip = request.headers.get("X-Forwarded-For", "").split(",")[0].strip()
        if not client_ip:
            client_ip = request.client.host if request.client else None
        
        # Process the request
        error_payload = None
        try:
            response = await call_next(request)
            status_code = response.status_code
        except Exception as e:
            # Capture the exception
            error_payload = {
                "exception_type": type(e).__name__,
                "exception_message": str(e)[:500]
            }
            status_code = 500
            raise  # Re-raise the exception
        finally:
            latency_ms = int((time.time() - start_time) * 1000)
            
            # Only track failures (>= min_status_code)
            if status_code >= config.min_status_code:
                # Get safe request headers
                request_headers = {}
                for key in ("content-type", "user-agent", "accept", "accept-language"):
                    if key in request.headers:
                        request_headers[key] = request.headers[key]
                
                client.track_event(
                    method=request.method,
                    path=path,
                    status_code=status_code,
                    latency_ms=latency_ms,
                    error_payload=error_payload,
                    correlation_id=correlation_id,
                    trace_id=trace_id,
                    client_ip=client_ip,
                    request_headers=request_headers
                )
        
        return response
    
    return middleware


class AFIRMiddleware:
    """
    ASGI Middleware class for FastAPI/Starlette.
    
    Alternative to the function-based middleware for more control.
    
    Usage:
        from fastapi import FastAPI
        from afir_sdk.middleware.fastapi import AFIRMiddleware
        from afir_sdk import AFIRConfig
        
        config = AFIRConfig(api_key="your-key", service_name="my-api")
        app = FastAPI()
        app.add_middleware(AFIRMiddleware, config=config)
    """
    
    def __init__(self, app, config: AFIRConfig):
        self.app = app
        self.config = config
        self.client = AFIRClient(config)
    
    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        
        from starlette.requests import Request
        from starlette.middleware.base import RequestResponseEndpoint
        
        start_time = time.time()
        path = scope.get("path", "/")
        method = scope.get("method", "GET")
        
        # Skip ignored paths
        if self.config.ignored_paths:
            for ignored in self.config.ignored_paths:
                if path.startswith(ignored):
                    await self.app(scope, receive, send)
                    return
        
        # Track response status
        response_status = [200]  # Default, will be updated
        
        async def send_wrapper(message):
            if message["type"] == "http.response.start":
                response_status[0] = message.get("status", 200)
            await send(message)
        
        error_payload = None
        try:
            await self.app(scope, receive, send_wrapper)
        except Exception as e:
            error_payload = {
                "exception_type": type(e).__name__,
                "exception_message": str(e)[:500]
            }
            response_status[0] = 500
            raise
        finally:
            latency_ms = int((time.time() - start_time) * 1000)
            
            if response_status[0] >= self.config.min_status_code:
                self.client.track_event(
                    method=method,
                    path=path,
                    status_code=response_status[0],
                    latency_ms=latency_ms,
                    error_payload=error_payload
                )
