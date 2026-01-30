"""Key manager for encryption operations"""

from ....types import (
    GenerateEncryptionKeyOptions,
    GenerateEncryptionKeyResponse,
    GetEncryptedKeyOptions,
    GetEncryptedKeyResponse,
)
from ....utils.http import HTTPClient


class KeyManager:
    """KeyManager module for encryption key operations"""

    def __init__(self, http_client: HTTPClient):
        self.http_client = http_client

    def generate_key(
        self, options: GenerateEncryptionKeyOptions
    ) -> GenerateEncryptionKeyResponse:
        """
        Generate encryption key for a DID

        This method covers the endpoint: POST /identity/generate-encryption-key

        Args:
            options: DID and owner email

        Returns:
            GenerateEncryptionKeyResponse with encrypted key, DID, owner email, and message

        Raises:
            ValueError: If DID or owner email is invalid
        """
        if not options.did or not options.did.startswith("did:"):
            raise ValueError('Valid DID is required (must start with "did:")')

        if not options.owner_email or "@" not in options.owner_email:
            raise ValueError("Valid owner email is required")

        response = self.http_client.post(
            "/identity/generate-encryption-key",
            json={"did": options.did, "ownerEmail": options.owner_email},
        )

        return GenerateEncryptionKeyResponse(
            encrypted_key=response["encryptedKey"],
            did=response["did"],
            owner_email=response["ownerEmail"],
            message=response["message"],
        )

    def get_key(self, options: GetEncryptedKeyOptions) -> GetEncryptedKeyResponse:
        """
        Get encrypted key for a DID

        This method covers the endpoint: POST /identity/get-encrypted-key

        Args:
            options: DID

        Returns:
            GetEncryptedKeyResponse with encrypted key, DID, and message

        Raises:
            ValueError: If DID is invalid
        """
        if not options.did or not options.did.startswith("did:"):
            raise ValueError('Valid DID is required (must start with "did:")')

        response = self.http_client.post(
            "/identity/get-encrypted-key", json={"did": options.did}
        )

        return GetEncryptedKeyResponse(
            encrypted_key=response["encryptedKey"],
            did=response["did"],
            message=response["message"],
        )
