"""Tests for modules/identity/encryption/key_manager.py — KeyManager."""

import pytest
from unittest.mock import patch

from dcid_server_sdk.modules.identity.encryption.key_manager import KeyManager
from dcid_server_sdk.types import GenerateEncryptionKeyOptions, GetEncryptedKeyOptions
from dcid_server_sdk.utils.http import HTTPClient
from dcid_server_sdk.utils.logger import NoOpLogger
from tests.conftest import make_mock_response


def _make_key_manager():
    http_client = HTTPClient("http://test", logger=NoOpLogger())
    return KeyManager(http_client)


# ---------------------------------------------------------------------------
# generate_key
# ---------------------------------------------------------------------------

class TestGenerateKey:
    @patch("dcid_server_sdk.utils.http.requests.request")
    def test_success(self, mock_request):
        mock_request.return_value = make_mock_response(
            json_data={
                "encryptedKey": "enc-key-123",
                "did": "did:test:123",
                "ownerEmail": "user@example.com",
                "message": "Key generated",
            },
            text="ok",
        )
        km = _make_key_manager()
        result = km.generate_key(
            GenerateEncryptionKeyOptions(did="did:test:123", owner_email="user@example.com")
        )
        assert result.encrypted_key == "enc-key-123"
        assert result.did == "did:test:123"
        assert result.owner_email == "user@example.com"

    def test_invalid_did_empty(self):
        km = _make_key_manager()
        with pytest.raises(ValueError, match="Valid DID is required"):
            km.generate_key(GenerateEncryptionKeyOptions(did="", owner_email="u@e.com"))

    def test_invalid_did_no_prefix(self):
        km = _make_key_manager()
        with pytest.raises(ValueError, match="Valid DID is required"):
            km.generate_key(GenerateEncryptionKeyOptions(did="invalid", owner_email="u@e.com"))

    def test_invalid_email(self):
        km = _make_key_manager()
        with pytest.raises(ValueError, match="Valid owner email"):
            km.generate_key(GenerateEncryptionKeyOptions(did="did:test:1", owner_email="bad"))

    def test_empty_email(self):
        km = _make_key_manager()
        with pytest.raises(ValueError, match="Valid owner email"):
            km.generate_key(GenerateEncryptionKeyOptions(did="did:test:1", owner_email=""))

    @patch("dcid_server_sdk.utils.http.requests.request")
    def test_calls_correct_endpoint(self, mock_request):
        mock_request.return_value = make_mock_response(
            json_data={"encryptedKey": "k", "did": "d", "ownerEmail": "e", "message": "m"},
            text="ok",
        )
        km = _make_key_manager()
        km.generate_key(GenerateEncryptionKeyOptions(did="did:test:1", owner_email="u@e.com"))
        call_args = mock_request.call_args
        assert "/identity/generate-encryption-key" in call_args[0][1]


# ---------------------------------------------------------------------------
# get_key
# ---------------------------------------------------------------------------

class TestGetKey:
    @patch("dcid_server_sdk.utils.http.requests.request")
    def test_success(self, mock_request):
        mock_request.return_value = make_mock_response(
            json_data={
                "encryptedKey": "key-abc",
                "did": "did:test:123",
                "message": "Key retrieved",
            },
            text="ok",
        )
        km = _make_key_manager()
        result = km.get_key(GetEncryptedKeyOptions(did="did:test:123"))
        assert result.encrypted_key == "key-abc"
        assert result.did == "did:test:123"

    def test_invalid_did(self):
        km = _make_key_manager()
        with pytest.raises(ValueError, match="Valid DID is required"):
            km.get_key(GetEncryptedKeyOptions(did="bad"))

    def test_empty_did(self):
        km = _make_key_manager()
        with pytest.raises(ValueError, match="Valid DID is required"):
            km.get_key(GetEncryptedKeyOptions(did=""))

    @patch("dcid_server_sdk.utils.http.requests.request")
    def test_calls_correct_endpoint(self, mock_request):
        mock_request.return_value = make_mock_response(
            json_data={"encryptedKey": "k", "did": "d", "message": "m"},
            text="ok",
        )
        km = _make_key_manager()
        km.get_key(GetEncryptedKeyOptions(did="did:test:1"))
        call_args = mock_request.call_args
        assert "/identity/get-encrypted-key" in call_args[0][1]
