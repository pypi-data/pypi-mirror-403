"""OTP authentication module"""

from typing import Optional, Callable
from ...types import (
    InitiateOTPOptions,
    InitiateOTPResponse,
    ConfirmOTPOptions,
    TokenResponse,
    RefreshTokenOptions,
)
from ...utils.http import HTTPClient


class AuthOTP:
    """Authentication module for OTP-based registration and sign-in"""

    def __init__(
        self,
        http_client: HTTPClient,
        on_tokens_received: Optional[Callable[[TokenResponse], None]] = None,
    ):
        self.http_client = http_client
        self.on_tokens_received = on_tokens_received

    def register_otp(self, options: InitiateOTPOptions) -> InitiateOTPResponse:
        """
        Register-OTP: Initiates OTP registration/sign-in process

        This method covers the endpoint: POST /auth/sign-in/initiate

        Args:
            options: Email or phone

        Returns:
            InitiateOTPResponse with OTP code (only in dev environment)

        Raises:
            ValueError: If neither email nor phone is provided
        """
        if not options.email and not options.phone:
            raise ValueError("Either email or phone must be provided")

        # Only include non-None values in the request
        body = {}
        if options.email:
            body["email"] = options.email
        if options.phone:
            body["phone"] = options.phone

        response = self.http_client.post(
            "/auth/sign-in/initiate",
            json=body,
        )

        return InitiateOTPResponse(**response)

    def confirm_otp(self, options: ConfirmOTPOptions) -> TokenResponse:
        """
        Register-OTP (Confirm): Confirms OTP and completes registration/sign-in

        This method covers the endpoint: POST /auth/sign-in/confirm

        Args:
            options: Email/phone and the OTP code

        Returns:
            TokenResponse with access_token and refresh_token

        Raises:
            ValueError: If neither email nor phone is provided or OTP is missing
        """
        if not options.email and not options.phone:
            raise ValueError("Either email or phone must be provided")
        if not options.otp:
            raise ValueError("OTP code is required")

        # Only include non-None values in the request
        body = {"otp": options.otp}
        if options.email:
            body["email"] = options.email
        if options.phone:
            body["phone"] = options.phone

        response = self.http_client.post(
            "/auth/sign-in/confirm",
            json=body,
        )

        # Extract only the fields we need (backend may return extra Keycloak fields)
        tokens = TokenResponse(
            access_token=response.get("access_token"),
            refresh_token=response.get("refresh_token"),
            expires_in=response.get("expires_in"),
        )

        # Automatically set tokens in SDK context if callback is provided
        if self.on_tokens_received:
            self.on_tokens_received(tokens)

        return tokens

    def admin_login(self, options: InitiateOTPOptions) -> InitiateOTPResponse:
        """
        Sign In-OTP: Admin OTP registration/sign-in initiation

        This method covers the endpoint: POST /auth/sign-in/initiate?type=admin

        Args:
            options: Email or phone

        Returns:
            InitiateOTPResponse with OTP code (only in dev environment)

        Raises:
            ValueError: If neither email nor phone is provided
        """
        if not options.email and not options.phone:
            raise ValueError("Either email or phone must be provided")

        # Only include non-None values in the request
        body = {}
        if options.email:
            body["email"] = options.email
        if options.phone:
            body["phone"] = options.phone

        response = self.http_client.post(
            "/auth/sign-in/initiate?type=admin",
            json=body,
        )

        return InitiateOTPResponse(**response)

    def refresh_token(self, options: RefreshTokenOptions) -> TokenResponse:
        """
        Sign In-OTP (Refresh): Refreshes the access token using refresh token

        This method covers the endpoint: POST /auth/refresh-token

        Args:
            options: Refresh token

        Returns:
            TokenResponse with new access_token and refresh_token

        Raises:
            ValueError: If refresh token is not provided
        """
        if not options.refresh_token:
            raise ValueError("Refresh token is required")

        response = self.http_client.post(
            "/auth/refresh-token",
            json={"refreshToken": options.refresh_token},
        )

        # Extract only the fields we need (backend may return extra Keycloak fields)
        return TokenResponse(
            access_token=response.get("access_token"),
            refresh_token=response.get("refresh_token"),
            expires_in=response.get("expires_in"),
        )
