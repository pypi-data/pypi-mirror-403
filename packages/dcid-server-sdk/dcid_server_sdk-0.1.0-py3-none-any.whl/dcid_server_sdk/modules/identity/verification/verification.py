"""Verification for credential verification operations"""

from ....types import (
    VerifySignInOptions,
    VerifySignInResponse,
    PostLinkStoreOptions,
    PostLinkStoreResponse,
    GetLinkStoreOptions,
    GetLinkStoreResponse,
    VerifyCallbackOptions,
    VerifyCallbackResponse,
)
from ....utils.http import HTTPClient


class Verification:
    """Verification module for credential verification operations"""

    def __init__(self, http_client: HTTPClient):
        self.http_client = http_client

    def verify_sign_in(self, options: VerifySignInOptions) -> VerifySignInResponse:
        """
        Initiate sign-in verification request

        This method covers the endpoint: POST /identity/verify/sign-in

        Args:
            options: Credential name to verify

        Returns:
            VerifySignInResponse with proof request URL, iden3comm URL, and session ID

        Raises:
            ValueError: If credential name is invalid
        """
        if not options.credential_name or not isinstance(
            options.credential_name, str
        ):
            raise ValueError("Valid credential name is required")

        response = self.http_client.post(
            "/identity/verify/sign-in",
            json={"credentialName": options.credential_name},
        )

        return VerifySignInResponse(
            proof_request_url=response["proofRequestUrl"],
            iden3comm_url=response["iden3commUrl"],
            session_id=response["sessionId"],
        )

    def get_link_store(self, options: GetLinkStoreOptions) -> GetLinkStoreResponse:
        """
        Get proof request from Redis link store

        This method covers the endpoint: GET /identity/verify/link-store

        Args:
            options: Session ID to retrieve

        Returns:
            GetLinkStoreResponse with the full proof request JSON

        Raises:
            ValueError: If id is invalid
        """
        if not options.id or not isinstance(options.id, str):
            raise ValueError("Valid id is required")

        response = self.http_client.get(
            "/identity/verify/link-store", params={"id": options.id}
        )

        return GetLinkStoreResponse(
            id=response["id"],
            thid=response["thid"],
            type=response["type"],
            from_did=response["from"],
            typ=response["typ"],
            body=response["body"],
        )

    def post_link_store(
        self, options: PostLinkStoreOptions
    ) -> PostLinkStoreResponse:
        """
        Store proof request in Redis link store

        This method covers the endpoint: POST /identity/verify/link-store

        Args:
            options: Full proof request object (iden3comm authorization request)

        Returns:
            PostLinkStoreResponse with proof request URL and iden3comm URL

        Raises:
            ValueError: If any required field is invalid
        """
        if not options.id or not isinstance(options.id, str):
            raise ValueError("Valid id is required")

        if not options.body or not isinstance(options.body, dict):
            raise ValueError("Valid body object is required")

        if not options.body.get("callback_url") or not isinstance(
            options.body["callback_url"], str
        ):
            raise ValueError("Valid callbackUrl in body is required")

        if not isinstance(options.body.get("scope"), list):
            raise ValueError("Valid scope array in body is required")

        response = self.http_client.post(
            "/identity/verify/link-store",
            json={
                "id": options.id,
                "thid": options.thid,
                "type": options.type,
                "from": options.from_did,
                "typ": options.typ,
                "body": options.body,
            },
        )

        return PostLinkStoreResponse(
            proof_request_url=response["proofRequestUrl"],
            iden3comm_url=response["iden3commUrl"],
        )

    def verify_callback(
        self, options: VerifyCallbackOptions
    ) -> VerifyCallbackResponse:
        """
        Submit and verify proof response

        This method covers the endpoint: POST /identity/verify/callback

        Args:
            options: Session ID and JWZ token (proof response)

        Returns:
            VerifyCallbackResponse with verified authorization response

        Raises:
            ValueError: If session ID or token is invalid
        """
        if not options.session_id or not isinstance(options.session_id, str):
            raise ValueError("Valid session ID is required")

        if not options.token or not isinstance(options.token, str):
            raise ValueError("Valid token (JWZ) is required")

        response = self.http_client.post(
            "/identity/verify/callback",
            json={"token": options.token},
            params={"sessionId": options.session_id},
        )

        return VerifyCallbackResponse(
            id=response["id"],
            typ=response["typ"],
            type=response["type"],
            thid=response["thid"],
            body=response["body"],
            from_did=response["from"],
            to=response["to"],
        )
