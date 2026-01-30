"""Tests for modules/identity/issuer/issuer.py — Issuer."""

import pytest
from unittest.mock import patch

from dcid_server_sdk.modules.identity.issuer.issuer import Issuer
from dcid_server_sdk.types import IssueCredentialOptions, GetCredentialOfferOptions
from dcid_server_sdk.utils.http import HTTPClient
from dcid_server_sdk.utils.logger import NoOpLogger
from tests.conftest import make_mock_response


def _make_issuer():
    http_client = HTTPClient("http://test", logger=NoOpLogger())
    return Issuer(http_client)


# ---------------------------------------------------------------------------
# issue_credential
# ---------------------------------------------------------------------------

class TestIssueCredential:
    @patch("dcid_server_sdk.utils.http.requests.request")
    def test_success_sig(self, mock_request):
        mock_request.return_value = make_mock_response(
            json_data={
                "qrCodeLink": "https://example.com/qr",
                "schemaType": "KYCAgeCredential",
            },
            text="ok",
        )
        issuer = _make_issuer()
        result = issuer.issue_credential(
            IssueCredentialOptions(
                did="did:test:123",
                credential_name="KYCAgeCredential",
                values={"birthday": 25},
                owner_email="user@example.com",
            )
        )
        assert result["qr_code_link"] == "https://example.com/qr"
        assert result["schema_type"] == "KYCAgeCredential"

    @patch("dcid_server_sdk.utils.http.requests.request")
    def test_success_mtp(self, mock_request):
        mock_request.return_value = make_mock_response(
            json_data={"txId": "tx-1", "claimId": "claim-1"},
            text="ok",
        )
        issuer = _make_issuer()
        result = issuer.issue_credential(
            IssueCredentialOptions(
                did="did:test:123",
                credential_name="cred",
                values={"key": "val"},
                owner_email="user@example.com",
            )
        )
        assert result["tx_id"] == "tx-1"
        assert result["claim_id"] == "claim-1"

    def test_invalid_did(self):
        issuer = _make_issuer()
        with pytest.raises(ValueError, match="Valid DID is required"):
            issuer.issue_credential(
                IssueCredentialOptions(
                    did="bad", credential_name="c", values={"k": "v"}, owner_email="u@e.com"
                )
            )

    def test_missing_credential_name(self):
        issuer = _make_issuer()
        with pytest.raises(ValueError, match="Valid credential name"):
            issuer.issue_credential(
                IssueCredentialOptions(
                    did="did:test:1", credential_name="", values={"k": "v"}, owner_email="u@e.com"
                )
            )

    def test_invalid_values(self):
        issuer = _make_issuer()
        with pytest.raises(ValueError, match="Valid values"):
            issuer.issue_credential(
                IssueCredentialOptions(
                    did="did:test:1", credential_name="c", values={}, owner_email="u@e.com"
                )
            )

    def test_invalid_email(self):
        issuer = _make_issuer()
        with pytest.raises(ValueError, match="Valid owner email"):
            issuer.issue_credential(
                IssueCredentialOptions(
                    did="did:test:1", credential_name="c", values={"k": "v"}, owner_email="bad"
                )
            )

    @patch("dcid_server_sdk.utils.http.requests.request")
    def test_calls_correct_endpoint(self, mock_request):
        mock_request.return_value = make_mock_response(
            json_data={"qrCodeLink": "url", "schemaType": "t"},
            text="ok",
        )
        issuer = _make_issuer()
        issuer.issue_credential(
            IssueCredentialOptions(
                did="did:test:1", credential_name="c", values={"k": "v"}, owner_email="u@e.com"
            )
        )
        call_args = mock_request.call_args
        assert "/identity/issuer/issue-credential" in call_args[0][1]


# ---------------------------------------------------------------------------
# get_credential_offer
# ---------------------------------------------------------------------------

class TestGetCredentialOffer:
    @patch("dcid_server_sdk.utils.http.requests.request")
    def test_success(self, mock_request):
        mock_request.return_value = make_mock_response(
            json_data={
                "status": "published",
                "txId": "tx-1",
                "claimId": "claim-1",
                "offerAvailable": True,
                "qrCodeLink": "https://example.com/offer-qr",
            },
            text="ok",
        )
        issuer = _make_issuer()
        result = issuer.get_credential_offer(
            GetCredentialOfferOptions(claim_id="claim-1", tx_id="tx-1")
        )
        assert result.status == "published"
        assert result.offer_available is True
        assert result.qr_code_link == "https://example.com/offer-qr"

    def test_missing_claim_id(self):
        issuer = _make_issuer()
        with pytest.raises(ValueError, match="Valid claim ID"):
            issuer.get_credential_offer(
                GetCredentialOfferOptions(claim_id="", tx_id="tx-1")
            )

    def test_missing_tx_id(self):
        issuer = _make_issuer()
        with pytest.raises(ValueError, match="Valid transaction ID"):
            issuer.get_credential_offer(
                GetCredentialOfferOptions(claim_id="c-1", tx_id="")
            )

    @patch("dcid_server_sdk.utils.http.requests.request")
    def test_uses_get_method(self, mock_request):
        mock_request.return_value = make_mock_response(
            json_data={
                "status": "pending",
                "txId": "tx-1",
                "claimId": "c-1",
                "offerAvailable": False,
                "message": "pending",
            },
            text="ok",
        )
        issuer = _make_issuer()
        issuer.get_credential_offer(
            GetCredentialOfferOptions(claim_id="c-1", tx_id="tx-1")
        )
        call_args = mock_request.call_args
        assert call_args[0][0] == "GET"
