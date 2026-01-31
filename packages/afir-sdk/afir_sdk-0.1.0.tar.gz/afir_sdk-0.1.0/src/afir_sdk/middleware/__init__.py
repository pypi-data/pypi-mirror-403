"""Middleware exports."""

from afir_sdk.middleware.fastapi import create_middleware, AFIRMiddleware

__all__ = ["create_middleware", "AFIRMiddleware"]

# Lazy imports for optional dependencies
def get_flask_middleware():
    """Get Flask middleware (requires Flask)."""
    from afir_sdk.middleware.flask import create_flask_middleware
    return create_flask_middleware
