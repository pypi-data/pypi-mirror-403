"""Issuer for credential operations"""

from typing import Union
from ....types import (
    IssueCredentialOptions,
    IssueCredentialResponse,
    GetCredentialOfferOptions,
    GetCredentialOfferResponse,
)
from ....utils.http import HTTPClient


class Issuer:
    """Issuer module for credential issuance operations"""

    def __init__(self, http_client: HTTPClient):
        self.http_client = http_client

    def issue_credential(
        self, options: IssueCredentialOptions
    ) -> IssueCredentialResponse:
        """
        Issue a credential (SIG or MTP)

        This method covers the endpoint: POST /identity/issuer/issue-credential

        Args:
            options: DID, credential name, values, and owner email

        Returns:
            IssueCredentialResponse (either QR code link for SIG or txId/claimId for MTP)

        Raises:
            ValueError: If any required field is invalid
        """
        if not options.did or not options.did.startswith("did:"):
            raise ValueError('Valid DID is required (must start with "did:")')

        if not options.credential_name or not isinstance(
            options.credential_name, str
        ):
            raise ValueError("Valid credential name is required")

        if not options.values or not isinstance(options.values, dict):
            raise ValueError("Valid values object is required")

        if not options.owner_email or "@" not in options.owner_email:
            raise ValueError("Valid owner email is required")

        response = self.http_client.post(
            "/identity/issuer/issue-credential",
            json={
                "did": options.did,
                "credentialName": options.credential_name,
                "values": options.values,
                "ownerEmail": options.owner_email,
            },
        )

        # Return response as is - it will have either qrCodeLink or txId/claimId
        if "qrCodeLink" in response:
            return {
                "qr_code_link": response["qrCodeLink"],
                "schema_type": response["schemaType"],
            }
        else:
            return {"tx_id": response["txId"], "claim_id": response["claimId"]}

    def get_credential_offer(
        self, options: GetCredentialOfferOptions
    ) -> GetCredentialOfferResponse:
        """
        Get credential offer link for MTP credentials

        This method covers the endpoint: GET /identity/issuer/get-credential-offer

        Args:
            options: Claim ID and transaction ID

        Returns:
            GetCredentialOfferResponse with status and QR code link (if available)

        Raises:
            ValueError: If claim ID or transaction ID is invalid
        """
        if not options.claim_id or not isinstance(options.claim_id, str):
            raise ValueError("Valid claim ID is required")

        if not options.tx_id or not isinstance(options.tx_id, str):
            raise ValueError("Valid transaction ID is required")

        response = self.http_client.get(
            "/identity/issuer/get-credential-offer",
            params={"claimId": options.claim_id, "txId": options.tx_id},
        )

        return GetCredentialOfferResponse(
            status=response["status"],
            tx_id=response["txId"],
            claim_id=response["claimId"],
            offer_available=response["offerAvailable"],
            qr_code_link=response.get("qrCodeLink"),
            offer=response.get("offer"),
            message=response.get("message"),
        )
