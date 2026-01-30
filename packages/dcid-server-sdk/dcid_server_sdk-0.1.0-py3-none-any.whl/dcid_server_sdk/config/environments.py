"""Environment configuration for DCID SDK"""

from typing import Literal
from dataclasses import dataclass


@dataclass
class EnvironmentConfig:
    """Environment configuration"""
    base_url: str


ENVIRONMENTS = {
    "dev": EnvironmentConfig(
        base_url="http://krakend.dev-external.trustid.life/api"
    ),
    "prod": EnvironmentConfig(
        base_url="https://gateway.trustid.life/api"
    ),
}


def get_environment_config(
    environment: Literal["dev", "prod"]
) -> EnvironmentConfig:
    """
    Get environment configuration

    Args:
        environment: Environment name ('dev' or 'prod')

    Returns:
        Environment configuration

    Raises:
        ValueError: If environment is invalid
    """
    config = ENVIRONMENTS.get(environment)
    if not config:
        raise ValueError(
            f"Invalid environment: {environment}. Must be 'dev' or 'prod'."
        )
    return config
