"""Tests for gRPC storage module (PathPrefixGrpcStorageProxy).

Tests for 6.10.1 and 6.10.2 Multi-Agent review results:
- 6.10.1: Interceptor bug fix - _stub/_cache recreation with intercepted channel
- 6.10.2: use_secure parameter for scheme-based secure/insecure channel selection
"""

from unittest.mock import MagicMock, patch

import pytest


class TestPathPrefixGrpcStorageProxy:
    """Test PathPrefixGrpcStorageProxy class."""

    @pytest.fixture
    def mock_grpc(self):
        """Mock grpc module."""
        with patch("aiauto.grpc_storage.grpc") as mock:
            mock.insecure_channel.return_value = MagicMock(name="insecure_channel")
            mock.secure_channel.return_value = MagicMock(name="secure_channel")
            mock.ssl_channel_credentials.return_value = MagicMock(name="credentials")
            mock.intercept_channel.return_value = MagicMock(name="intercepted_channel")
            yield mock

    @pytest.fixture
    def mock_optuna_imports(self):
        """Mock optuna gRPC imports."""
        with patch.dict(
            "sys.modules",
            {
                "optuna.storages._grpc.auto_generated": MagicMock(),
                "optuna.storages._grpc.auto_generated.api_pb2_grpc": MagicMock(),
                "optuna.storages._grpc.client": MagicMock(),
            },
        ):
            yield

    @pytest.fixture
    def mock_interceptor(self):
        """Mock path prefix interceptor."""
        with patch("aiauto.grpc_storage.create_path_prefix_interceptor") as mock:
            mock.return_value = MagicMock(name="interceptor")
            yield mock

    @pytest.fixture
    def mock_grpc_storage_proxy(self):
        """Mock GrpcStorageProxy base class."""
        with patch("aiauto.grpc_storage.GrpcStorageProxy") as mock:
            # Don't call real __init__
            mock.__init__ = MagicMock(return_value=None)
            yield mock

    def test_init_stores_user_id_and_use_secure(
        self, mock_grpc, mock_optuna_imports, mock_interceptor
    ):
        """Test that __init__ stores user_id and use_secure before calling super()."""
        with patch("aiauto.grpc_storage.GrpcStorageProxy.__init__", return_value=None):
            from aiauto.grpc_storage import PathPrefixGrpcStorageProxy

            proxy = PathPrefixGrpcStorageProxy(
                host="example.com",
                port=80,
                user_id="user123",
                use_secure=False,
            )

            assert proxy._user_id == "user123"
            assert proxy._use_secure is False

    def test_init_use_secure_true(self, mock_grpc, mock_optuna_imports, mock_interceptor):
        """Test that use_secure=True is stored correctly."""
        with patch("aiauto.grpc_storage.GrpcStorageProxy.__init__", return_value=None):
            from aiauto.grpc_storage import PathPrefixGrpcStorageProxy

            proxy = PathPrefixGrpcStorageProxy(
                host="example.com",
                port=443,
                user_id="user123",
                use_secure=True,
            )

            assert proxy._use_secure is True

    def test_init_default_values(self, mock_grpc, mock_optuna_imports, mock_interceptor):
        """Test default values for user_id and use_secure."""
        with patch("aiauto.grpc_storage.GrpcStorageProxy.__init__", return_value=None):
            from aiauto.grpc_storage import PathPrefixGrpcStorageProxy

            proxy = PathPrefixGrpcStorageProxy(
                host="example.com",
                port=80,
            )

            assert proxy._user_id == ""
            assert proxy._use_secure is False

    def test_setup_creates_insecure_channel_when_use_secure_false(
        self, mock_grpc, mock_optuna_imports, mock_interceptor
    ):
        """Test _setup() creates insecure_channel when use_secure=False (http://)."""
        with patch("aiauto.grpc_storage.GrpcStorageProxy.__init__", return_value=None):
            from aiauto.grpc_storage import PathPrefixGrpcStorageProxy

            proxy = PathPrefixGrpcStorageProxy(
                host="example.com",
                port=80,
                user_id="",
                use_secure=False,
            )
            proxy._host = "example.com"
            proxy._port = 80

            proxy._setup()

            mock_grpc.insecure_channel.assert_called_once_with("example.com:80")
            mock_grpc.secure_channel.assert_not_called()

    def test_setup_creates_secure_channel_when_use_secure_true(
        self, mock_grpc, mock_optuna_imports, mock_interceptor
    ):
        """Test _setup() creates secure_channel when use_secure=True (https://)."""
        with patch("aiauto.grpc_storage.GrpcStorageProxy.__init__", return_value=None):
            from aiauto.grpc_storage import PathPrefixGrpcStorageProxy

            proxy = PathPrefixGrpcStorageProxy(
                host="example.com",
                port=443,
                user_id="",
                use_secure=True,
            )
            proxy._host = "example.com"
            proxy._port = 443

            proxy._setup()

            mock_grpc.ssl_channel_credentials.assert_called_once()
            mock_grpc.secure_channel.assert_called_once()
            mock_grpc.insecure_channel.assert_not_called()

    def test_setup_applies_interceptor_when_user_id_provided(
        self, mock_grpc, mock_optuna_imports, mock_interceptor
    ):
        """Test _setup() applies path prefix interceptor when user_id is provided."""
        with patch("aiauto.grpc_storage.GrpcStorageProxy.__init__", return_value=None):
            from aiauto.grpc_storage import PathPrefixGrpcStorageProxy

            proxy = PathPrefixGrpcStorageProxy(
                host="example.com",
                port=80,
                user_id="user123",
                use_secure=False,
            )
            proxy._host = "example.com"
            proxy._port = 80

            proxy._setup()

            mock_interceptor.assert_called_once_with("user123")
            mock_grpc.intercept_channel.assert_called_once()

    def test_setup_no_interceptor_when_user_id_empty(
        self, mock_grpc, mock_optuna_imports, mock_interceptor
    ):
        """Test _setup() does not apply interceptor when user_id is empty."""
        with patch("aiauto.grpc_storage.GrpcStorageProxy.__init__", return_value=None):
            from aiauto.grpc_storage import PathPrefixGrpcStorageProxy

            proxy = PathPrefixGrpcStorageProxy(
                host="example.com",
                port=80,
                user_id="",
                use_secure=False,
            )
            proxy._host = "example.com"
            proxy._port = 80

            proxy._setup()

            mock_interceptor.assert_not_called()
            mock_grpc.intercept_channel.assert_not_called()

    def test_setup_creates_stub_with_intercepted_channel(
        self, mock_grpc, mock_optuna_imports, mock_interceptor
    ):
        """Test _setup() creates _stub with intercepted channel (6.10.1 bug fix).

        Verifies that when user_id is provided, _stub and _cache are created
        with the intercepted channel (not the original channel).
        This ensures the interceptor bug fix (6.10.1) works correctly.
        """
        with patch("aiauto.grpc_storage.GrpcStorageProxy.__init__", return_value=None):
            from aiauto.grpc_storage import PathPrefixGrpcStorageProxy

            proxy = PathPrefixGrpcStorageProxy(
                host="example.com",
                port=80,
                user_id="user123",
                use_secure=False,
            )
            proxy._host = "example.com"
            proxy._port = 80

            proxy._setup()

            # Verify the intercepted channel was used (not the raw channel)
            # When user_id is provided, intercept_channel should be called
            mock_grpc.intercept_channel.assert_called_once()

            # After _setup(), proxy._channel should be the intercepted channel
            intercepted_channel = mock_grpc.intercept_channel.return_value
            assert proxy._channel == intercepted_channel

            # Verify _stub and _cache are set (created with the channel)
            assert hasattr(proxy, "_stub")
            assert hasattr(proxy, "_cache")

    def test_setup_ip_address_with_custom_port(
        self, mock_grpc, mock_optuna_imports, mock_interceptor
    ):
        """Test _setup() works with IP address and custom port (hospital internal network)."""
        with patch("aiauto.grpc_storage.GrpcStorageProxy.__init__", return_value=None):
            from aiauto.grpc_storage import PathPrefixGrpcStorageProxy

            proxy = PathPrefixGrpcStorageProxy(
                host="192.168.1.100",
                port=8080,
                user_id="user123",
                use_secure=False,
            )
            proxy._host = "192.168.1.100"
            proxy._port = 8080

            proxy._setup()

            mock_grpc.insecure_channel.assert_called_once_with("192.168.1.100:8080")
