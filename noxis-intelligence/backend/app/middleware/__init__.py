"""
NOXIS Intelligence - Middleware Module
"""
from app.middleware.audit_logging import AuditLoggingMiddleware

__all__ = [
    "AuditLoggingMiddleware",
]
