"""Tests for modules/auth/otp.py — AuthOTP."""

import pytest
from unittest.mock import patch, MagicMock

from dcid_server_sdk.modules.auth.otp import AuthOTP
from dcid_server_sdk.types import (
    InitiateOTPOptions,
    ConfirmOTPOptions,
    RefreshTokenOptions,
    TokenResponse,
)
from dcid_server_sdk.utils.http import HTTPClient
from dcid_server_sdk.utils.logger import NoOpLogger
from tests.conftest import make_mock_response


def _make_auth_client():
    http_client = HTTPClient("http://test", logger=NoOpLogger())
    tokens_received = []
    auth = AuthOTP(http_client, on_tokens_received=lambda t: tokens_received.append(t))
    return auth, tokens_received


# ---------------------------------------------------------------------------
# register_otp
# ---------------------------------------------------------------------------

class TestRegisterOTP:
    @patch("dcid_server_sdk.utils.http.requests.request")
    def test_success_email(self, mock_request):
        mock_request.return_value = make_mock_response(
            json_data={"otp": "123456"}, text="ok"
        )
        auth, _ = _make_auth_client()
        result = auth.register_otp(InitiateOTPOptions(email="user@example.com"))
        assert result.otp == "123456"

    @patch("dcid_server_sdk.utils.http.requests.request")
    def test_success_phone(self, mock_request):
        mock_request.return_value = make_mock_response(
            json_data={"otp": "654321"}, text="ok"
        )
        auth, _ = _make_auth_client()
        result = auth.register_otp(InitiateOTPOptions(phone="+1234567890"))
        assert result.otp == "654321"

    def test_missing_email_and_phone(self):
        auth, _ = _make_auth_client()
        with pytest.raises(ValueError, match="Either email or phone"):
            auth.register_otp(InitiateOTPOptions())

    @patch("dcid_server_sdk.utils.http.requests.request")
    def test_calls_correct_endpoint(self, mock_request):
        mock_request.return_value = make_mock_response(json_data={}, text="{}")
        auth, _ = _make_auth_client()
        auth.register_otp(InitiateOTPOptions(email="user@example.com"))
        call_args = mock_request.call_args
        assert "/auth/sign-in/initiate" in call_args[0][1]
        assert call_args[0][0] == "POST"


# ---------------------------------------------------------------------------
# confirm_otp
# ---------------------------------------------------------------------------

class TestConfirmOTP:
    @patch("dcid_server_sdk.utils.http.requests.request")
    def test_success(self, mock_request):
        mock_request.return_value = make_mock_response(
            json_data={
                "access_token": "at-123",
                "refresh_token": "rt-456",
                "expires_in": 3600,
            },
            text="ok",
        )
        auth, tokens_received = _make_auth_client()
        result = auth.confirm_otp(
            ConfirmOTPOptions(email="user@example.com", otp="123456")
        )
        assert result.access_token == "at-123"
        assert result.refresh_token == "rt-456"
        # Verify tokens callback was called
        assert len(tokens_received) == 1
        assert tokens_received[0].access_token == "at-123"

    def test_missing_email_and_phone(self):
        auth, _ = _make_auth_client()
        with pytest.raises(ValueError, match="Either email or phone"):
            auth.confirm_otp(ConfirmOTPOptions(otp="123456"))

    def test_missing_otp(self):
        auth, _ = _make_auth_client()
        with pytest.raises(ValueError, match="OTP code is required"):
            auth.confirm_otp(ConfirmOTPOptions(email="user@example.com", otp=""))

    @patch("dcid_server_sdk.utils.http.requests.request")
    def test_calls_correct_endpoint(self, mock_request):
        mock_request.return_value = make_mock_response(
            json_data={"access_token": "x", "refresh_token": "y"}, text="ok"
        )
        auth, _ = _make_auth_client()
        auth.confirm_otp(ConfirmOTPOptions(email="user@example.com", otp="123"))
        call_args = mock_request.call_args
        assert "/auth/sign-in/confirm" in call_args[0][1]

    @patch("dcid_server_sdk.utils.http.requests.request")
    def test_no_callback_still_works(self, mock_request):
        mock_request.return_value = make_mock_response(
            json_data={"access_token": "x", "refresh_token": "y"}, text="ok"
        )
        auth = AuthOTP(HTTPClient("http://test", logger=NoOpLogger()))
        result = auth.confirm_otp(ConfirmOTPOptions(email="u@e.com", otp="123"))
        assert result.access_token == "x"


# ---------------------------------------------------------------------------
# admin_login
# ---------------------------------------------------------------------------

class TestAdminLogin:
    @patch("dcid_server_sdk.utils.http.requests.request")
    def test_success(self, mock_request):
        mock_request.return_value = make_mock_response(
            json_data={"otp": "admin-otp"}, text="ok"
        )
        auth, _ = _make_auth_client()
        result = auth.admin_login(InitiateOTPOptions(email="admin@example.com"))
        assert result.otp == "admin-otp"

    @patch("dcid_server_sdk.utils.http.requests.request")
    def test_calls_admin_endpoint(self, mock_request):
        mock_request.return_value = make_mock_response(json_data={}, text="{}")
        auth, _ = _make_auth_client()
        auth.admin_login(InitiateOTPOptions(email="admin@example.com"))
        call_args = mock_request.call_args
        assert "type=admin" in call_args[0][1]

    def test_missing_email_and_phone(self):
        auth, _ = _make_auth_client()
        with pytest.raises(ValueError, match="Either email or phone"):
            auth.admin_login(InitiateOTPOptions())


# ---------------------------------------------------------------------------
# refresh_token
# ---------------------------------------------------------------------------

class TestRefreshToken:
    @patch("dcid_server_sdk.utils.http.requests.request")
    def test_success(self, mock_request):
        mock_request.return_value = make_mock_response(
            json_data={"access_token": "new-at", "refresh_token": "new-rt"},
            text="ok",
        )
        auth, _ = _make_auth_client()
        result = auth.refresh_token(RefreshTokenOptions(refresh_token="old-rt"))
        assert result.access_token == "new-at"
        assert result.refresh_token == "new-rt"

    def test_missing_refresh_token(self):
        auth, _ = _make_auth_client()
        with pytest.raises(ValueError, match="Refresh token is required"):
            auth.refresh_token(RefreshTokenOptions(refresh_token=""))

    @patch("dcid_server_sdk.utils.http.requests.request")
    def test_calls_correct_endpoint(self, mock_request):
        mock_request.return_value = make_mock_response(
            json_data={"access_token": "x", "refresh_token": "y"}, text="ok"
        )
        auth, _ = _make_auth_client()
        auth.refresh_token(RefreshTokenOptions(refresh_token="old-rt"))
        call_args = mock_request.call_args
        assert "/auth/refresh-token" in call_args[0][1]
