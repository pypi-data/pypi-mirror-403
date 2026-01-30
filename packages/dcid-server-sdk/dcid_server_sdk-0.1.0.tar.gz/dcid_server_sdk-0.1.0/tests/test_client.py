"""Tests for client.py — DCIDServerSDK."""

import pytest
from unittest.mock import patch

from dcid_server_sdk.client import DCIDServerSDK, Identity
from dcid_server_sdk.types import DCIDServerSDKConfig, TokenResponse
from dcid_server_sdk.modules.auth.otp import AuthOTP
from dcid_server_sdk.modules.identity.encryption.key_manager import KeyManager
from dcid_server_sdk.modules.identity.issuer.issuer import Issuer
from dcid_server_sdk.modules.identity.ipfs.ipfs import IPFS
from dcid_server_sdk.modules.identity.verification.verification import Verification
from dcid_server_sdk.modules.analytics.analytics import Analytics


# ---------------------------------------------------------------------------
# Initialization
# ---------------------------------------------------------------------------

class TestDCIDServerSDKInit:
    def test_api_key_required(self):
        with pytest.raises(ValueError, match="api_key is required"):
            DCIDServerSDK(api_key="")

    def test_api_key_required_with_config(self):
        with pytest.raises(ValueError, match="api_key is required"):
            DCIDServerSDK(config=DCIDServerSDKConfig(api_key=""))

    def test_creates_with_valid_key(self):
        sdk = DCIDServerSDK(api_key="test-key")
        assert sdk is not None

    def test_defaults_to_prod(self):
        sdk = DCIDServerSDK(api_key="test-key")
        assert sdk._base_url == "https://gateway.trustid.life/api"

    def test_dev_environment(self):
        sdk = DCIDServerSDK(api_key="test-key", environment="dev")
        assert sdk._base_url == "http://krakend.dev-external.trustid.life/api"

    def test_trims_trailing_slash(self):
        sdk = DCIDServerSDK(
            config=DCIDServerSDKConfig(api_key="test-key", environment="dev")
        )
        assert not sdk._base_url.endswith("/")

    def test_modules_initialized(self):
        sdk = DCIDServerSDK(api_key="test-key")
        assert isinstance(sdk.auth, AuthOTP)
        assert isinstance(sdk.identity, Identity)
        assert isinstance(sdk.identity.encryption, KeyManager)
        assert isinstance(sdk.identity.issuer, Issuer)
        assert isinstance(sdk.identity.ipfs, IPFS)
        assert isinstance(sdk.identity.verification, Verification)
        assert isinstance(sdk.analytics, Analytics)

    def test_config_object(self):
        config = DCIDServerSDKConfig(api_key="test-key", environment="dev")
        sdk = DCIDServerSDK(config=config)
        assert sdk._base_url == "http://krakend.dev-external.trustid.life/api"

    def test_kwargs_merge_into_config(self):
        config = DCIDServerSDKConfig(api_key="old-key")
        sdk = DCIDServerSDK(config=config, api_key="new-key")
        # Merged kwarg should take effect — SDK created successfully
        assert sdk is not None

    def test_custom_timeout(self):
        sdk = DCIDServerSDK(api_key="test-key", timeout=60000)
        assert sdk is not None

    def test_enable_request_logging(self):
        sdk = DCIDServerSDK(api_key="test-key", enable_request_logging=True)
        assert sdk is not None


# ---------------------------------------------------------------------------
# Token management
# ---------------------------------------------------------------------------

class TestTokenManagement:
    def test_tokens_initially_none(self):
        sdk = DCIDServerSDK(api_key="test-key")
        assert sdk.get_auth_token() is None
        assert sdk.get_refresh_token() is None

    def test_set_tokens(self):
        sdk = DCIDServerSDK(api_key="test-key")
        sdk.set_tokens(TokenResponse(access_token="at-123", refresh_token="rt-456"))
        assert sdk.get_auth_token() == "at-123"
        assert sdk.get_refresh_token() == "rt-456"

    def test_set_auth_token(self):
        sdk = DCIDServerSDK(api_key="test-key")
        sdk.set_auth_token("token-abc")
        assert sdk.get_auth_token() == "token-abc"

    def test_set_refresh_token(self):
        sdk = DCIDServerSDK(api_key="test-key")
        sdk.set_refresh_token("refresh-xyz")
        assert sdk.get_refresh_token() == "refresh-xyz"

    def test_set_tokens_overwrites(self):
        sdk = DCIDServerSDK(api_key="test-key")
        sdk.set_tokens(TokenResponse(access_token="a1", refresh_token="r1"))
        sdk.set_tokens(TokenResponse(access_token="a2", refresh_token="r2"))
        assert sdk.get_auth_token() == "a2"
        assert sdk.get_refresh_token() == "r2"


# ---------------------------------------------------------------------------
# Identity container
# ---------------------------------------------------------------------------

class TestIdentityContainer:
    def test_holds_submodules(self):
        sdk = DCIDServerSDK(api_key="test-key")
        identity = sdk.identity
        assert identity.encryption is not None
        assert identity.issuer is not None
        assert identity.ipfs is not None
        assert identity.verification is not None
