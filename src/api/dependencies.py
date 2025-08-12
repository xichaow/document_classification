"""
Shared dependencies for FastAPI application.

This module provides reusable dependencies for authentication, 
rate limiting, and other cross-cutting concerns.
"""

import time
import logging
from typing import Optional, Dict, Any
from fastapi import Depends, HTTPException, Request
from datetime import datetime

from ..utils.config import settings, validate_aws_credentials

logger = logging.getLogger(__name__)

# Simple rate limiting (use Redis in production)
rate_limit_storage: Dict[str, list] = {}


class RateLimiter:
    """
    Simple rate limiter for API endpoints.

    In production, use Redis or a dedicated rate limiting service.
    """

    def __init__(self, max_requests: int = 100, window_minutes: int = 60):
        """
        Initialize rate limiter.

        Args:
            max_requests: Maximum requests allowed in time window.
            window_minutes: Time window in minutes.
        """
        self.max_requests = max_requests
        self.window_seconds = window_minutes * 60

    def __call__(self, request: Request) -> bool:
        """
        Check rate limit for client.

        Args:
            request: FastAPI request object.

        Returns:
            bool: True if request is allowed.

        Raises:
            HTTPException: If rate limit exceeded.
        """
        client_ip = request.client.host
        current_time = time.time()

        # Get or create request history for client
        if client_ip not in rate_limit_storage:
            rate_limit_storage[client_ip] = []

        client_requests = rate_limit_storage[client_ip]

        # Remove old requests outside the window
        cutoff_time = current_time - self.window_seconds
        client_requests[:] = [
            req_time for req_time in client_requests if req_time > cutoff_time
        ]

        # Check if limit exceeded
        if len(client_requests) >= self.max_requests:
            raise HTTPException(
                status_code=429,
                detail=f"Rate limit exceeded. Maximum {self.max_requests} requests per {self.window_seconds/60} minutes.",
            )

        # Add current request
        client_requests.append(current_time)
        return True


# Rate limiter instances
upload_rate_limiter = RateLimiter(
    max_requests=50, window_minutes=60
)  # 50 uploads per hour
general_rate_limiter = RateLimiter(
    max_requests=200, window_minutes=60
)  # 200 requests per hour


def check_aws_credentials() -> bool:
    """
    Dependency to check AWS credentials are configured.

    Returns:
        bool: True if credentials are valid.

    Raises:
        HTTPException: If credentials are missing or invalid.
    """
    if not validate_aws_credentials():
        raise HTTPException(
            status_code=500, detail="AWS credentials not configured properly"
        )
    return True


def get_client_info(request: Request) -> Dict[str, Any]:
    """
    Extract client information from request.

    Args:
        request: FastAPI request object.

    Returns:
        Dict[str, Any]: Client information.
    """
    return {
        "ip": request.client.host,
        "user_agent": request.headers.get("user-agent", "unknown"),
        "timestamp": datetime.utcnow().isoformat(),
    }


def log_request(
    request: Request, client_info: Dict[str, Any] = Depends(get_client_info)
) -> None:
    """
    Log request information for monitoring.

    Args:
        request: FastAPI request object.
        client_info: Client information.
    """
    logger.info(
        f"Request: {request.method} {request.url.path} from {client_info['ip']}"
    )


# Optional: Simple API key authentication (disabled by default)
def verify_api_key(request: Request) -> Optional[str]:
    """
    Verify API key from request headers.

    Args:
        request: FastAPI request object.

    Returns:
        Optional[str]: API key if present, None otherwise.

    Note:
        This is a placeholder for API key authentication.
        In production, implement proper authentication.
    """
    api_key = request.headers.get("X-API-Key")

    # For demo purposes, no authentication required
    # In production, validate against your API key store
    return api_key


def get_system_status() -> Dict[str, Any]:
    """
    Get current system status for health checks.

    Returns:
        Dict[str, Any]: System status information.
    """
    return {
        "timestamp": datetime.utcnow().isoformat(),
        "aws_credentials_configured": validate_aws_credentials(),
        "max_file_size_mb": settings.MAX_FILE_SIZE / (1024 * 1024),
        "confidence_threshold": settings.CONFIDENCE_THRESHOLD,
    }


class RequestSizeValidator:
    """
    Validate request size to prevent large payloads.
    """

    def __init__(self, max_size_mb: int = 25):
        """
        Initialize size validator.

        Args:
            max_size_mb: Maximum request size in MB.
        """
        self.max_size_bytes = max_size_mb * 1024 * 1024

    async def __call__(self, request: Request) -> bool:
        """
        Validate request size.

        Args:
            request: FastAPI request object.

        Returns:
            bool: True if size is acceptable.

        Raises:
            HTTPException: If request too large.
        """
        content_length = request.headers.get("content-length")

        if content_length:
            content_length = int(content_length)
            if content_length > self.max_size_bytes:
                raise HTTPException(
                    status_code=413,
                    detail=f"Request too large. Maximum size: {self.max_size_bytes / (1024*1024):.1f}MB",
                )

        return True


# Size validator instance
request_size_validator = RequestSizeValidator(max_size_mb=25)
