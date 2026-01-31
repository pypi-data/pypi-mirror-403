"""Configuration for AFIR SDK."""

from dataclasses import dataclass
from typing import Optional, List


@dataclass
class AFIRConfig:
    """
    Configuration for the AFIR SDK client.
    
    Args:
        api_key: Your API key from the AFIR dashboard
        endpoint: Base URL for the AFIR API (default: localhost for dev)
        service_name: Name of your service (defaults to detecting from environment)
        environment: Environment name (prod, staging, dev)
        enabled: Whether to send events (disable for testing)
        batch_size: Number of events to batch before sending
        flush_interval: Max seconds between flushes
        ignored_paths: List of paths to not track (e.g., /health, /metrics)
        min_status_code: Minimum status code to track (default: 400)
    """
    api_key: str
    endpoint: str = "http://localhost:8000/api/v1"
    service_name: str = "unknown-service"
    environment: str = "dev"
    enabled: bool = True
    batch_size: int = 10
    flush_interval: float = 5.0
    ignored_paths: Optional[List[str]] = None
    min_status_code: int = 400
    
    def __post_init__(self):
        if self.ignored_paths is None:
            self.ignored_paths = ["/health", "/healthz", "/ready", "/metrics", "/favicon.ico"]
