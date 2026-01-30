"""Tests for config/environments.py"""

import pytest
from dcid_server_sdk.config.environments import (
    get_environment_config,
    ENVIRONMENTS,
    EnvironmentConfig,
)


class TestGetEnvironmentConfig:
    def test_dev_environment(self):
        config = get_environment_config("dev")
        assert config.base_url == "http://krakend.dev-external.trustid.life/api"

    def test_prod_environment(self):
        config = get_environment_config("prod")
        assert config.base_url == "https://gateway.trustid.life/api"

    def test_invalid_environment_raises(self):
        with pytest.raises(ValueError, match="Invalid environment"):
            get_environment_config("staging")

    def test_empty_string_raises(self):
        with pytest.raises(ValueError, match="Invalid environment"):
            get_environment_config("")

    def test_returns_environment_config_type(self):
        config = get_environment_config("dev")
        assert isinstance(config, EnvironmentConfig)


class TestEnvironmentsDict:
    def test_has_dev_and_prod(self):
        assert "dev" in ENVIRONMENTS
        assert "prod" in ENVIRONMENTS

    def test_dev_url(self):
        assert ENVIRONMENTS["dev"].base_url == "http://krakend.dev-external.trustid.life/api"

    def test_prod_url(self):
        assert ENVIRONMENTS["prod"].base_url == "https://gateway.trustid.life/api"
