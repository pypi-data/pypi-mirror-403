"""Custom GrpcStorageProxy with path prefix interceptor for Gateway routing.

Path-based routing requires modifying gRPC :path pseudo-header to include
user ID prefix. This module provides PathPrefixGrpcStorageProxy that inherits
from optuna.storages.GrpcStorageProxy and injects the path prefix interceptor.

Example:
    # journalGrpcStorageProxyHostExternal: "http://aiauto.pangyo.ainode.ai:80/grpc/user123"
    # Parses to: host="aiauto.pangyo.ainode.ai", port=80, user_id="user123", use_secure=False
    storage = PathPrefixGrpcStorageProxy(
        host="aiauto.pangyo.ainode.ai",
        port=80,
        user_id="user123",
        use_secure=False,  # http:// → insecure, https:// → secure
    )
"""

import grpc
from optuna.storages import GrpcStorageProxy

from ._config import AIAUTO_INSECURE
from .path_prefix_interceptor import create_path_prefix_interceptor


class PathPrefixGrpcStorageProxy(GrpcStorageProxy):
    """GrpcStorageProxy with path prefix interceptor for Gateway routing.

    This class overrides _setup() to intercept the channel and add path prefix
    to all gRPC calls. The prefix format is: /grpc/{user_id}{original_method}

    Args:
        host: gRPC server hostname (without port)
        port: gRPC server port
        user_id: User identifier for path routing
        use_secure: If True, use grpc.secure_channel() (for https://)
                   If False, use grpc.insecure_channel() (for http://)
    """

    def __init__(self, host: str, port: int, user_id: str = "", use_secure: bool = False):
        self._user_id = user_id
        self._use_secure = use_secure
        super().__init__(host=host, port=port)

    def _setup(self) -> None:
        """Override to create channel with secure/insecure based on URL scheme.

        - http:// URL → use_secure=False → grpc.insecure_channel()
        - https:// URL → use_secure=True → grpc.secure_channel()

        Also injects path prefix interceptor and recreates _stub/_cache.
        """
        # Import here to avoid circular imports and keep optuna as optional dependency
        from optuna.storages._grpc.auto_generated import api_pb2_grpc
        from optuna.storages._grpc.client import GrpcClientCache

        # Create channel based on use_secure flag
        target = f"{self._host}:{self._port}"
        if self._use_secure:
            # TLS channel for https:// URLs
            if AIAUTO_INSECURE:
                # Skip SSL verification for self-signed certificates
                # Note: grpc doesn't have a direct "skip verify" option,
                # so we use empty root_certificates which accepts any cert
                credentials = grpc.ssl_channel_credentials(
                    root_certificates=None,  # Use system CA (or accept any if not available)
                )
                # Channel options to skip hostname verification
                options = [
                    ("grpc.ssl_target_name_override", self._host),
                ]
                self._channel = grpc.secure_channel(target, credentials, options=options)
            else:
                credentials = grpc.ssl_channel_credentials()
                self._channel = grpc.secure_channel(target, credentials)
        else:
            # Cleartext channel for http:// URLs
            self._channel = grpc.insecure_channel(target)

        # If user_id is provided, wrap the channel with path prefix interceptor
        if self._user_id:
            interceptor = create_path_prefix_interceptor(self._user_id)
            self._channel = grpc.intercept_channel(self._channel, interceptor)

        # Create stub and cache with the (possibly intercepted) channel
        self._stub = api_pb2_grpc.StorageServiceStub(self._channel)
        self._cache = GrpcClientCache(self._stub)
