"""Main DCID Server SDK Client"""

from typing import Optional
from .types import DCIDServerSDKConfig, TokenResponse
from .config.environments import get_environment_config
from .utils.logger import ConsoleLogger, NoOpLogger
from .utils.http import create_http_client
from .modules.auth.otp import AuthOTP
from .modules.identity.encryption.key_manager import KeyManager
from .modules.identity.issuer.issuer import Issuer
from .modules.identity.ipfs.ipfs import IPFS
from .modules.identity.verification.verification import Verification
from .modules.analytics.analytics import Analytics


class Identity:
    """Identity module container"""

    def __init__(
        self,
        encryption: KeyManager,
        issuer: Issuer,
        ipfs: IPFS,
        verification: Verification,
    ):
        self.encryption = encryption
        self.issuer = issuer
        self.ipfs = ipfs
        self.verification = verification


class DCIDServerSDK:
    """
    Main DCID Server SDK Client

    This is the main entry point for using the SDK.

    Example:
        ```python
        from dcid_server_sdk import DCIDServerSDK

        sdk = DCIDServerSDK(
            api_key='your-api-key-here',
            environment='prod'  # or 'dev'
        )

        # Register with OTP
        await sdk.auth.register_otp(email='user@example.com')

        # Confirm OTP (tokens are automatically set in SDK context)
        tokens = await sdk.auth.confirm_otp(
            email='user@example.com',
            otp='123456'
        )

        # Generate encryption key (will auto-refresh token if expired)
        await sdk.identity.encryption.generate_key(
            did='did:iden3:dcid:main:...',
            owner_email='user@example.com'
        )
        ```
    """

    def __init__(self, config: Optional[DCIDServerSDKConfig] = None, **kwargs):
        """
        Creates a new DCID Server SDK instance

        Args:
            config: SDK configuration (can also pass as kwargs)
            **kwargs: Configuration options as keyword arguments
        """
        # Support both config object and kwargs
        if config is None:
            config = DCIDServerSDKConfig(**kwargs)
        elif kwargs:
            # Merge kwargs into config
            for key, value in kwargs.items():
                setattr(config, key, value)

        if not config.api_key:
            raise ValueError("api_key is required in SDK configuration")

        # Get environment configuration
        env_config = get_environment_config(config.environment)

        # Remove trailing slash from baseUrl
        self._base_url = env_config.base_url.rstrip("/")

        # Setup logger
        environment = config.environment
        logger = config.logger or (
            ConsoleLogger(True) if environment == "dev" else NoOpLogger()
        )

        # Determine if request logging should be enabled
        enable_request_logging = (
            config.enable_request_logging
            if config.enable_request_logging is not None
            else environment == "dev"
        )

        # Create default headers with API key
        default_headers = {
            "X-API-Key": config.api_key,
            **(config.default_headers or {}),
        }

        # Token storage
        self._auth_token: Optional[str] = None
        self._refresh_token: Optional[str] = None

        # Create getter functions for tokens
        def get_auth_token() -> Optional[str]:
            return self._auth_token

        def get_refresh_token() -> Optional[str]:
            return self._refresh_token

        # Create HTTP client for unauthenticated requests (auth module)
        http_client = create_http_client(
            self._base_url,
            config.timeout,
            default_headers,
            None,
            None,
            None,
            None,
            logger,
            enable_request_logging,
        )

        # Callback to automatically set tokens after successful OTP confirmation
        def on_tokens_received(tokens: TokenResponse) -> None:
            self._auth_token = tokens.access_token
            self._refresh_token = tokens.refresh_token

        # Initialize auth module first (needed for refresh callback)
        self.auth = AuthOTP(http_client, on_tokens_received)

        # Callback to refresh token using SDK's refreshToken method
        def refresh_token_callback(refresh_token: str) -> TokenResponse:
            from .types import RefreshTokenOptions

            return self.auth.refresh_token(
                RefreshTokenOptions(refresh_token=refresh_token)
            )

        # Callback to handle token refresh result
        def on_token_refreshed(tokens: TokenResponse) -> None:
            self._auth_token = tokens.access_token
            self._refresh_token = tokens.refresh_token

        # Create HTTP client for authenticated requests
        authenticated_http_client = create_http_client(
            self._base_url,
            config.timeout,
            default_headers,
            get_auth_token,
            get_refresh_token,
            refresh_token_callback,
            on_token_refreshed,
            logger,
            enable_request_logging,
        )

        # Initialize identity modules
        self.identity = Identity(
            encryption=KeyManager(authenticated_http_client),
            issuer=Issuer(authenticated_http_client),
            ipfs=IPFS(authenticated_http_client),
            verification=Verification(authenticated_http_client),
        )

        # Analytics uses unauthenticated HTTP client (public endpoint)
        analytics_http_client = create_http_client(
            "",  # Base URL is empty since we use full URL in analytics methods
            config.timeout,
            default_headers,
            None,
            None,
            None,
            None,
            logger,
            enable_request_logging,
        )
        self.analytics = Analytics(analytics_http_client, self._base_url)

    def set_tokens(self, tokens: TokenResponse) -> None:
        """
        Sets the authorization and refresh tokens for authenticated requests

        Args:
            tokens: Token response containing access_token and refresh_token
        """
        self._auth_token = tokens.access_token
        self._refresh_token = tokens.refresh_token

    def set_auth_token(self, token: str) -> None:
        """
        Sets the authorization token for authenticated requests

        Args:
            token: JWT access token
        """
        self._auth_token = token

    def set_refresh_token(self, token: str) -> None:
        """
        Sets the refresh token

        Args:
            token: JWT refresh token
        """
        self._refresh_token = token

    def get_auth_token(self) -> Optional[str]:
        """Gets the current authorization token"""
        return self._auth_token

    def get_refresh_token(self) -> Optional[str]:
        """Gets the current refresh token"""
        return self._refresh_token
