"""gRPC interceptor that adds path prefix to :path pseudo-header.

Usage:
    interceptor = create_path_prefix_interceptor("user123")
    channel = grpc.intercept_channel(channel, interceptor)

Effect:
    Original :path: /echo.EchoService/Echo
    Modified :path: /grpc/user123/echo.EchoService/Echo
"""

import collections

import grpc

from . import generic_client_interceptor


class _ClientCallDetails(
    collections.namedtuple("_ClientCallDetails", ("method", "timeout", "metadata", "credentials")),
    grpc.ClientCallDetails,
):
    """Custom ClientCallDetails that allows method modification."""

    pass


def create_path_prefix_interceptor(user_id: str, prefix: str = "/grpc"):
    """Create an interceptor that adds path prefix to gRPC method.

    Args:
        user_id: User identifier to include in path
        prefix: Path prefix (default: "/grpc")

    Returns:
        gRPC interceptor that modifies :path to {prefix}/{user_id}{original_method}
    """

    def intercept_call(
        client_call_details, request_iterator, _request_streaming, _response_streaming
    ):
        # Original method: /echo.EchoService/Echo
        # Modified method: /grpc/user123/echo.EchoService/Echo
        new_method = f"{prefix}/{user_id}{client_call_details.method}"

        new_details = _ClientCallDetails(
            new_method,
            client_call_details.timeout,
            client_call_details.metadata,
            client_call_details.credentials,
        )
        return new_details, request_iterator, None

    return generic_client_interceptor.create(intercept_call)
