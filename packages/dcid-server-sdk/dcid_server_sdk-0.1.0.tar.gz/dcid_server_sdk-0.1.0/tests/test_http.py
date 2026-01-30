"""Tests for utils/http.py — HTTPClient, error helpers."""

import pytest
from unittest.mock import patch, MagicMock
import requests

from dcid_server_sdk.utils.http import (
    HTTPClient,
    create_http_client,
    sanitize_headers,
    is_krakend_error,
    is_api_key_error,
    is_backend_connectivity_error,
    create_error_context,
)
from dcid_server_sdk.types import (
    DCIDServerSDKError,
    NetworkError,
    AuthenticationError,
    ServerError,
    TokenResponse,
)
from dcid_server_sdk.utils.logger import NoOpLogger
from tests.conftest import make_mock_response


# ---------------------------------------------------------------------------
# sanitize_headers
# ---------------------------------------------------------------------------

class TestSanitizeHeaders:
    def test_redacts_authorization(self):
        result = sanitize_headers({"Authorization": "Bearer secret"})
        assert result["Authorization"] == "[REDACTED]"

    def test_redacts_api_key(self):
        result = sanitize_headers({"X-API-Key": "my-key"})
        assert result["X-API-Key"] == "[REDACTED]"

    def test_redacts_cookie(self):
        result = sanitize_headers({"Cookie": "session=abc"})
        assert result["Cookie"] == "[REDACTED]"

    def test_preserves_non_sensitive(self):
        result = sanitize_headers({"Content-Type": "application/json"})
        assert result["Content-Type"] == "application/json"

    def test_case_insensitive(self):
        result = sanitize_headers({"authorization": "Bearer x", "x-api-key": "y"})
        assert result["authorization"] == "[REDACTED]"
        assert result["x-api-key"] == "[REDACTED]"


# ---------------------------------------------------------------------------
# is_krakend_error
# ---------------------------------------------------------------------------

class TestIsKrakendError:
    def test_none_response(self):
        assert is_krakend_error(None) is False

    def test_krakend_header(self):
        resp = make_mock_response(headers={"x-krakend": "true"})
        assert is_krakend_error(resp) is True

    def test_api_key_in_error_message(self):
        resp = make_mock_response(
            json_data={"error": "Invalid API Key"},
            text="error",
        )
        assert is_krakend_error(resp) is True

    def test_no_krakend_indicators(self):
        resp = make_mock_response(json_data={"message": "ok"}, text="ok")
        assert is_krakend_error(resp) is False


# ---------------------------------------------------------------------------
# is_api_key_error
# ---------------------------------------------------------------------------

class TestIsApiKeyError:
    def test_none_response(self):
        assert is_api_key_error(None) is False

    def test_non_401_returns_false(self):
        resp = make_mock_response(status_code=400)
        assert is_api_key_error(resp) is False

    def test_jwt_error_returns_false(self):
        resp = make_mock_response(
            status_code=401,
            json_data={"error": "token expired"},
            text="token expired",
        )
        assert is_api_key_error(resp) is False

    def test_api_key_message_returns_true(self):
        resp = make_mock_response(
            status_code=401,
            json_data={"error": "Invalid API Key"},
            text="error",
            headers={"x-krakend": "true"},
        )
        assert is_api_key_error(resp) is True


# ---------------------------------------------------------------------------
# is_backend_connectivity_error
# ---------------------------------------------------------------------------

class TestIsBackendConnectivityError:
    def test_none_response(self):
        assert is_backend_connectivity_error(None) is False

    def test_non_krakend_returns_false(self):
        resp = make_mock_response(status_code=500, json_data={"error": "backend unreachable"}, text="err")
        assert is_backend_connectivity_error(resp) is False

    def test_non_5xx_returns_false(self):
        resp = make_mock_response(
            status_code=400,
            headers={"x-krakend": "true"},
            json_data={"error": "backend unreachable"},
            text="err",
        )
        assert is_backend_connectivity_error(resp) is False

    def test_krakend_502_backend_message(self):
        resp = make_mock_response(
            status_code=502,
            headers={"x-krakend": "true"},
            json_data={"error": "backend connection refused"},
            text="err",
        )
        assert is_backend_connectivity_error(resp) is True

    def test_krakend_500_timeout_message(self):
        resp = make_mock_response(
            status_code=500,
            headers={"x-krakend": "true"},
            json_data={"message": "timeout waiting for backend"},
            text="err",
        )
        assert is_backend_connectivity_error(resp) is True


# ---------------------------------------------------------------------------
# create_error_context
# ---------------------------------------------------------------------------

class TestCreateErrorContext:
    def test_with_response(self):
        resp = make_mock_response(status_code=500)
        ctx = create_error_context(response=resp, url="http://test/api", method="POST")
        assert ctx.status_code == 500
        assert ctx.timestamp is not None

    def test_without_response(self):
        ctx = create_error_context(url="http://test/api", method="GET")
        assert ctx.status_code is None
        assert ctx.url == "http://test/api"
        assert ctx.method == "GET"
        assert ctx.error_source == "network"


# ---------------------------------------------------------------------------
# HTTPClient
# ---------------------------------------------------------------------------

class TestHTTPClient:
    @patch("dcid_server_sdk.utils.http.requests.request")
    def test_post_success(self, mock_request):
        mock_request.return_value = make_mock_response(
            json_data={"status": "ok"}, text="ok"
        )
        client = HTTPClient("http://test", logger=NoOpLogger())
        result = client.post("/test", json={"key": "val"})
        assert result == {"status": "ok"}
        mock_request.assert_called_once()

    @patch("dcid_server_sdk.utils.http.requests.request")
    def test_get_success(self, mock_request):
        mock_request.return_value = make_mock_response(
            json_data={"data": "value"}, text="ok"
        )
        client = HTTPClient("http://test", logger=NoOpLogger())
        result = client.get("/resource")
        assert result == {"data": "value"}

    @patch("dcid_server_sdk.utils.http.requests.request")
    def test_sets_required_headers(self, mock_request):
        mock_request.return_value = make_mock_response(json_data={}, text="{}")
        client = HTTPClient(
            "http://test",
            default_headers={"X-API-Key": "my-key"},
            logger=NoOpLogger(),
        )
        client.get("/test")
        call_kwargs = mock_request.call_args
        headers = call_kwargs.kwargs.get("headers") or call_kwargs[1].get("headers", {})
        assert headers["Content-Type"] == "application/json"
        assert headers["Accept"] == "application/json"
        assert headers["X-API-Key"] == "my-key"

    @patch("dcid_server_sdk.utils.http.requests.request")
    def test_bearer_token_injection(self, mock_request):
        mock_request.return_value = make_mock_response(json_data={}, text="{}")
        client = HTTPClient(
            "http://test",
            get_auth_token=lambda: "my-token",
            logger=NoOpLogger(),
        )
        client.get("/auth")
        call_kwargs = mock_request.call_args
        headers = call_kwargs.kwargs.get("headers") or call_kwargs[1].get("headers", {})
        assert headers["Authorization"] == "Bearer my-token"

    @patch("dcid_server_sdk.utils.http.requests.request")
    def test_no_bearer_when_no_token(self, mock_request):
        mock_request.return_value = make_mock_response(json_data={}, text="{}")
        client = HTTPClient("http://test", logger=NoOpLogger())
        client.get("/test")
        call_kwargs = mock_request.call_args
        headers = call_kwargs.kwargs.get("headers") or call_kwargs[1].get("headers", {})
        assert "Authorization" not in headers

    @patch("dcid_server_sdk.utils.http.requests.request")
    def test_no_bearer_when_token_is_none(self, mock_request):
        mock_request.return_value = make_mock_response(json_data={}, text="{}")
        client = HTTPClient(
            "http://test",
            get_auth_token=lambda: None,
            logger=NoOpLogger(),
        )
        client.get("/test")
        call_kwargs = mock_request.call_args
        headers = call_kwargs.kwargs.get("headers") or call_kwargs[1].get("headers", {})
        assert "Authorization" not in headers

    @patch("dcid_server_sdk.utils.http.requests.request")
    def test_400_raises_sdk_error(self, mock_request):
        mock_request.return_value = make_mock_response(
            status_code=400,
            json_data={"message": "bad request"},
            text="bad request",
        )
        client = HTTPClient("http://test", logger=NoOpLogger())
        with pytest.raises(DCIDServerSDKError) as exc_info:
            client.get("/bad")
        assert exc_info.value.status_code == 400

    @patch("dcid_server_sdk.utils.http.requests.request")
    def test_401_raises_authentication_error(self, mock_request):
        mock_request.return_value = make_mock_response(
            status_code=401,
            json_data={"message": "token expired"},
            text="token expired",
        )
        client = HTTPClient("http://test", logger=NoOpLogger())
        with pytest.raises(AuthenticationError):
            client.get("/protected")

    @patch("dcid_server_sdk.utils.http.requests.request")
    def test_500_raises_server_error(self, mock_request):
        mock_request.return_value = make_mock_response(
            status_code=500,
            json_data={"message": "internal error"},
            text="internal error",
        )
        client = HTTPClient("http://test", logger=NoOpLogger())
        with pytest.raises(ServerError):
            client.get("/error")

    @patch("dcid_server_sdk.utils.http.requests.request")
    def test_timeout_raises_network_error(self, mock_request):
        mock_request.side_effect = requests.exceptions.Timeout("timed out")
        client = HTTPClient("http://test", logger=NoOpLogger())
        with pytest.raises(NetworkError) as exc_info:
            client.get("/slow")
        assert exc_info.value.code == "ETIMEDOUT"

    @patch("dcid_server_sdk.utils.http.requests.request")
    def test_connection_error_raises_network_error(self, mock_request):
        mock_request.side_effect = requests.exceptions.ConnectionError("refused")
        client = HTTPClient("http://test", logger=NoOpLogger())
        with pytest.raises(NetworkError) as exc_info:
            client.get("/down")
        assert exc_info.value.code == "ECONNREFUSED"

    @patch("dcid_server_sdk.utils.http.requests.request")
    def test_request_exception_raises_network_error(self, mock_request):
        mock_request.side_effect = requests.exceptions.RequestException("generic")
        client = HTTPClient("http://test", logger=NoOpLogger())
        with pytest.raises(NetworkError):
            client.get("/fail")

    @patch("dcid_server_sdk.utils.http.requests.request")
    def test_401_auto_refresh_and_retry(self, mock_request):
        # First call returns 401, second (after refresh) returns 200
        resp_401 = make_mock_response(
            status_code=401,
            json_data={"message": "token expired"},
            text="token expired",
        )
        resp_200 = make_mock_response(
            json_data={"data": "refreshed"},
            text="ok",
        )
        mock_request.side_effect = [resp_401, resp_200]

        refreshed_tokens = TokenResponse(
            access_token="new-access",
            refresh_token="new-refresh",
        )

        client = HTTPClient(
            "http://test",
            get_auth_token=lambda: "old-token",
            get_refresh_token=lambda: "old-refresh",
            refresh_token_callback=lambda rt: refreshed_tokens,
            on_token_refreshed=lambda t: None,
            logger=NoOpLogger(),
        )
        result = client.get("/protected")
        assert result == {"data": "refreshed"}
        assert mock_request.call_count == 2

    @patch("dcid_server_sdk.utils.http.requests.request")
    def test_401_no_refresh_callback_raises(self, mock_request):
        mock_request.return_value = make_mock_response(
            status_code=401,
            json_data={"message": "unauthorized"},
            text="unauthorized",
        )
        client = HTTPClient("http://test", logger=NoOpLogger())
        with pytest.raises(AuthenticationError):
            client.get("/protected")

    @patch("dcid_server_sdk.utils.http.requests.request")
    def test_put_success(self, mock_request):
        mock_request.return_value = make_mock_response(
            json_data={"updated": True}, text="ok"
        )
        client = HTTPClient("http://test", logger=NoOpLogger())
        result = client.put("/resource", json={"key": "val"})
        assert result == {"updated": True}

    @patch("dcid_server_sdk.utils.http.requests.request")
    def test_delete_success(self, mock_request):
        mock_request.return_value = make_mock_response(
            json_data={"deleted": True}, text="ok"
        )
        client = HTTPClient("http://test", logger=NoOpLogger())
        result = client.delete("/resource")
        assert result == {"deleted": True}

    @patch("dcid_server_sdk.utils.http.requests.request")
    def test_error_message_from_error_field(self, mock_request):
        mock_request.return_value = make_mock_response(
            status_code=422,
            json_data={"error": "validation failed"},
            text="err",
        )
        client = HTTPClient("http://test", logger=NoOpLogger())
        with pytest.raises(DCIDServerSDKError) as exc_info:
            client.get("/validate")
        assert "validation failed" in str(exc_info.value)

    @patch("dcid_server_sdk.utils.http.requests.request")
    def test_error_default_message(self, mock_request):
        resp = make_mock_response(status_code=503, text="not json")
        resp.json.side_effect = ValueError("not json")
        mock_request.return_value = resp
        client = HTTPClient("http://test", logger=NoOpLogger())
        with pytest.raises(ServerError):
            client.get("/unavailable")

    @patch("dcid_server_sdk.utils.http.requests.request")
    def test_request_logging_enabled(self, mock_request):
        mock_request.return_value = make_mock_response(json_data={}, text="{}")
        logger = NoOpLogger()
        client = HTTPClient(
            "http://test", logger=logger, enable_request_logging=True
        )
        client.get("/logged")


# ---------------------------------------------------------------------------
# create_http_client factory
# ---------------------------------------------------------------------------

class TestCreateHttpClient:
    def test_returns_http_client(self):
        client = create_http_client("http://test")
        assert isinstance(client, HTTPClient)

    def test_strips_trailing_slash(self):
        client = create_http_client("http://test/api/")
        assert client.base_url == "http://test/api"

    def test_timeout_conversion(self):
        client = create_http_client("http://test", timeout=5000)
        assert client.timeout == 5.0  # ms to seconds
