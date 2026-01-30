"""Tests for generic_client_interceptor module."""

from unittest.mock import MagicMock

from aiauto.generic_client_interceptor import _GenericClientInterceptor, create


class TestGenericClientInterceptor:
    """Test _GenericClientInterceptor class."""

    def test_create_returns_interceptor(self):
        """Test create() returns _GenericClientInterceptor instance."""
        intercept_fn = MagicMock(return_value=(None, iter([]), None))
        interceptor = create(intercept_fn)
        assert isinstance(interceptor, _GenericClientInterceptor)

    def test_init_stores_function(self):
        """Test __init__ stores the interceptor function."""
        intercept_fn = MagicMock()
        interceptor = _GenericClientInterceptor(intercept_fn)
        assert interceptor._fn is intercept_fn

    def test_intercept_unary_unary_without_postprocess(self):
        """Test intercept_unary_unary without postprocess function."""
        new_details = MagicMock()
        new_request = "modified_request"
        intercept_fn = MagicMock(return_value=(new_details, iter([new_request]), None))
        interceptor = _GenericClientInterceptor(intercept_fn)

        continuation = MagicMock(return_value="response")
        client_call_details = MagicMock()
        request = "original_request"

        result = interceptor.intercept_unary_unary(continuation, client_call_details, request)

        assert result == "response"
        continuation.assert_called_once_with(new_details, new_request)
        intercept_fn.assert_called_once()
        # Verify request_streaming=False, response_streaming=False
        call_args = intercept_fn.call_args[0]
        assert call_args[2] is False  # request_streaming
        assert call_args[3] is False  # response_streaming

    def test_intercept_unary_unary_with_postprocess(self):
        """Test intercept_unary_unary with postprocess function."""
        new_details = MagicMock()
        postprocess = MagicMock(return_value="postprocessed_response")
        intercept_fn = MagicMock(return_value=(new_details, iter(["request"]), postprocess))
        interceptor = _GenericClientInterceptor(intercept_fn)

        continuation = MagicMock(return_value="response")
        client_call_details = MagicMock()

        result = interceptor.intercept_unary_unary(continuation, client_call_details, "request")

        assert result == "postprocessed_response"
        postprocess.assert_called_once_with("response")

    def test_intercept_unary_stream_without_postprocess(self):
        """Test intercept_unary_stream without postprocess function."""
        new_details = MagicMock()
        intercept_fn = MagicMock(return_value=(new_details, iter(["request"]), None))
        interceptor = _GenericClientInterceptor(intercept_fn)

        response_iterator = iter(["resp1", "resp2"])
        continuation = MagicMock(return_value=response_iterator)
        client_call_details = MagicMock()

        result = interceptor.intercept_unary_stream(continuation, client_call_details, "request")

        assert result is response_iterator
        # Verify request_streaming=False, response_streaming=True
        call_args = intercept_fn.call_args[0]
        assert call_args[2] is False  # request_streaming
        assert call_args[3] is True  # response_streaming

    def test_intercept_unary_stream_with_postprocess(self):
        """Test intercept_unary_stream with postprocess function."""
        new_details = MagicMock()
        postprocess = MagicMock(return_value="postprocessed")
        intercept_fn = MagicMock(return_value=(new_details, iter(["request"]), postprocess))
        interceptor = _GenericClientInterceptor(intercept_fn)

        continuation = MagicMock(return_value=iter(["resp"]))

        result = interceptor.intercept_unary_stream(continuation, MagicMock(), "request")

        assert result == "postprocessed"
        postprocess.assert_called_once()

    def test_intercept_stream_unary_without_postprocess(self):
        """Test intercept_stream_unary without postprocess function."""
        new_details = MagicMock()
        new_request_iterator = iter(["req1", "req2"])
        intercept_fn = MagicMock(return_value=(new_details, new_request_iterator, None))
        interceptor = _GenericClientInterceptor(intercept_fn)

        continuation = MagicMock(return_value="response")
        client_call_details = MagicMock()
        request_iterator = iter(["original"])

        result = interceptor.intercept_stream_unary(
            continuation, client_call_details, request_iterator
        )

        assert result == "response"
        continuation.assert_called_once_with(new_details, new_request_iterator)
        # Verify request_streaming=True, response_streaming=False
        call_args = intercept_fn.call_args[0]
        assert call_args[2] is True  # request_streaming
        assert call_args[3] is False  # response_streaming

    def test_intercept_stream_unary_with_postprocess(self):
        """Test intercept_stream_unary with postprocess function."""
        new_details = MagicMock()
        postprocess = MagicMock(return_value="postprocessed")
        intercept_fn = MagicMock(return_value=(new_details, iter([]), postprocess))
        interceptor = _GenericClientInterceptor(intercept_fn)

        continuation = MagicMock(return_value="response")

        result = interceptor.intercept_stream_unary(continuation, MagicMock(), iter([]))

        assert result == "postprocessed"
        postprocess.assert_called_once_with("response")

    def test_intercept_stream_stream_without_postprocess(self):
        """Test intercept_stream_stream without postprocess function."""
        new_details = MagicMock()
        new_request_iterator = iter(["req1"])
        intercept_fn = MagicMock(return_value=(new_details, new_request_iterator, None))
        interceptor = _GenericClientInterceptor(intercept_fn)

        response_iterator = iter(["resp1", "resp2"])
        continuation = MagicMock(return_value=response_iterator)
        client_call_details = MagicMock()

        result = interceptor.intercept_stream_stream(
            continuation, client_call_details, iter(["original"])
        )

        assert result is response_iterator
        continuation.assert_called_once_with(new_details, new_request_iterator)
        # Verify request_streaming=True, response_streaming=True
        call_args = intercept_fn.call_args[0]
        assert call_args[2] is True  # request_streaming
        assert call_args[3] is True  # response_streaming

    def test_intercept_stream_stream_with_postprocess(self):
        """Test intercept_stream_stream with postprocess function."""
        new_details = MagicMock()
        postprocess = MagicMock(return_value="postprocessed")
        intercept_fn = MagicMock(return_value=(new_details, iter([]), postprocess))
        interceptor = _GenericClientInterceptor(intercept_fn)

        continuation = MagicMock(return_value=iter(["resp"]))

        result = interceptor.intercept_stream_stream(continuation, MagicMock(), iter([]))

        assert result == "postprocessed"
        postprocess.assert_called_once()
