"""Tests for path_prefix_interceptor module."""

from unittest.mock import MagicMock

from aiauto.path_prefix_interceptor import _ClientCallDetails, create_path_prefix_interceptor


class TestClientCallDetails:
    """Test _ClientCallDetails namedtuple."""

    def test_create_with_all_fields(self):
        """Test _ClientCallDetails creation with all fields."""
        details = _ClientCallDetails(
            method="/test.Service/Method",
            timeout=30.0,
            metadata=[("key", "value")],
            credentials=None,
        )
        assert details.method == "/test.Service/Method"
        assert details.timeout == 30.0
        assert details.metadata == [("key", "value")]
        assert details.credentials is None


class TestCreatePathPrefixInterceptor:
    """Test create_path_prefix_interceptor function."""

    def test_returns_interceptor(self):
        """Test that function returns an interceptor."""
        interceptor = create_path_prefix_interceptor("user123")
        assert interceptor is not None
        # Should have all intercept methods from _GenericClientInterceptor
        assert hasattr(interceptor, "intercept_unary_unary")
        assert hasattr(interceptor, "intercept_unary_stream")
        assert hasattr(interceptor, "intercept_stream_unary")
        assert hasattr(interceptor, "intercept_stream_stream")

    def test_interceptor_modifies_method_path(self):
        """Test that interceptor modifies the gRPC method path."""
        interceptor = create_path_prefix_interceptor("user123")

        # Create mock client_call_details
        original_details = MagicMock()
        original_details.method = "/optuna.StorageService/GetStudy"
        original_details.timeout = 30.0
        original_details.metadata = None
        original_details.credentials = None

        # Create mock continuation
        continuation = MagicMock(return_value="response")

        # Call intercept_unary_unary
        result = interceptor.intercept_unary_unary(continuation, original_details, "request")

        # Verify continuation was called with modified details
        call_args = continuation.call_args[0]
        new_details = call_args[0]

        assert new_details.method == "/grpc/user123/optuna.StorageService/GetStudy"
        assert new_details.timeout == 30.0
        assert result == "response"

    def test_interceptor_with_custom_prefix(self):
        """Test interceptor with custom prefix."""
        interceptor = create_path_prefix_interceptor("user456", prefix="/custom")

        original_details = MagicMock()
        original_details.method = "/test.Service/Method"
        original_details.timeout = None
        original_details.metadata = [("auth", "token")]
        original_details.credentials = "creds"

        continuation = MagicMock(return_value="response")

        interceptor.intercept_unary_unary(continuation, original_details, "request")

        call_args = continuation.call_args[0]
        new_details = call_args[0]

        assert new_details.method == "/custom/user456/test.Service/Method"
        assert new_details.metadata == [("auth", "token")]
        assert new_details.credentials == "creds"

    def test_interceptor_preserves_metadata(self):
        """Test that interceptor preserves original metadata."""
        interceptor = create_path_prefix_interceptor("testuser")

        original_details = MagicMock()
        original_details.method = "/test.Service/Call"
        original_details.timeout = 10.0
        original_details.metadata = [("x-request-id", "abc123"), ("authorization", "Bearer token")]
        original_details.credentials = None

        continuation = MagicMock(return_value="response")

        interceptor.intercept_unary_unary(continuation, original_details, "request")

        call_args = continuation.call_args[0]
        new_details = call_args[0]

        assert new_details.metadata == [
            ("x-request-id", "abc123"),
            ("authorization", "Bearer token"),
        ]
