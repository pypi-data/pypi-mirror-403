"""Tests for error types in types.py"""

import pytest
from dcid_server_sdk.types import (
    DCIDServerSDKError,
    NetworkError,
    AuthenticationError,
    ServerError,
    ErrorContext,
)


class TestDCIDServerSDKError:
    def test_message(self):
        err = DCIDServerSDKError("bad request", 400)
        assert str(err) == "bad request"
        assert err.message == "bad request"
        assert err.status_code == 400

    def test_without_status_code(self):
        err = DCIDServerSDKError("something failed")
        assert str(err) == "something failed"
        assert err.status_code is None

    def test_with_response(self):
        err = DCIDServerSDKError("err", 422, {"detail": "invalid"})
        assert err.response == {"detail": "invalid"}

    def test_with_context(self):
        ctx = ErrorContext(timestamp="2024-01-01T00:00:00")
        err = DCIDServerSDKError("err", context=ctx)
        assert err.context is ctx

    def test_is_exception(self):
        err = DCIDServerSDKError("err")
        assert isinstance(err, Exception)


class TestNetworkError:
    def test_message_and_code(self):
        err = NetworkError("connection refused", code="ECONNREFUSED")
        assert str(err) == "connection refused"
        assert err.code == "ECONNREFUSED"

    def test_without_code(self):
        err = NetworkError("timeout")
        assert err.code is None

    def test_inherits_sdk_error(self):
        err = NetworkError("err")
        assert isinstance(err, DCIDServerSDKError)
        assert isinstance(err, Exception)

    def test_with_context(self):
        ctx = ErrorContext(timestamp="2024-01-01T00:00:00", error_source="network")
        err = NetworkError("err", context=ctx)
        assert err.context.error_source == "network"


class TestAuthenticationError:
    def test_api_key_error(self):
        err = AuthenticationError("bad api key", is_api_key_error=True, status_code=401)
        assert err.is_api_key_error is True
        assert err.status_code == 401

    def test_jwt_token_error(self):
        err = AuthenticationError("token expired", is_api_key_error=False, status_code=401)
        assert err.is_api_key_error is False

    def test_inherits_sdk_error(self):
        err = AuthenticationError("err", is_api_key_error=False)
        assert isinstance(err, DCIDServerSDKError)

    def test_with_response(self):
        err = AuthenticationError(
            "unauthorized", is_api_key_error=False, status_code=401,
            response={"error": "unauthorized"}
        )
        assert err.response == {"error": "unauthorized"}


class TestServerError:
    def test_backend_connectivity(self):
        err = ServerError("backend down", is_backend_connectivity_error=True, status_code=502)
        assert err.is_backend_connectivity_error is True
        assert err.status_code == 502

    def test_gateway_error(self):
        err = ServerError("gateway error", is_backend_connectivity_error=False, status_code=500)
        assert err.is_backend_connectivity_error is False

    def test_inherits_sdk_error(self):
        err = ServerError("err", is_backend_connectivity_error=False)
        assert isinstance(err, DCIDServerSDKError)


class TestErrorContext:
    def test_all_fields(self):
        ctx = ErrorContext(
            timestamp="2024-01-01T00:00:00",
            url="http://example.com",
            method="POST",
            status_code=500,
            status_text="Internal Server Error",
            is_krakend_error=True,
            error_source="krakend",
        )
        assert ctx.url == "http://example.com"
        assert ctx.method == "POST"
        assert ctx.status_code == 500
        assert ctx.is_krakend_error is True
        assert ctx.error_source == "krakend"

    def test_defaults(self):
        ctx = ErrorContext(timestamp="2024-01-01T00:00:00")
        assert ctx.url is None
        assert ctx.method is None
        assert ctx.status_code is None
        assert ctx.is_krakend_error is False
        assert ctx.error_source is None
