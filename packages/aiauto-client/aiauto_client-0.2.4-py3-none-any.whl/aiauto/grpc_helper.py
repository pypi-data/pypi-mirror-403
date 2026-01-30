"""gRPC-related helper functions for AIAuto client.

This module contains gRPC-specific utilities for error handling and URL parsing.
These functions are used internally by core.py.
"""

from typing import Tuple
from urllib.parse import urlparse

from .http_client import ConnectRPCError

# gRPC URL path parsing constants
_MIN_GRPC_PATH_PARTS = 2  # /grpc/{user_id} requires at least 2 parts


def _should_retry_rpc_error(exception: Exception) -> bool:
    """Check if RPC error should be retried.

    Only ConnectRPCError with retryable codes (unavailable, failed_precondition)
    should be retried. Other exceptions (RuntimeError, etc.) should not.

    Args:
        exception: The exception to check

    Returns:
        True if the exception is a retryable RPC error, False otherwise
    """
    if isinstance(exception, ConnectRPCError):
        return exception.is_retryable()
    # Don't retry other exceptions (RuntimeError, etc.)
    return False


def _parse_grpc_url(url: str) -> Tuple[str, int, str]:
    """Parse gRPC storage URL to extract host, port, and user_id.

    Supports both path-based routing (new) and legacy host:port format.

    Path-based format:
        "https://aiauto.pangyo.ainode.ai/grpc/user123"
        -> host="aiauto.pangyo.ainode.ai", port=443, user_id="user123"

    Legacy format:
        "grpc-storage.aiauto-user.svc.cluster.local:50051"
        -> host="grpc-storage.aiauto-user.svc.cluster.local", port=50051, user_id=""

    Args:
        url: gRPC storage URL (path-based or legacy host:port)

    Returns:
        Tuple of (host, port, user_id)

    Raises:
        ValueError: If URL format is invalid
    """
    # Check if it's a URL (starts with http:// or https://)
    if url.startswith("http://") or url.startswith("https://"):
        parsed = urlparse(url)
        host = parsed.hostname or ""
        port = parsed.port or (443 if parsed.scheme == "https" else 80)

        # Extract user_id from path: /grpc/{user_id}
        # Path format: /grpc/user123 or /grpc/user123/
        path_parts = [p for p in parsed.path.split("/") if p]
        if len(path_parts) >= _MIN_GRPC_PATH_PARTS and path_parts[0] == "grpc":
            user_id = path_parts[1]
        else:
            raise ValueError(
                f"Invalid gRPC URL path: {parsed.path}. Expected format: /grpc/{{user_id}}"
            )

        return host, port, user_id

    # Legacy format: host:port
    if ":" in url:
        parts = url.rsplit(":", 1)
        host = parts[0]
        try:
            port = int(parts[1])
        except ValueError as e:
            raise ValueError(f"Invalid port in gRPC URL: {url}") from e
        return host, port, ""

    raise ValueError(
        f"Invalid gRPC URL format: {url}. Expected: https://host/grpc/user_id or host:port"
    )
