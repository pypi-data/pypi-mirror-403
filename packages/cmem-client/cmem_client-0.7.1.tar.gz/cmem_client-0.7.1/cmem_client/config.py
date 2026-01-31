"""Configuration management for the Corporate Memory client.

This module provides the Config class that handles all configuration aspects
of the Corporate Memory client, including URL construction, SSL verification,
authentication endpoints, and environment variable parsing.

The Config class automatically constructs various API endpoints based on a base URL
and provides flexible configuration through both programmatic setup and environment
variables, making it suitable for different deployment environments.
"""

from os import getenv

from cmem_client.exceptions import ClientEnvConfigError
from cmem_client.models.url import HttpUrl


class Config:
    """Corporate Memory Client configuration.

    The Config class manages all configuration aspects for connecting to Corporate
    Memory instances, including URL construction, SSL verification, timeout settings,
    and authentication endpoints. It provides both programmatic configuration and
    automatic configuration from environment variables.

    The class automatically constructs various API endpoints based on a base URL
    and realm configuration, with support for customizing individual endpoints
    when needed for complex deployment scenarios.

    Attributes:
        _realm_id: The Keycloak realm identifier for authentication.
        _verify: SSL/TLS certificate verification flag.
        _url_base: Base URL of the Corporate Memory instance.
        _url_keycloak: Base URL of the Keycloak authentication server.
        _url_keycloak_issuer: Keycloak realm issuer URL for token validation.
        _url_build_api: DataIntegration (build) API endpoint URL.
        _url_explore_api: DataPlatform (explore) API endpoint URL.
        _url_oauth_token: OAuth token endpoint URL for authentication.
        timeout: HTTP request timeout in seconds.
    """

    _realm_id: str = "cmem"
    """Keycloak realm identifier, defaults to 'cmem' for standard deployments."""

    _verify: bool = True
    """SSL/TLS certificate verification flag, defaults to True for security."""

    _url_base: HttpUrl
    """Base URL of the Corporate Memory instance, used to construct other endpoints."""

    _url_keycloak: HttpUrl
    """Base URL of the Keycloak authentication server, derived from base URL if not set."""

    _url_keycloak_issuer: HttpUrl
    """Keycloak realm issuer URL, constructed from Keycloak URL and realm ID."""

    _url_build_api: HttpUrl
    """DataIntegration (build) API endpoint URL, derived from base URL if not set."""

    _url_explore_api: HttpUrl
    """DataPlatform (explore) API endpoint URL, derived from base URL if not set."""

    _url_oauth_token: HttpUrl
    """OAuth token endpoint URL, constructed from Keycloak issuer URL."""

    timeout: int = 10
    """HTTP request timeout in seconds, defaults to 10 seconds."""

    def __init__(self, url_base: HttpUrl | str, realm_id: str = "cmem") -> None:
        """Initialize a new Config instance.

        Args:
            url_base: The base URL of the Corporate Memory instance. Can be
                provided as either an HttpUrl object or a string that will
                be converted to HttpUrl.
            realm_id: The Keycloak realm identifier for authentication.
                Defaults to "cmem" for standard Corporate Memory deployments.
        """
        self.url_base = HttpUrl(url_base) if isinstance(url_base, str) else url_base
        self.realm_id = realm_id

    @classmethod
    def from_env(cls) -> "Config":
        """Create a Config instance from environment variables.

        This factory method creates a configuration by reading various environment
        variables that specify Corporate Memory connection details. It provides
        a convenient way to configure the client in containerized or cloud
        environments where configuration is managed through environment variables.

        Returns:
            A Config instance configured with values from environment variables.

        Raises:
            ClientEnvConfigError: If the required CMEM_BASE_URI environment
                variable is not set.

        Environment Variables:
            CMEM_BASE_URI (required): Base URL of the Corporate Memory instance.
            DI_API_ENDPOINT (optional): DataIntegration API endpoint override.
            DP_API_ENDPOINT (optional): DataPlatform API endpoint override.
            KEYCLOAK_BASE_URI (optional): Keycloak server URL override.
            KEYCLOAK_REALM_ID (optional): Keycloak realm identifier override.
            OAUTH_TOKEN_URI (optional): OAuth token endpoint override.
            SSL_VERIFY (optional): SSL certificate verification flag.
        """
        cmem_base_uri = getenv("CMEM_BASE_URI")
        di_api_endpoint = getenv("DI_API_ENDPOINT")
        dp_api_endpoint = getenv("DP_API_ENDPOINT")
        keycloak_base_uri = getenv("KEYCLOAK_BASE_URI")
        keycloak_realm_id = getenv("KEYCLOAK_REALM_ID")
        oauth_token_uri = getenv("OAUTH_TOKEN_URI")
        ssl_verify = getenv("SSL_VERIFY")
        """
        requests_ca_bundle = getenv("REQUESTS_CA_BUNDLE")
        """

        if not cmem_base_uri:
            raise ClientEnvConfigError("CMEM_BASE_URI environment variable not set.")
        config = cls(url_base=cmem_base_uri)

        if ssl_verify:
            config.verify = bool(ssl_verify)
        if keycloak_realm_id:
            config.realm_id = keycloak_realm_id
        if keycloak_base_uri:
            config.url_keycloak = HttpUrl(keycloak_base_uri)
        if oauth_token_uri:
            config.url_oauth_token = HttpUrl(oauth_token_uri)
        if di_api_endpoint:
            config.url_build_api = HttpUrl(di_api_endpoint)
        if dp_api_endpoint:
            config.url_explore_api = HttpUrl(dp_api_endpoint)
        return config

    @classmethod
    def from_cmempy(cls) -> "Config":
        """Create a Config instance from a cmempy environment."""
        try:
            import cmem.cmempy.config as cmempy_config  # noqa: PLC0415
        except ImportError as error:
            raise OSError("cmempy is not installed.") from error
        cmem_base_uri = cmempy_config.get_cmem_base_uri()
        di_api_endpoint = cmempy_config.get_di_api_endpoint()
        dp_api_endpoint = cmempy_config.get_dp_api_endpoint()
        keycloak_base_uri = cmempy_config.get_keycloak_base_uri()
        keycloak_realm_id = cmempy_config.get_keycloak_realm_id()
        oauth_token_uri = cmempy_config.get_oauth_token_uri()
        ssl_verify = cmempy_config.get_ssl_verify()
        """
        requests_ca_bundle = getenv("REQUESTS_CA_BUNDLE")
        """

        if not cmem_base_uri:
            raise ClientEnvConfigError("CMEM_BASE_URI environment variable not set.")
        config = cls(url_base=cmem_base_uri)

        if ssl_verify:
            config.verify = bool(ssl_verify)
        if keycloak_realm_id:
            config.realm_id = keycloak_realm_id
        if keycloak_base_uri:
            config.url_keycloak = HttpUrl(keycloak_base_uri)
        if oauth_token_uri:
            config.url_oauth_token = HttpUrl(oauth_token_uri)
        if di_api_endpoint:
            config.url_build_api = HttpUrl(di_api_endpoint)
        if dp_api_endpoint:
            config.url_explore_api = HttpUrl(dp_api_endpoint)
        return config

    @property
    def verify(self) -> bool:
        """Get the SSL/TLS certificate verification flag.

        Returns:
            True if SSL/TLS certificates should be verified, False otherwise.
            Defaults to True for security reasons.

        Note:
            Disabling SSL verification should only be done in development
            environments. Production deployments should always verify certificates.
        """
        return self._verify

    @verify.setter
    def verify(self, value: bool) -> None:
        """Set the SSL/TLS certificate verification flag.

        Args:
            value: True to enable SSL/TLS certificate verification,
                False to disable it.

        Warning:
            Disabling SSL verification reduces security and should only be
            done in development environments or with proper security measures.
        """
        self._verify = value

    @property
    def url_base(self) -> HttpUrl:
        """Get the base URL of the Corporate Memory instance.

        Returns:
            The base URL from which all other API endpoints are derived.
            This is the root URL of the Corporate Memory deployment.
        """
        return self._url_base

    @url_base.setter
    def url_base(self, value: HttpUrl) -> None:
        """Set the base URL of the Corporate Memory instance.

        Args:
            value: The base URL of the Corporate Memory instance.
                Must be a valid HttpUrl object.

        Note:
            Changing the base URL will affect the construction of all
            derived endpoints unless they have been explicitly overridden.
        """
        self._url_base = value

    @property
    def url_explore_api(self) -> HttpUrl:
        """Get the DataPlatform (explore) API endpoint URL.

        Returns the URL for the DataPlatform API, which handles graph storage,
        SPARQL queries, and semantic data exploration. If not explicitly set,
        it defaults to the base URL with '/dataplatform/' appended.

        Returns:
            The DataPlatform API endpoint URL.
        """
        try:
            return self._url_explore_api
        except AttributeError:
            return self.url_base / "/dataplatform/"

    @url_explore_api.setter
    def url_explore_api(self, value: HttpUrl) -> None:
        """Set the DataPlatform (explore) API endpoint URL.

        Args:
            value: The DataPlatform API endpoint URL. This overrides the
                default URL construction based on the base URL.

        Note:
            Setting this explicitly allows for custom API endpoint configurations
            in complex deployment scenarios with separate DataPlatform services.
        """
        self._url_explore_api = value

    @property
    def url_build_api(self) -> HttpUrl:
        """Get the DataIntegration (build) API endpoint URL.

        Returns the URL for the DataIntegration API, which handles projects,
        datasets, transformations, and data integration workflows. If not
        explicitly set, it defaults to the base URL with '/dataintegration/' appended.

        Returns:
            The DataIntegration API endpoint URL.
        """
        try:
            return self._url_build_api
        except AttributeError:
            return self.url_base / "/dataintegration/"

    @url_build_api.setter
    def url_build_api(self, value: HttpUrl) -> None:
        """Set the DataIntegration (build) API endpoint URL.

        Args:
            value: The DataIntegration API endpoint URL. This overrides the
                default URL construction based on the base URL.

        Note:
            Setting this explicitly allows for custom API endpoint configurations
            in complex deployment scenarios with separate DataIntegration services.
        """
        self._url_build_api = value

    @property
    def url_keycloak(self) -> HttpUrl:
        """Get the Keycloak authentication server base URL.

        Returns the URL of the Keycloak server used for authentication and
        authorization. If not explicitly set, it defaults to the base URL
        with '/auth/' appended.

        Returns:
            The Keycloak server base URL.
        """
        try:
            return self._url_keycloak
        except AttributeError:
            return self.url_base / "/auth/"

    @url_keycloak.setter
    def url_keycloak(self, value: HttpUrl) -> None:
        """Set the Keycloak authentication server base URL.

        Args:
            value: The Keycloak server base URL. This overrides the default
                URL construction based on the base URL.

        Note:
            Setting this explicitly allows for configurations where Keycloak
            is deployed separately from the main Corporate Memory instance.
        """
        self._url_keycloak = value

    @property
    def url_keycloak_issuer(self) -> HttpUrl:
        """Get the Keycloak realm issuer URL.

        Returns the issuer URL for the specific Keycloak realm, which is used
        for token validation and OpenID Connect flows. This URL is constructed
        from the Keycloak base URL and the realm identifier.

        Returns:
            The Keycloak realm issuer URL.

        Note:
            This property cannot be set directly. It is automatically constructed
            based on the Keycloak URL and realm ID. To customize it, set the
            url_keycloak property and realm_id attribute instead.
        """
        try:
            return self._url_keycloak_issuer
        except AttributeError:
            return self.url_keycloak / f"/realms/{self.realm_id}/"

    @property
    def url_oauth_token(self) -> HttpUrl:
        """Get the OAuth 2.0 token endpoint URL.

        Returns the URL for the OAuth 2.0 token endpoint, which is used by
        authentication providers to obtain access tokens. If not explicitly
        set, it defaults to the standard OpenID Connect token endpoint path
        within the Keycloak realm.

        Returns:
            The OAuth 2.0 token endpoint URL.
        """
        try:
            return self._url_oauth_token
        except AttributeError:
            return self.url_keycloak_issuer / "/protocol/openid-connect/token"

    @url_oauth_token.setter
    def url_oauth_token(self, value: HttpUrl) -> None:
        """Set the OAuth 2.0 token endpoint URL.

        Args:
            value: The OAuth 2.0 token endpoint URL. This overrides the
                default URL construction based on the Keycloak issuer URL.

        Note:
            Setting this explicitly allows for custom OAuth configurations
            or alternative token endpoints in specialized deployment scenarios.
        """
        self._url_oauth_token = value
