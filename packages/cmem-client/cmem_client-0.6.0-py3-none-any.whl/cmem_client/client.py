"""Main API client for eccenca Corporate Memory.

This module provides the primary Client class that serves as the central interface
for interacting with eccenca Corporate Memory instances. The Client orchestrates
authentication, HTTP communication, and provides access to various service components
like workspaces and graph stores.

The Client uses lazy loading for its components and can be configured either manually
or automatically from environment variables, making it flexible for different
deployment scenarios.

Examples:
    >>> from os import environ
    >>> from cmem_client.models.url import HttpUrl
    >>> from cmem_client.auth_provider.client_credentials import ClientCredentialsFlow
    >>> config = Config(url_base=HttpUrl(environ.get("TESTING_BASE_URL")))
    >>> client = Client(config=config)
    >>> client_id = environ.get("TESTING_CCF_CLIENT_ID")
    >>> client_secret = environ.get("TESTING_CCF_CLIENT_SECRET")
    >>> client.auth = ClientCredentialsFlow(config=config, client_id=client_id, client_secret=client_secret)
    >>> # Client is now configured with oauth provider from environment
"""

from __future__ import annotations

import json
import logging
from logging.config import dictConfig
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Any, ClassVar

import httpx

from cmem_client.auth_provider.abc import AuthProvider
from cmem_client.components.graph_store import GraphStore
from cmem_client.components.marketplace import Marketplace
from cmem_client.components.workspace import BuildWorkspace
from cmem_client.config import Config
from cmem_client.exceptions import ClientNoAuthProviderError
from cmem_client.logging_utils import install_trace_logger
from cmem_client.models.logging_config import LoggingConfig
from cmem_client.repositories.files import FilesRepository
from cmem_client.repositories.graph_imports import GraphImportsRepository
from cmem_client.repositories.graphs import GraphsRepository
from cmem_client.repositories.marketplace_packages import MarketplacePackagesRepository
from cmem_client.repositories.projects import ProjectsRepository
from cmem_client.repositories.python_packages import PythonPackagesRepository
from cmem_client.repositories.workflows import WorkflowsRepository


class Client:
    """API Client for eccenca Corporate Memory.

    The Client class provides the main interface for interacting with eccenca
    Corporate Memory instances. It manages authentication, HTTP communication,
    and provides access to various service components through lazy-loaded properties.

    The client follows a lazy initialization pattern where components are only
    created when first accessed, improving performance and reducing unnecessary
    resource allocation.

    Attributes:
        config: Configuration object containing URLs and connection settings.
        _headers: Class-level dictionary of HTTP headers shared across instances.
        _auth: Authentication provider for obtaining access tokens.
        _http: HTTP client instance for making API requests.
        _workspace: DataIntegration workspace component for build operations.
        _store: DataPlatform graph store component for explore operations.
    """

    config: Config
    """Configuration object containing URLs, timeouts, and SSL settings."""

    _logger: logging.Logger
    """Logger object for configuring logging."""

    _headers: ClassVar[dict] = {}
    """Class-level HTTP headers dictionary shared across all client instances."""

    _auth: AuthProvider
    """Authentication provider responsible for token management and refresh."""

    _http: httpx.Client
    """HTTP client instance configured with headers, SSL settings, and timeouts."""

    _workspace: BuildWorkspace
    """DataIntegration workspace component for project and dataset operations."""

    _store: GraphStore
    """DataPlatform graph store component for RDF graph operations."""

    _graphs: GraphsRepository
    """Graph repository for graphs."""

    _graph_imports: GraphImportsRepository
    """Graph Imports repository"""

    _vocabularies: GraphsRepository
    """Graph repository configured for vocabulary import and export operations."""

    _marketplace_packages: MarketplacePackagesRepository
    """MarketplacePackagesRepository object for marketplace package operations."""

    _python_packages: PythonPackagesRepository
    """PythonPackageRepository object for python package operations."""

    _projects: ProjectsRepository
    """ProjectsRepository object for project operations."""

    _marketplace: Marketplace
    """Marketplace repository object for marketplace server operations."""

    _workflows: WorkflowsRepository
    """WorkflowsRepository object for workflow operations."""

    _files: FilesRepository
    """FilesRepository object for file operations."""

    def __init__(
        self,
        config: Config,
        logger: logging.Logger | None = None,
    ) -> None:
        """Initialize a new Client instance.

        Args:
            config: Configuration object containing base URLs, SSL settings,
                and other connection parameters.
            logger: Optional Logger object for configuring logging.

        Note:
            The client requires an authentication provider to be set after
            initialization before it can make authenticated requests.
        """
        self.config = config
        self._logger = logger or logging.getLogger(__name__)
        install_trace_logger()

    @property
    def logger(self) -> logging.Logger:
        """Return the configured logger."""
        return self._logger

    @classmethod
    def from_env(cls, logger: logging.Logger | None = None) -> Client:
        """Create a client instance configured from environment variables.

        This factory method creates a fully configured client by reading
        configuration and authentication settings from environment variables.
        It's the recommended way to create clients in most applications.

        Args:
            logger: Optional Logger object for configuring logging.

        Returns:
            A fully configured Client instance with authentication provider
            automatically set based on environment variables.

        Raises:
            ClientEnvConfigError: If required environment variables are missing.

        Examples:
            >>> my_client = Client.from_env()  # Uses CMEM_BASE_URI, OAUTH_* vars
            >>> store_info = my_client.store.self_information
        """
        logger_instance = logger or logging.getLogger(__name__)
        config = Config.from_env()
        client = cls(config=config, logger=logger_instance)
        client.auth = AuthProvider.from_env(config=config)
        logger_instance.info("Initialized Client from environment")
        return client

    @classmethod
    def from_cmempy(cls, logger: logging.Logger | None = None) -> Client:
        """Create a client instance configured from a cmempy environment."""
        logger_instance = logger or logging.getLogger(__name__)
        config = Config.from_cmempy()
        client = Client(config=config, logger=logger_instance)
        client.auth = AuthProvider.from_cmempy(config=config)
        logger_instance.info("Initialized Client from cmempy")
        return client

    def configure_client_logger(
        self,
        level: str | int = "INFO",
        format_string: str | None = None,
        handlers: list[logging.Handler] | None = None,
        filename: str | Path | None = None,
    ) -> None:
        """Configure logging for the client's loggger and its decendants.

        Args:
            level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL) or int
            format_string: Custom log format string
            handlers: List of custom handlers (if provided, overrides filename)
            filename: Path to log file (creates FileHandler if provided)

        Examples:
            >>> Client.configure_client_logger(level="DEBUG")
            >>> Client.configure_client_logger(level="INFO", filename="cmem.log")
        """
        self.logger.setLevel(level)
        self.logger.handlers.clear()

        if format_string is None:
            # Default logging format
            format_string = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        formatter = logging.Formatter(format_string)

        if handlers is not None:
            for handler in handlers:
                if handler.formatter is None:
                    handler.setFormatter(formatter)
                self.logger.addHandler(handler)
        elif filename is not None:
            # Use RotatingFileHandler for production (https://fangpenlin.com/posts/2012/08/26/good-logging-practice-in-python/)
            file_handler = RotatingFileHandler(str(filename))
            file_handler.setFormatter(formatter)
            self.logger.addHandler(file_handler)
        else:
            # Default use console logging
            console_handler = logging.StreamHandler()
            console_handler.setFormatter(formatter)
            self.logger.addHandler(console_handler)

    def configure_logging_from_dict(self, config: dict[str, Any]) -> None:
        """Configure logging for the client.

        Args:
            config: Dictionary of logging configuration
        """
        validated_config = LoggingConfig(**config)
        dictConfig(validated_config.model_dump(by_alias=True, exclude_none=True))

    def configure_logging_from_json(self, json_config: Path) -> None:
        """Configure logging for the client via a json file.

        Args:
            json_config: Path to json configuration file
        """
        with Path.open(json_config, "r") as json_file:
            config_dict = json.load(json_file)
        self.configure_logging_from_dict(config_dict)

    def get_new_httpx_client(self) -> httpx.Client:
        """Create a new HTTP client instance with current configuration.

        Creates a fresh httpx.Client instance configured with the current
        headers, SSL verification settings, and timeout values from the
        client configuration.

        Returns:
            A new httpx.Client instance ready for making HTTP requests.

        Note:
            This method is called internally when the auth provider changes
            or when the HTTP client needs to be refreshed with new headers.
        """
        return httpx.Client(headers=self._headers, verify=self.config.verify, timeout=self.config.timeout)

    @property
    def http(self) -> httpx.Client:
        """Get the HTTP client instance for making API requests.

        Returns the configured HTTP client, creating it lazily on first access.
        The client is pre-configured with authentication headers, SSL settings,
        and timeout values.

        Returns:
            The httpx.Client instance configured for this client.

        Note:
            The HTTP client is automatically recreated when the authentication
            provider is changed to ensure headers are updated.
        """
        try:
            return self._http
        except AttributeError:
            self._http = self.get_new_httpx_client()
            return self._http

    @property
    def auth(self) -> AuthProvider:
        """Get the current authentication provider.

        Returns the authentication provider responsible for obtaining and
        refreshing access tokens for API requests.

        Returns:
            The currently configured AuthProvider instance.

        Raises:
            ClientNoAuthProviderError: If no authentication provider has been
                set on this client instance.

        Note:
            An authentication provider must be set before the client can make
            authenticated API requests. Use Client.from_env() for automatic
            configuration or set the auth property manually.
        """
        try:
            return self._auth
        except AttributeError as error:
            raise ClientNoAuthProviderError from error

    @auth.setter
    def auth(self, value: AuthProvider) -> None:
        """Set the authentication provider for this client.

        Setting a new authentication provider will immediately fetch an access
        token and update the HTTP client with the new authorization header.

        Args:
            value: The AuthProvider instance to use for authentication.

        Note:
            Setting a new auth provider will refresh the HTTP client to ensure
            the new authorization headers are applied to all future requests.
        """
        self.logger.debug("Setting a new auth provider for this client: '%s'", value.__class__.__name__)
        self._auth = value
        self._auth.logger = logging.getLogger(f"{self.logger.name}.{self._auth.__class__.__name__}")
        self._headers["Authorization"] = f"Bearer {self.auth.get_access_token()}"
        self._http = self.get_new_httpx_client()

    @property
    def workspace(self) -> BuildWorkspace:
        """Get the DataIntegration (build) workspace component.

        Returns the BuildWorkspace component for managing Corporate Memory's
        DataIntegration workspace, including projects, datasets, transformations,
        and workspace-level import/export operations.

        Returns:
            The BuildWorkspace component instance, created lazily on first access.

        Examples:
            >>> from pathlib import Path
            >>> client = Client.from_env()
            >>> client.workspace.import_from_zip(Path("backup.zip"))
            >>> client.workspace.export_to_zip(Path("new_backup.zip"))
        """
        try:
            return self._workspace
        except AttributeError:
            self._workspace = BuildWorkspace(client=self)
            return self._workspace

    @property
    def store(self) -> GraphStore:
        """Get the DataPlatform (explore) graph store component.

        Returns the GraphStore component for managing Corporate Memory's
        DataPlatform graph store, including RDF graph operations, bootstrap
        data management, and store-level backup/restore functionality.

        Returns:
            The GraphStore component instance, created lazily on first access.

        Examples:
            >>> client = Client.from_env()
            >>> store_info = client.store.self_information
            >>> print(f"Store type: {store_info.type}, version: {store_info.version}")
        """
        try:
            return self._store
        except AttributeError:
            self._store = GraphStore(client=self)
            return self._store

    @property
    def marketplace(self) -> Marketplace:
        """Get the DataPlatform (explore) marketplace component.

        Returns the Marketplace component.

        Returns:
            The Marketplace component instance, created lazily on first access.
        """
        try:
            return self._marketplace
        except AttributeError:
            self._marketplace = Marketplace(client=self)
            return self._marketplace

    @property
    def graphs(self) -> GraphsRepository:
        """Get the DataPlatform (explore) graph repository component.

        Returns the GraphsRepository component for managing Corporate Memory's
        DataPlatform graph repository for importing and exporting graph
        files and manages their integration with the graph store.

        Returns:
            The GraphRepository component instance, created lazily on first access.

        Examples:
            >>> from pathlib import Path
            >>> client = Client.from_env()
            >>> graphs = client.graphs
            >>> graphs.import_item(Path("backup.ttl"))
        """
        try:
            return self._graphs
        except AttributeError:
            self._graphs = GraphsRepository(client=self)
            return self._graphs

    @property
    def projects(self) -> ProjectsRepository:
        """Get the DataIntegration (build) project repository component.

        Returns the ProjectsRepository component to manage
        DataIntegration projects, such as importing and exporting project
        files.

        Returns:
            The ProjectsRepository component instance, created lazily on first access.

        Examples:
            >>> from pathlib import Path
            >>> client = Client.from_env()
            >>> projects = client.projects
            >>> projects.import_item(Path("project.zip"))
        """
        try:
            return self._projects
        except AttributeError:
            self._projects = ProjectsRepository(client=self)
            return self._projects

    @property
    def marketplace_packages(self) -> MarketplacePackagesRepository:
        """Get the package repository for managing Corporate Memory's marketplace packages

        Returns the package repository for managing Corporate Memory's
        marketplace packages. This component handles marketplace packages
        in a .zip format.

        Returns: The marketplace package repository instance, created lazily on first access.

        Examples:
            >>> from pathlib import Path
            >>> client = Client.from_env()
            >>> packages = client.marketplace_packages
            >>> packages.import_item(Path("marketplace_package.zip"))
        """
        try:
            return self._marketplace_packages
        except AttributeError:
            self._marketplace_packages = MarketplacePackagesRepository(client=self)
            return self._marketplace_packages

    @property
    def python_packages(self) -> PythonPackagesRepository:
        """Get the package repository for managing python packages

        Returns: The python package repository instance, created lazily on first access.
        """
        try:
            return self._python_packages
        except AttributeError:
            self._python_packages = PythonPackagesRepository(client=self)
            return self._python_packages

    @property
    def graph_imports(self) -> GraphImportsRepository:
        """Get the graph imports repository for managing graph imports

        Returns: The graph imports repository instance, created lazily on first access.
        """
        try:
            return self._graph_imports
        except AttributeError:
            self._graph_imports = GraphImportsRepository(client=self)
            return self._graph_imports

    @property
    def workflows(self) -> WorkflowsRepository:
        """Get the workflows repository for managing workflows

        Returns: The workflows repository instance, created lazily on first access.
        """
        try:
            return self._workflows
        except AttributeError:
            self._workflows = WorkflowsRepository(client=self)
            return self._workflows

    @property
    def files(self) -> FilesRepository:
        """Get the files repository for managing files

        Returns: The files repository instance, created lazy on first access.
        """
        try:
            return self._files
        except AttributeError:
            self._files = FilesRepository(client=self)
            return self._files
