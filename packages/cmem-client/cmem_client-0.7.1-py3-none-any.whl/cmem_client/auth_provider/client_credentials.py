"""Client Credentials OAuth 2.0 flow authentication provider.

This module implements the Client Credentials Flow authentication method for
accessing eccenca Corporate Memory via OAuth 2.0. This flow is designed for
machine-to-machine authentication where no user interaction is required.

The Client Credentials Flow exchanges client ID and client secret for an access
token directly with the authorization server. It's ideal for backend services,
APIs, and automated systems that need to authenticate without user involvement.

This implementation handles token caching and automatic renewal when tokens expire.
"""

import logging
from os import getenv

import httpx

from cmem_client.auth_provider.abc import AuthProvider
from cmem_client.config import Config
from cmem_client.exceptions import ClientEnvConfigError
from cmem_client.models.token import KeycloakToken


class ClientCredentialsFlow(AuthProvider):
    """Client Credentials OAuth 2.0 flow authentication provider.

    Implements the Client Credentials Flow (RFC 6749, section 4.4) for machine-to-machine
    authentication with Corporate Memory via Keycloak. This flow exchanges client credentials
    (client ID and secret) directly for access tokens without user interaction.

    The provider handles automatic token caching and refresh, ensuring that get_access_token()
    always returns a valid, non-expired token. It's designed for backend services, CLIs,
    daemons, and other automated systems that need to authenticate as an application
    rather than on behalf of a user.

    Attributes:
        client_id: The OAuth 2.0 client identifier for the application.
        client_secret: The confidential client secret for authentication.
        config: Corporate Memory configuration containing endpoint URLs.
        httpx: HTTP client for making token requests to the OAuth server.
        token: Currently cached Keycloak token with expiration tracking.

    See Also:
        https://auth0.com/docs/get-started/authentication-and-authorization-flow/client-credentials-flow
        https://tools.ietf.org/html/rfc6749#section-4.4
    """

    client_id: str
    """OAuth 2.0 client identifier used to identify the application to the authorization server."""

    client_secret: str
    """Confidential client secret used to authenticate the application with the OAuth server."""

    config: Config
    """Corporate Memory configuration containing OAuth token endpoint and other URLs."""

    httpx: httpx.Client
    """HTTP client instance used for making requests to the OAuth token endpoint."""

    token: KeycloakToken
    """Currently cached access token with automatic expiration tracking and JWT parsing."""

    logger: logging.Logger
    """Logger object for logging."""

    def __init__(self, config: Config, client_id: str, client_secret: str) -> None:
        """Initialize a new Client Credentials Flow authentication provider.

        Creates a new provider instance and immediately fetches an initial access
        token. The provider will handle token refresh automatically when needed.

        Args:
            config: Corporate Memory configuration containing OAuth endpoint URLs
                and other connection details.
            client_id: The OAuth 2.0 client identifier registered with the
                authorization server.
            client_secret: The confidential client secret associated with the
                client_id for authentication.

        Raises:
            HTTPError: If the initial token request fails due to network issues
                or invalid credentials.
            ValidationError: If the token response cannot be parsed as a valid
                Keycloak token.

        Note:
            The constructor makes an immediate HTTP request to fetch the initial
            token, so ensure network connectivity and valid credentials before
            instantiation.
        """
        self.config = config
        self.client_id = client_id
        self.client_secret = client_secret
        self.httpx = httpx.Client()
        self.logger = logging.getLogger(__name__)
        self.token = self.fetch_new_token()

    @classmethod
    def from_env(cls, config: Config) -> "ClientCredentialsFlow":
        """Create a Client Credentials Flow provider from environment variables.

        This factory method creates a provider instance by reading OAuth client
        credentials from environment variables. It's the recommended way to
        create providers in production environments where credentials are
        managed externally.

        Args:
            config: Corporate Memory configuration containing OAuth endpoint URLs.

        Returns:
            A configured ClientCredentialsFlow instance ready for use.

        Raises:
            ClientEnvConfigError: If the required OAUTH_CLIENT_SECRET environment
                variable is not set.

        Environment Variables:
            OAUTH_CLIENT_ID (optional): The OAuth 2.0 client identifier.
                Defaults to "cmem-service-account" if not specified.
            OAUTH_CLIENT_SECRET (required): The confidential client secret
                for authentication. Must be provided.

        Security Note:
            Client secrets should be stored securely and never committed to
            version control. Use environment variables or secure secret
            management systems in production.
        """
        oauth_client_id = getenv("OAUTH_CLIENT_ID", "cmem-service-account")
        oauth_client_secret = getenv("OAUTH_CLIENT_SECRET")
        if not oauth_client_secret:
            raise ClientEnvConfigError("Need OAUTH_CLIENT_SECRET environment variable.")
        return cls(client_secret=oauth_client_secret, client_id=oauth_client_id, config=config)

    @classmethod
    def from_cmempy(cls, config: Config) -> "ClientCredentialsFlow":
        """Create a Client Credentials Flow provider from a cmempy environment."""
        try:
            import cmem.cmempy.config as cmempy_config  # noqa: PLC0415
        except ImportError as error:
            raise OSError("cmempy is not installed.") from error
        oauth_client_id = cmempy_config.get_oauth_client_id()
        oauth_client_secret = cmempy_config.get_oauth_client_secret()
        if not oauth_client_secret:
            raise ClientEnvConfigError("Need OAUTH_CLIENT_SECRET environment variable.")
        return cls(client_secret=oauth_client_secret, client_id=oauth_client_id, config=config)

    def get_access_token(self) -> str:
        """Get a valid access token for Bearer Authorization header.

        Returns a valid access token, automatically handling token refresh when
        the current token is expired or near expiration. This method implements
        intelligent caching to minimize unnecessary token requests while ensuring
        the returned token is always valid.

        Returns:
            A valid access token string ready for use in HTTP Authorization headers.

        Raises:
            HTTPError: If token refresh fails due to network issues or invalid
                credentials.
            ValidationError: If the token response cannot be parsed.
        """
        if self.token.is_expired():
            self.logger.debug("Access token expired, refreshing...")
            self.token = self.fetch_new_token()
        return self.token.access_token

    def fetch_new_token(self) -> KeycloakToken:
        """Fetch a new access token from the OAuth 2.0 token endpoint.

        Makes an HTTP POST request to the Keycloak token endpoint using the
        Client Credentials Flow parameters. The response is parsed and returned
        as a KeycloakToken object with automatic expiration tracking.

        Returns:
            A new KeycloakToken instance with the fresh access token and
            expiration information.

        Raises:
            HTTPError: If the token request fails due to network issues,
                invalid credentials, or server errors.
            ValidationError: If the token response cannot be parsed as a
                valid Keycloak token format.

        Note:
            This method performs a synchronous HTTP request and should not be
            called directly in most cases. Use get_access_token() instead,
            which handles caching and only calls this method when necessary.

        Implementation Details:
            - Uses the standard OAuth 2.0 Client Credentials Flow parameters
            - Sends credentials in the request body (not in Authorization header)
            - Automatically decodes the JSON response and validates the format
            - Extracts JWT claims for expiration tracking
        """
        self.logger.debug("Fetching new access token from OAuth 2.0 token endpoint.")
        post_data = {
            "grant_type": "client_credentials",
            "client_id": self.client_id,
            "client_secret": self.client_secret,
        }
        response = self.httpx.post(url=self.config.url_oauth_token, data=post_data)
        response.raise_for_status()
        content = response.content.decode("utf-8")
        self.logger.debug("Successfully fetched new access token from OAuth 2.0 token endpoint.")
        return KeycloakToken.model_validate_json(json_data=content)
