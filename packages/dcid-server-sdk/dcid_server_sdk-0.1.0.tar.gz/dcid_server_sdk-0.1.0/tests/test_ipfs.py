"""Tests for modules/identity/ipfs/ipfs.py — IPFS."""

import pytest
from unittest.mock import patch

from dcid_server_sdk.modules.identity.ipfs.ipfs import IPFS
from dcid_server_sdk.types import (
    StoreCredentialOptions,
    RetrieveUserCredentialOptions,
    GetAllUserCredentialsOptions,
)
from dcid_server_sdk.utils.http import HTTPClient
from dcid_server_sdk.utils.logger import NoOpLogger
from tests.conftest import make_mock_response


def _make_ipfs():
    http_client = HTTPClient("http://test", logger=NoOpLogger())
    return IPFS(http_client)


# ---------------------------------------------------------------------------
# store_credential
# ---------------------------------------------------------------------------

class TestStoreCredential:
    @patch("dcid_server_sdk.utils.http.requests.request")
    def test_success_encrypted(self, mock_request):
        mock_request.return_value = make_mock_response(
            json_data={
                "cid": "QmTest123",
                "did": "did:test:123",
                "credentialType": "KYCAgeCredential",
                "message": "stored",
                "encrypted": True,
            },
            text="ok",
        )
        ipfs = _make_ipfs()
        result = ipfs.store_credential(
            StoreCredentialOptions(
                did="did:test:123",
                credential_type="KYCAgeCredential",
                credential="encrypted-data",
                encrypted=True,
            )
        )
        assert result.cid == "QmTest123"
        assert result.encrypted is True

    @patch("dcid_server_sdk.utils.http.requests.request")
    def test_success_unencrypted(self, mock_request):
        mock_request.return_value = make_mock_response(
            json_data={
                "cid": "QmTest456",
                "did": "did:test:123",
                "credentialType": "cred",
                "message": "stored",
                "encrypted": False,
            },
            text="ok",
        )
        ipfs = _make_ipfs()
        result = ipfs.store_credential(
            StoreCredentialOptions(
                did="did:test:123",
                credential_type="cred",
                credential={"key": "value"},
                encrypted=False,
            )
        )
        assert result.cid == "QmTest456"
        assert result.encrypted is False

    def test_missing_did(self):
        ipfs = _make_ipfs()
        with pytest.raises(ValueError, match="Valid DID is required"):
            ipfs.store_credential(
                StoreCredentialOptions(did="", credential_type="c", credential="data")
            )

    def test_missing_credential_type(self):
        ipfs = _make_ipfs()
        with pytest.raises(ValueError, match="Valid credential type"):
            ipfs.store_credential(
                StoreCredentialOptions(did="did:test:1", credential_type="", credential="data")
            )

    def test_missing_credential(self):
        ipfs = _make_ipfs()
        with pytest.raises(ValueError, match="Credential data is required"):
            ipfs.store_credential(
                StoreCredentialOptions(did="did:test:1", credential_type="c", credential="")
            )

    def test_encrypted_must_be_string(self):
        ipfs = _make_ipfs()
        with pytest.raises(ValueError, match="Encrypted credentials must be provided as string"):
            ipfs.store_credential(
                StoreCredentialOptions(
                    did="did:test:1",
                    credential_type="c",
                    credential={"key": "val"},
                    encrypted=True,
                )
            )

    def test_unencrypted_must_be_dict(self):
        ipfs = _make_ipfs()
        with pytest.raises(ValueError, match="Unencrypted credentials must be provided as object"):
            ipfs.store_credential(
                StoreCredentialOptions(
                    did="did:test:1",
                    credential_type="c",
                    credential="string-data",
                    encrypted=False,
                )
            )


# ---------------------------------------------------------------------------
# retrieve_user_credential
# ---------------------------------------------------------------------------

class TestRetrieveUserCredential:
    @patch("dcid_server_sdk.utils.http.requests.request")
    def test_success(self, mock_request):
        mock_request.return_value = make_mock_response(
            json_data={
                "cid": "QmRetrieve",
                "did": "did:test:123",
                "credentialType": "KYCAgeCredential",
                "message": "retrieved",
                "credential": "data",
                "encrypted": True,
            },
            text="ok",
        )
        ipfs = _make_ipfs()
        result = ipfs.retrieve_user_credential(
            RetrieveUserCredentialOptions(did="did:test:123", credential_type="KYCAgeCredential")
        )
        assert result.cid == "QmRetrieve"
        assert result.credential == "data"

    def test_missing_did(self):
        ipfs = _make_ipfs()
        with pytest.raises(ValueError, match="Valid DID"):
            ipfs.retrieve_user_credential(
                RetrieveUserCredentialOptions(did="", credential_type="c")
            )

    def test_missing_credential_type(self):
        ipfs = _make_ipfs()
        with pytest.raises(ValueError, match="Valid credential type"):
            ipfs.retrieve_user_credential(
                RetrieveUserCredentialOptions(did="did:test:1", credential_type="")
            )

    @patch("dcid_server_sdk.utils.http.requests.request")
    def test_cid_only(self, mock_request):
        mock_request.return_value = make_mock_response(
            json_data={
                "cid": "QmCid",
                "did": "did:test:1",
                "credentialType": "c",
                "message": "ok",
            },
            text="ok",
        )
        ipfs = _make_ipfs()
        result = ipfs.retrieve_user_credential(
            RetrieveUserCredentialOptions(
                did="did:test:1", credential_type="c", include_cid_only=True
            )
        )
        assert result.cid == "QmCid"


# ---------------------------------------------------------------------------
# get_all_user_credentials
# ---------------------------------------------------------------------------

class TestGetAllUserCredentials:
    @patch("dcid_server_sdk.utils.http.requests.request")
    def test_success(self, mock_request):
        mock_request.return_value = make_mock_response(
            json_data={
                "credentials": {"KYCAgeCredential": "QmCid1", "ProofOfAge": "QmCid2"},
                "did": "did:test:123",
                "count": 2,
                "message": "found",
            },
            text="ok",
        )
        ipfs = _make_ipfs()
        result = ipfs.get_all_user_credentials(
            GetAllUserCredentialsOptions(did="did:test:123")
        )
        assert result.count == 2
        assert len(result.credentials) == 2

    def test_missing_did(self):
        ipfs = _make_ipfs()
        with pytest.raises(ValueError, match="Valid DID"):
            ipfs.get_all_user_credentials(GetAllUserCredentialsOptions(did=""))

    @patch("dcid_server_sdk.utils.http.requests.request")
    def test_with_credential_data(self, mock_request):
        mock_request.return_value = make_mock_response(
            json_data={
                "credentials": {"cred": {"data": "value"}},
                "did": "did:test:1",
                "count": 1,
                "message": "ok",
            },
            text="ok",
        )
        ipfs = _make_ipfs()
        result = ipfs.get_all_user_credentials(
            GetAllUserCredentialsOptions(did="did:test:1", include_credential_data=True)
        )
        assert result.count == 1
