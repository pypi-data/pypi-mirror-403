"""
AFIR SDK - Python SDK for API Failure Recorder

A lightweight SDK for monitoring and tracking API failures
in your FastAPI, Flask, or other Python web applications.
"""

from afir_sdk.client import AFIRClient
from afir_sdk.config import AFIRConfig

__version__ = "0.1.0"
__all__ = ["AFIRClient", "AFIRConfig"]
