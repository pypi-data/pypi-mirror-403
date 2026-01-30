"""Tests for modules/identity/verification/verification.py — Verification."""

import pytest
from unittest.mock import patch

from dcid_server_sdk.modules.identity.verification.verification import Verification
from dcid_server_sdk.types import (
    VerifySignInOptions,
    GetLinkStoreOptions,
    PostLinkStoreOptions,
    VerifyCallbackOptions,
)
from dcid_server_sdk.utils.http import HTTPClient
from dcid_server_sdk.utils.logger import NoOpLogger
from tests.conftest import make_mock_response


def _make_verification():
    http_client = HTTPClient("http://test", logger=NoOpLogger())
    return Verification(http_client)


# ---------------------------------------------------------------------------
# verify_sign_in
# ---------------------------------------------------------------------------

class TestVerifySignIn:
    @patch("dcid_server_sdk.utils.http.requests.request")
    def test_success(self, mock_request):
        mock_request.return_value = make_mock_response(
            json_data={
                "proofRequestUrl": "https://example.com/proof",
                "iden3commUrl": "iden3comm://example",
                "sessionId": "session-1",
            },
            text="ok",
        )
        v = _make_verification()
        result = v.verify_sign_in(VerifySignInOptions(credential_name="ProofOfAgeCredential"))
        assert result.session_id == "session-1"
        assert result.proof_request_url == "https://example.com/proof"

    def test_missing_credential_name(self):
        v = _make_verification()
        with pytest.raises(ValueError, match="Valid credential name"):
            v.verify_sign_in(VerifySignInOptions(credential_name=""))

    @patch("dcid_server_sdk.utils.http.requests.request")
    def test_calls_correct_endpoint(self, mock_request):
        mock_request.return_value = make_mock_response(
            json_data={"proofRequestUrl": "u", "iden3commUrl": "u", "sessionId": "s"},
            text="ok",
        )
        v = _make_verification()
        v.verify_sign_in(VerifySignInOptions(credential_name="cred"))
        call_args = mock_request.call_args
        assert "/identity/verify/sign-in" in call_args[0][1]


# ---------------------------------------------------------------------------
# get_link_store
# ---------------------------------------------------------------------------

class TestGetLinkStore:
    @patch("dcid_server_sdk.utils.http.requests.request")
    def test_success(self, mock_request):
        mock_request.return_value = make_mock_response(
            json_data={
                "id": "session-1",
                "thid": "session-1",
                "type": "auth-request",
                "from": "did:verifier:123",
                "typ": "application/iden3comm-plain-json",
                "body": {"reason": "test", "message": "m", "callback_url": "u", "scope": []},
            },
            text="ok",
        )
        v = _make_verification()
        result = v.get_link_store(GetLinkStoreOptions(id="session-1"))
        assert result.id == "session-1"
        assert result.from_did == "did:verifier:123"

    def test_missing_id(self):
        v = _make_verification()
        with pytest.raises(ValueError, match="Valid id is required"):
            v.get_link_store(GetLinkStoreOptions(id=""))

    @patch("dcid_server_sdk.utils.http.requests.request")
    def test_uses_get_method(self, mock_request):
        mock_request.return_value = make_mock_response(
            json_data={
                "id": "s", "thid": "s", "type": "t", "from": "f", "typ": "t",
                "body": {"reason": "r", "message": "m", "callback_url": "u", "scope": []},
            },
            text="ok",
        )
        v = _make_verification()
        v.get_link_store(GetLinkStoreOptions(id="session-1"))
        call_args = mock_request.call_args
        assert call_args[0][0] == "GET"


# ---------------------------------------------------------------------------
# post_link_store
# ---------------------------------------------------------------------------

class TestPostLinkStore:
    @patch("dcid_server_sdk.utils.http.requests.request")
    def test_success(self, mock_request):
        mock_request.return_value = make_mock_response(
            json_data={
                "proofRequestUrl": "https://example.com/proof",
                "iden3commUrl": "iden3comm://example",
            },
            text="ok",
        )
        v = _make_verification()
        result = v.post_link_store(
            PostLinkStoreOptions(
                id="session-1",
                thid="session-1",
                type="auth-request",
                from_did="did:verifier:123",
                typ="application/iden3comm-plain-json",
                body={
                    "reason": "test",
                    "message": "verify",
                    "callback_url": "https://example.com/callback",
                    "scope": [],
                },
            )
        )
        assert result.proof_request_url == "https://example.com/proof"

    def test_missing_id(self):
        v = _make_verification()
        with pytest.raises(ValueError, match="Valid id is required"):
            v.post_link_store(
                PostLinkStoreOptions(
                    id="", thid="t", type="t", from_did="f", typ="t",
                    body={"reason": "r", "message": "m", "callback_url": "u", "scope": []},
                )
            )

    def test_missing_body(self):
        v = _make_verification()
        with pytest.raises(ValueError, match="Valid body"):
            v.post_link_store(
                PostLinkStoreOptions(
                    id="s", thid="t", type="t", from_did="f", typ="t",
                    body=None,
                )
            )

    def test_missing_callback_url(self):
        v = _make_verification()
        with pytest.raises(ValueError, match="callbackUrl"):
            v.post_link_store(
                PostLinkStoreOptions(
                    id="s", thid="t", type="t", from_did="f", typ="t",
                    body={"reason": "r", "message": "m", "callback_url": "", "scope": []},
                )
            )

    def test_missing_scope(self):
        v = _make_verification()
        with pytest.raises(ValueError, match="scope"):
            v.post_link_store(
                PostLinkStoreOptions(
                    id="s", thid="t", type="t", from_did="f", typ="t",
                    body={"reason": "r", "message": "m", "callback_url": "u"},
                )
            )


# ---------------------------------------------------------------------------
# verify_callback
# ---------------------------------------------------------------------------

class TestVerifyCallback:
    @patch("dcid_server_sdk.utils.http.requests.request")
    def test_success(self, mock_request):
        mock_request.return_value = make_mock_response(
            json_data={
                "id": "resp-1",
                "typ": "application/iden3comm-plain-json",
                "type": "auth-response",
                "thid": "session-1",
                "body": {"message": "verified", "scope": []},
                "from": "did:user:123",
                "to": "did:verifier:456",
            },
            text="ok",
        )
        v = _make_verification()
        result = v.verify_callback(
            VerifyCallbackOptions(session_id="session-1", token="jwz-token")
        )
        assert result.id == "resp-1"
        assert result.from_did == "did:user:123"
        assert result.to == "did:verifier:456"

    def test_missing_session_id(self):
        v = _make_verification()
        with pytest.raises(ValueError, match="Valid session ID"):
            v.verify_callback(VerifyCallbackOptions(session_id="", token="tok"))

    def test_missing_token(self):
        v = _make_verification()
        with pytest.raises(ValueError, match="Valid token"):
            v.verify_callback(VerifyCallbackOptions(session_id="s-1", token=""))

    @patch("dcid_server_sdk.utils.http.requests.request")
    def test_sends_token_in_body(self, mock_request):
        mock_request.return_value = make_mock_response(
            json_data={
                "id": "r", "typ": "t", "type": "t", "thid": "t",
                "body": {"message": "m", "scope": []}, "from": "f", "to": "t",
            },
            text="ok",
        )
        v = _make_verification()
        v.verify_callback(VerifyCallbackOptions(session_id="s-1", token="jwz-data"))
        call_kwargs = mock_request.call_args
        json_body = call_kwargs.kwargs.get("json") or call_kwargs[1].get("json", {})
        assert json_body["token"] == "jwz-data"
