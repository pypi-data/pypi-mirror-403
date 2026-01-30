"""Prefetched token authentication provider.

This module provides an authentication provider for scenarios where access tokens
are obtained through external means rather than through OAuth flows. This is useful
for environments where tokens are managed by external systems, CI/CD pipelines,
or when integrating with existing authentication infrastructure.

The PrefetchedToken provider simply stores and returns a pre-obtained access token
without performing any token refresh or validation. It's the responsibility of the
external system to ensure the token is valid and renewed when necessary.

This approach is often used in containerized environments, serverless functions,
or when tokens are managed by orchestration platforms.
"""

import logging
from os import getenv

from cmem_client.auth_provider.abc import AuthProvider
from cmem_client.config import Config
from cmem_client.exceptions import ClientEnvConfigError


class PrefetchedToken(AuthProvider):
    """Authentication provider for externally managed access tokens.

    PrefetchedToken is designed for scenarios where access tokens are obtained
    and managed by external systems rather than through standard OAuth 2.0 flows.
    This provider simply stores and returns a pre-obtained token without performing
    any validation, refresh, or expiration checking.

    This approach is commonly used in:
    - Containerized environments where tokens are injected at runtime
    - CI/CD pipelines with token management systems
    - Serverless functions with external authentication services
    - Integration with existing authentication infrastructure
    - Short-lived execution contexts where token refresh isn't needed

    Attributes:
        prefetched_token: The pre-obtained access token to be used for authentication.

    Important Notes:
        - No token validation or expiration checking is performed
        - Token refresh is not supported; external systems must handle renewal
        - The token is assumed to be valid and properly formatted
        - Suitable for short-lived processes or external token management scenarios

    See Also:
        For automatic token management with refresh capabilities, consider using
        ClientCredentialsFlow or PasswordFlow instead.
    """

    prefetched_token: str
    """The pre-obtained access token used for authentication requests."""

    logger: logging.Logger
    """Logger object for logging."""

    def __init__(self, prefetched_token: str) -> None:
        """Initialize a new Prefetched Token authentication provider.

        Creates a provider instance that stores the given access token for use
        in authentication requests. No validation or processing is performed
        on the token; it is stored as-is.

        Args:
            prefetched_token: A pre-obtained access token string. The token
                should be valid, properly formatted (typically JWT), and
                have appropriate permissions for Corporate Memory operations.

        Note:
            Unlike other authentication providers, this constructor does not
            make any network requests or perform token validation. The token
            is assumed to be valid and ready for immediate use.
        """
        self.prefetched_token = prefetched_token
        self.logger: logging.Logger = logging.getLogger(__name__)

    @classmethod
    def from_env(cls, config: Config) -> "PrefetchedToken":  # noqa: ARG003
        """Create a Prefetched Token provider from environment variables.

        This factory method creates a provider instance by reading a pre-obtained
        access token from the OAUTH_ACCESS_TOKEN environment variable.

        Args:
            config: Corporate Memory configuration object. Note that this parameter
                is not used by PrefetchedToken but is required to maintain
                consistency with other AuthProvider implementations.

        Returns:
            A configured PrefetchedToken instance ready for use.

        Raises:
            ClientEnvConfigError: If the required OAUTH_ACCESS_TOKEN environment
                variable is not set or is empty.

        Environment Variables:
            OAUTH_ACCESS_TOKEN (required): The pre-obtained access token.
                Should be a valid JWT or other token format accepted by
                Corporate Memory. The token must have appropriate permissions
                for the intended operations.

        Use Cases:
            - Docker containers with token injection
            - Kubernetes pods with secret mounting
            - CI/CD pipelines with secure token storage
            - Serverless functions with environment-based configuration
            - Integration with external token management systems
        """
        oauth_access_token = getenv("OAUTH_ACCESS_TOKEN")
        if not oauth_access_token:
            raise ClientEnvConfigError("Need OAUTH_ACCESS_TOKEN environment variable.")
        return cls(prefetched_token=oauth_access_token)

    @classmethod
    def from_cmempy(cls, config: Config) -> "PrefetchedToken":  # noqa: ARG003
        """Create a Prefetched Token provider from a cmempy environment."""
        try:
            import cmem.cmempy.config as cmempy_config  # noqa: PLC0415
        except ImportError as error:
            raise OSError("cmempy is not installed.") from error
        oauth_access_token = cmempy_config.get_oauth_access_token()
        if not oauth_access_token:
            raise ClientEnvConfigError("Need OAUTH_ACCESS_TOKEN environment variable.")
        return cls(prefetched_token=oauth_access_token)

    def get_access_token(self) -> str:
        """Get the prefetched access token for Bearer Authorization header.

        Returns the stored access token without any validation, refresh, or
        expiration checking. The token is returned as-is, exactly as it was
        provided during initialization.

        Returns:
            The prefetched access token string ready for use in HTTP
            Authorization headers.

        Important Notes:
            - No validation is performed on the token
            - No expiration checking is done
            - No automatic refresh capability
            - The token is assumed to be valid and current
            - External systems are responsible for token lifecycle management

        Limitations:
            Unlike other AuthProvider implementations, this method does not:
            - Check token expiration
            - Refresh expired tokens
            - Validate token format
            - Handle token renewal
        """
        return self.prefetched_token
