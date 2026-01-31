"""Abstract base class and factory for authentication providers.

This module defines the AuthProvider abstract base class that establishes the
interface all authentication providers must implement. It also provides a
factory method that automatically selects the appropriate authentication
provider based on environment variables.

The factory method supports automatic configuration from environment variables,
making it easy to switch between different authentication methods without
code changes by simply setting the OAUTH_GRANT_TYPE environment variable.
"""

import logging
from abc import ABC, abstractmethod
from os import getenv

from cmem_client.config import Config
from cmem_client.exceptions import ClientEnvConfigError


class AuthProvider(ABC):
    """Abstract base class for authentication providers.

    AuthProvider defines the common interface that all authentication providers
    must implement to work with the Corporate Memory client. It provides the
    contract for obtaining access tokens and includes a factory method for
    creating appropriate provider instances based on environment configuration.

    All concrete authentication provider implementations must inherit from this
    class and implement the get_access_token method. The class also provides
    automatic provider selection through environment variables.
    """

    logger: logging.Logger
    """The logger for the auth provider."""

    @abstractmethod
    def get_access_token(self) -> str:
        """Get the access token for Bearer Authorization header.

        This method must be implemented by all concrete authentication providers
        to return a valid access token that can be used in HTTP Authorization
        headers for API requests.

        Returns:
            A valid access token string.

        Note:
            Implementations should handle token refresh logic internally when
            tokens expire, ensuring this method always returns a valid token.
        """

    @classmethod
    def from_env(cls, config: Config) -> "AuthProvider":
        """Create an authentication provider from environment variables.

        This factory method automatically selects and configures the appropriate
        authentication provider based on the OAUTH_GRANT_TYPE environment variable.
        It supports multiple OAuth 2.0 flows and authentication methods.

        Args:
            config: Configuration object containing Corporate Memory connection
                details and endpoint URLs.

        Returns:
            A configured AuthProvider instance appropriate for the environment
            configuration.

        Raises:
            ClientEnvConfigError: If the OAUTH_GRANT_TYPE is not supported or
                if required environment variables for the selected provider
                are missing.

        Environment Variables:
            OAUTH_GRANT_TYPE (optional): The OAuth flow type. Defaults to
                "client_credentials". Supported values:
                - "client_credentials": Client Credentials Flow for M2M auth
                - "password": Resource Owner Password Flow for trusted apps
                - "prefetched_token": Use externally obtained access token
        """
        oauth_grant_type = getenv("OAUTH_GRANT_TYPE", "client_credentials")

        if oauth_grant_type == "prefetched_token":
            from cmem_client.auth_provider.prefetched_token import PrefetchedToken  # noqa: PLC0415

            return PrefetchedToken.from_env(config=config)

        if oauth_grant_type == "client_credentials":
            from cmem_client.auth_provider.client_credentials import ClientCredentialsFlow  # noqa: PLC0415

            return ClientCredentialsFlow.from_env(config=config)

        if oauth_grant_type == "password":
            from cmem_client.auth_provider.password import PasswordFlow  # noqa: PLC0415

            return PasswordFlow.from_env(config=config)

        raise ClientEnvConfigError(f"No auth_provider configurable for the current environment ({oauth_grant_type})")

    @classmethod
    def from_cmempy(cls, config: Config) -> "AuthProvider":
        """Create an authentication provider from a cmempy environment."""
        try:
            import cmem.cmempy.config as cmempy_config  # noqa: PLC0415
        except ImportError as error:
            raise OSError("cmempy is not installed.") from error
        oauth_grant_type = cmempy_config.get_oauth_grant_type()

        if oauth_grant_type == "prefetched_token":
            from cmem_client.auth_provider.prefetched_token import PrefetchedToken  # noqa: PLC0415

            return PrefetchedToken.from_cmempy(config=config)

        if oauth_grant_type == "client_credentials":
            from cmem_client.auth_provider.client_credentials import ClientCredentialsFlow  # noqa: PLC0415

            return ClientCredentialsFlow.from_cmempy(config=config)

        if oauth_grant_type == "password":
            from cmem_client.auth_provider.password import PasswordFlow  # noqa: PLC0415

            return PasswordFlow.from_cmempy(config=config)

        raise ClientEnvConfigError(f"No auth_provider configurable for the current environment ({oauth_grant_type})")
