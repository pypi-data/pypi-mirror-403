"""Resource Owner Password OAuth 2.0 flow authentication provider.

This module implements the Resource Owner Password Flow authentication method,
which allows highly-trusted applications to authenticate users by collecting
their username and password credentials directly.

Security Warning: This flow should only be used by absolutely trusted
applications as it requires handling user passwords directly. It's typically
used for legacy applications or first-party applications where other OAuth flows
are not feasible.

This implementation handles token caching and automatic renewal when tokens expire,
similar to the Client Credentials Flow but using username/password credentials.
"""

import logging
from os import getenv

import httpx

from cmem_client.auth_provider.abc import AuthProvider
from cmem_client.config import Config
from cmem_client.exceptions import ClientEnvConfigError
from cmem_client.models.token import KeycloakToken


class PasswordFlow(AuthProvider):
    """Resource Owner Password OAuth 2.0 flow authentication provider.

    Security Warning: This authentication flow should only be used by
    absolutely trusted applications as it requires handling user passwords directly.

    Implements the Resource Owner Password Flow (RFC 6749, section 4.3) for
    authentication with Corporate Memory via Keycloak. This flow exchanges user
    credentials (username and password) directly for access tokens, bypassing
    the standard OAuth 2.0 authorization code flow.

    This provider handles automatic token caching and refresh, ensuring that
    get_access_token() always returns a valid token. It's typically used for
    legacy applications, first-party applications, or scenarios where the standard
    OAuth flows are not feasible.

    Attributes:
        client_id: The OAuth 2.0 client identifier for the application.
        username: The user's username for authentication.
        password: The user's password for authentication.
        config: Corporate Memory configuration containing endpoint URLs.
        httpx: HTTP client for making token requests to the OAuth server.
        token: Currently cached Keycloak token with expiration tracking.

    Security Considerations:
        - User credentials are sent directly to the authorization server
        - Passwords may be stored in memory for token refresh purposes
        - Only use in highly trusted applications with secure credential handling
        - Consider using Client Credentials Flow for machine-to-machine auth instead

    See Also:
        https://auth0.com/docs/get-started/authentication-and-authorization-flow/resource-owner-password-flow
        https://tools.ietf.org/html/rfc6749#section-4.3
    """

    client_id: str
    """OAuth 2.0 client identifier used to identify the application to the authorization server."""

    username: str
    """User's username/email for authentication with the OAuth server."""

    password: str
    """User's password for authentication. ⚠️ Stored in memory for token refresh."""

    config: Config
    """Corporate Memory configuration containing OAuth token endpoint and other URLs."""

    httpx: httpx.Client
    """HTTP client instance used for making requests to the OAuth token endpoint."""

    token: KeycloakToken
    """Currently cached access token with automatic expiration tracking and JWT parsing."""

    logger: logging.Logger
    """Logger object used to log messages."""

    def __init__(self, config: Config, client_id: str, username: str, password: str) -> None:
        """Initialize a new Resource Owner Password Flow authentication provider.

        Security Warning: This constructor stores the user's password in memory
        for potential token refresh operations. Only use in absolutely trusted applications.

        Creates a new provider instance and immediately fetches an initial access
        token. The provider will handle token refresh automatically when needed.

        Args:
            config: Corporate Memory configuration containing OAuth endpoint URLs
                and other connection details.
            client_id: The OAuth 2.0 client identifier registered with the
                authorization server.
            username: The user's username or email address for authentication.
            password: The user's password for authentication.

        Raises:
            HTTPError: If the initial token request fails due to network issues
                or invalid credentials.
            ValidationError: If the token response cannot be parsed as a valid
                Keycloak token.

        Security Note:
            The constructor makes an immediate HTTP request to fetch the initial
            token, sending the user's credentials over the network. Ensure secure
            network connections (HTTPS) and proper credential handling.
        """
        self.config = config
        self.client_id = client_id
        self.username = username
        self.password = password
        self.httpx = httpx.Client()
        self.logger = logging.getLogger(__name__)
        self.token = self.fetch_new_token()

    @classmethod
    def from_env(cls, config: Config) -> "PasswordFlow":
        """Create a Password Flow provider from environment variables.

        Security Warning: This method reads user credentials from environment
        variables, which may be visible in process lists or logs. Use with extreme caution.

        This factory method creates a provider instance by reading user credentials
        from environment variables. While more secure than hardcoded credentials,
        environment variables should be properly protected in production environments.

        Args:
            config: Corporate Memory configuration containing OAuth endpoint URLs.

        Returns:
            A configured PasswordFlow instance ready for use.

        Raises:
            ClientEnvConfigError: If the required OAUTH_USER or OAUTH_PASSWORD
                environment variables are not set.

        Environment Variables:
            OAUTH_USER (required): The username or email address for authentication.
                Must be a valid user account in the Corporate Memory system.
            OAUTH_PASSWORD (required): The user's password for authentication.
                Should be handled securely and not logged.
            OAUTH_CLIENT_ID (optional): The OAuth 2.0 client identifier.
                Defaults to "cmem-service-account" if not specified.

        Security Notes:
            - Environment variables may be visible in process lists
            - Use secure credential management in production environments
            - Consider using Client Credentials Flow for service accounts instead
            - Ensure proper access controls on systems storing these credentials
        """
        oauth_user = getenv("OAUTH_USER")
        oauth_password = getenv("OAUTH_PASSWORD")
        oauth_client_id = getenv("OAUTH_CLIENT_ID", "cmem-service-account")
        if not oauth_user:
            raise ClientEnvConfigError("Need OAUTH_USER environment variable.")
        if not oauth_password:
            raise ClientEnvConfigError("Need OAUTH_PASSWORD environment variable.")
        return cls(username=oauth_user, password=oauth_password, config=config, client_id=oauth_client_id)

    @classmethod
    def from_cmempy(cls, config: Config) -> "PasswordFlow":
        """Create a Password Flow provider from a cmempy environment."""
        try:
            import cmem.cmempy.config as cmempy_config  # noqa: PLC0415
        except ImportError as error:
            raise OSError("cmempy is not installed.") from error
        oauth_user = cmempy_config.get_oauth_user()
        oauth_password = cmempy_config.get_oauth_password()
        oauth_client_id = cmempy_config.get_oauth_client_id()
        if not oauth_user:
            raise ClientEnvConfigError("Need OAUTH_USER environment variable.")
        if not oauth_password:
            raise ClientEnvConfigError("Need OAUTH_PASSWORD environment variable.")
        return cls(username=oauth_user, password=oauth_password, config=config, client_id=oauth_client_id)

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
                credentials (username/password may have changed).
            ValidationError: If the token response cannot be parsed.

        Security Note:
            Each token refresh operation sends the username and password over
            the network. Ensure secure connections (HTTPS) and consider token
            lifetime implications for security.
        """
        if self.token.is_expired():
            self.logger.debug("Access token expired, refreshing...")
            self.token = self.fetch_new_token()
        return self.token.access_token

    def fetch_new_token(self) -> KeycloakToken:
        """Fetch a new access token from the OAuth 2.0 token endpoint.

        Security Warning: This method sends user credentials (username and password)
        over the network to the authorization server. Ensure secure connections (HTTPS).

        Makes an HTTP POST request to the Keycloak token endpoint using the
        Resource Owner Password Flow parameters. The response is parsed and returned
        as a KeycloakToken object with automatic expiration tracking.

        Returns:
            A new KeycloakToken instance with the fresh access token and
            expiration information.

        Raises:
            HTTPError: If the token request fails due to network issues,
                invalid credentials, or server errors.
            ValidationError: If the token response cannot be parsed as a
                valid Keycloak token format.

        Security Considerations:
            - User credentials are sent in plaintext (over HTTPS)
            - Consider the security implications of credential reuse for token refresh
            - Monitor for credential compromise if tokens are frequently refreshed

        Note:
            This method performs a synchronous HTTP request and should not be
            called directly in most cases. Use get_access_token() instead,
            which handles caching and only calls this method when necessary.

        Implementation Details:
            - Uses the standard OAuth 2.0 Resource Owner Password Flow parameters
            - Sends credentials in the request body (not in Authorization header)
            - Automatically decodes the JSON response and validates the format
            - Extracts JWT claims for expiration tracking
        """
        self.logger.debug("Fetching new access token from OAuth 2.0 token endpoint.")
        post_data = {
            "grant_type": "password",
            "client_id": self.client_id,
            "username": self.username,
            "password": self.password,
        }
        response = self.httpx.post(url=self.config.url_oauth_token, data=post_data)
        response.raise_for_status()
        content = response.content.decode("utf-8")
        self.logger.debug("Successfully fetched new access token from OAuth 2.0 token endpoint.")
        return KeycloakToken.model_validate_json(json_data=content)
