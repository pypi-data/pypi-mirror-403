"""IPFS for credential storage operations"""

from typing import Union, Dict, Any
from ....types import (
    StoreCredentialOptions,
    StoreCredentialResponse,
    RetrieveUserCredentialOptions,
    RetrieveUserCredentialResponse,
    GetAllUserCredentialsOptions,
    GetAllUserCredentialsResponse,
)
from ....utils.http import HTTPClient


class IPFS:
    """IPFS module for credential storage and retrieval operations"""

    def __init__(self, http_client: HTTPClient):
        self.http_client = http_client

    def store_credential(
        self, options: StoreCredentialOptions
    ) -> StoreCredentialResponse:
        """
        Store credential data to IPFS and PostgreSQL

        This method covers the endpoint: POST /identity/ipfs/store-credential

        Args:
            options: DID, credential type, credential data, and encryption flag

        Returns:
            StoreCredentialResponse with CID and credential information

        Raises:
            ValueError: If any required field is invalid
        """
        if not options.did or not isinstance(options.did, str):
            raise ValueError("Valid DID is required")

        if not options.credential_type or not isinstance(
            options.credential_type, str
        ):
            raise ValueError("Valid credential type is required")

        if not options.credential:
            raise ValueError("Credential data is required")

        encrypted = options.encrypted

        if encrypted and not isinstance(options.credential, str):
            raise ValueError("Encrypted credentials must be provided as string")

        if not encrypted and not isinstance(options.credential, dict):
            raise ValueError("Unencrypted credentials must be provided as object")

        response = self.http_client.post(
            "/identity/ipfs/store-credential",
            json={
                "did": options.did,
                "credentialType": options.credential_type,
                "credential": options.credential,
                "encrypted": encrypted,
            },
        )

        return StoreCredentialResponse(
            cid=response["cid"],
            did=response["did"],
            credential_type=response["credentialType"],
            message=response["message"],
            encrypted=response["encrypted"],
        )

    def retrieve_user_credential(
        self, options: RetrieveUserCredentialOptions
    ) -> RetrieveUserCredentialResponse:
        """
        Retrieve user credential from PostgreSQL and IPFS

        This method covers the endpoint: POST /identity/retrieve-user-credential

        Args:
            options: DID, credential type, and optional includeCidOnly flag

        Returns:
            RetrieveUserCredentialResponse with credential data and metadata

        Raises:
            ValueError: If DID or credential type is invalid
        """
        if not options.did or not isinstance(options.did, str):
            raise ValueError("Valid DID is required")

        if not options.credential_type or not isinstance(
            options.credential_type, str
        ):
            raise ValueError("Valid credential type is required")

        include_cid_only = options.include_cid_only

        response = self.http_client.post(
            "/identity/retrieve-user-credential",
            json={
                "did": options.did,
                "credentialType": options.credential_type,
                "includeCidOnly": include_cid_only,
            },
        )

        return RetrieveUserCredentialResponse(
            cid=response["cid"],
            did=response["did"],
            credential_type=response["credentialType"],
            message=response["message"],
            credential=response.get("credential"),
            encrypted=response.get("encrypted"),
        )

    def get_all_user_credentials(
        self, options: GetAllUserCredentialsOptions
    ) -> GetAllUserCredentialsResponse:
        """
        Get all user credentials from PostgreSQL and optionally IPFS

        This method covers the endpoint: POST /identity/get-all-user-credentials

        Args:
            options: DID and optional includeCredentialData flag

        Returns:
            GetAllUserCredentialsResponse with all user credentials

        Raises:
            ValueError: If DID is invalid
        """
        if not options.did or not isinstance(options.did, str):
            raise ValueError("Valid DID is required")

        include_credential_data = options.include_credential_data

        response = self.http_client.post(
            "/identity/get-all-user-credentials",
            json={
                "did": options.did,
                "includeCredentialData": include_credential_data,
            },
        )

        return GetAllUserCredentialsResponse(
            credentials=response["credentials"],
            did=response["did"],
            count=response["count"],
            message=response["message"],
        )
