"""Corporate Memory DataPlatform (explore) graph store management.

This module provides the GraphStore component for managing Corporate Memory's
DataPlatform graph store. The graph store is the primary repository for RDF
data and knowledge graphs, supporting semantic queries and exploration.

The GraphStore component provides high-level administrative operations including
bootstrap data management, full store backup and restoration, and system
information retrieval. These operations are essential for store maintenance,
deployment, and operational monitoring.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from cmem_client.logging_utils import log_method
from cmem_client.models.base import Model

if TYPE_CHECKING:
    from pathlib import Path

    from httpx import Response

    from cmem_client.client import Client

from cmem_client.components.sparql_wrapper import SPARQLWrapper


class StoreInformation(Model):
    """Information about the graph store instance and its capabilities.

    This model represents metadata about the DataPlatform graph store,
    including the store type and version information. This information
    is useful for compatibility checks, monitoring, and debugging.

    Attributes:
        type: The type of graph store (e.g., "GRAPHDB", "TENTRIS").
        version: The version string of the graph store implementation.
    """

    type: str
    """The type/implementation of the graph store (e.g., "GRAPHDB", "TENTRIS")."""

    version: str
    """The version string of the graph store implementation."""


class GraphStore:
    """High-level interface for Corporate Memory DataPlatform graph store operations.

    The GraphStore component provides administrative and operational methods for
    managing the Corporate Memory DataPlatform graph store. It handles store-level
    operations including bootstrap data management, full backup and restoration,
    and system information retrieval.

    This component abstracts the complexities of the DataPlatform API and provides
    a convenient interface for common graph store management tasks. It's designed
    for administrative operations rather than individual graph manipulation
    (use repositories for graph-level operations).

    Attributes:
        _client: The Corporate Memory client instance used for API communication.
        _sparql_wrapper: SPARQLWrapper instance for rdflib SPARQL queries.

    Administrative Operations:
        - Full store backup and restoration
        - Bootstrap data management (system vocabularies, etc.)

    See Also:
        For individual graph operations, use the repositories.graphs module
        which provides CRUD operations for specific RDF graphs.
    """

    _client: Client
    """The Corporate Memory client instance used for making API requests to the DataPlatform."""

    _sparql_wrapper: SPARQLWrapper
    """SPARQLWrapper instance for executing SPARQL queries with rdflib."""

    def __init__(self, client: Client) -> None:
        """Initialize a new GraphStore component instance.

        Creates a GraphStore component that uses the provided client for
        API communication with the DataPlatform graph store.

        Args:
            client: A configured Corporate Memory client instance with
                authentication and endpoint configuration.

        Note:
            This constructor is typically called automatically by the
            Client class when accessing the store property. Direct
            instantiation is rarely needed in normal usage.
        """
        self._client = client
        self.logger = logging.getLogger(f"{self._client.logger.name}.{self.__class__.__name__}")

    @log_method
    def import_bootstrap_data(self) -> None:
        """Import or update bootstrap data in the graph store.

        Bootstrap data includes system vocabularies, ontologies, and other
        foundational RDF data required for proper Corporate Memory operation.
        This operation ensures the store contains all necessary system-level
        graphs and vocabularies.

        Raises:
            HTTPError: If the bootstrap import request fails due to network
                issues or server errors.

        Note:
            This operation may take some time.
            It's typically performed during system initialization or when
            updating to new Corporate Memory versions that include new
            system vocabularies.

        Use Cases:
            - Initial system setup
            - System updates with new vocabularies
            - Recovery after bootstrap data corruption
        """
        path = "/api/admin/bootstrap"
        url = self._client.config.url_explore_api / path
        self._client.http.post(url=url, data={})

    def delete_bootstrap_data(self) -> None:
        """Delete bootstrap data from the graph store.

        Warning: This operation removes system vocabularies and foundational
        RDF data required for proper Corporate Memory operation. Use with extreme caution.

        Removes all bootstrap data including system vocabularies, ontologies,
        and other foundational RDF graphs. This is typically used for cleanup
        during testing, or system reset.

        Raises:
            HTTPError: If the bootstrap deletion request fails due to network
                issues or server errors.

        Caution:
            After deleting bootstrap data, the Corporate Memory system may not
            function correctly until new bootstrap data is imported. This
            operation should typically be followed by import_bootstrap_data().

        Use Cases:
            - System reset during testing
            - Troubleshooting corrupted system vocabularies
            - Development environment reset
        """
        self.logger.info("Deleting bootstrap data from the graph store...")
        path = "/api/admin/bootstrap"
        url = self._client.config.url_explore_api / path
        self._client.http.delete(url=url)

    @log_method
    def export_to_zip(self, path: Path) -> None:
        """Export a complete backup of the graph store as a ZIP archive.

        Creates a full backup of the entire Corporate Memory DataPlatform graph store,
        including all RDF graphs, system vocabularies, and metadata. The backup is
        streamed directly to the specified file path as a compressed ZIP archive.

        This operation creates a point-in-time snapshot that can be used for:
        - Disaster recovery and backup strategies
        - Environment migration and cloning
        - System maintenance and testing
        - Data archival and compliance requirements

        Args:
            path: The file system path where the ZIP backup archive will be saved.
                The path should include the .zip extension and the parent directory
                must exist and be writable.

        Raises:
            HTTPError: If the backup request fails due to network issues, server
                errors, or insufficient permissions.
            OSError: If the specified path cannot be written to due to file system
                permissions or disk space issues.

        Performance Notes:
            - The backup is streamed directly to disk to minimize memory usage
            - Large stores may take significant time to back up completely
            - Network bandwidth and storage I/O will impact backup duration
            - The operation blocks until the entire backup is complete

        Security Considerations:
            - Backup files contain all graph data and should be stored securely
            - Consider encryption for sensitive data in backup archives
            - Ensure appropriate access controls on backup storage locations
            - Backup files may contain authentication tokens or sensitive metadata

        See Also:
            Use import_from_zip() to restore from backup archives created by this method.
        """
        response: Response
        url = self._client.config.url_explore_api / "/api/admin/backup/zip"
        with self._client.http.stream("GET", url=url) as response, path.open("wb") as file:
            for data in response.iter_bytes():
                file.write(data)

    @log_method
    def import_from_zip(self, path: Path) -> None:
        """Import and restore a complete graph store backup from a ZIP archive.

        Warning: This operation replaces ALL existing data in the graph store.
        All current graphs, vocabularies, and metadata will be permanently deleted
        and replaced with the contents of the backup archive.

        Restores a Corporate Memory DataPlatform graph store from a ZIP backup
        archive created by export_to_zip(). The restoration process completely
        replaces the current store contents with the archived data, effectively
        rolling back the store to the state captured in the backup.

        Args:
            path: The file system path to the ZIP backup archive to import.
                The file must be a valid backup archive created by export_to_zip()
                or compatible with the Corporate Memory backup format.

        Raises:
            HTTPError: If the restore request fails due to network issues, server
                errors, insufficient permissions, or invalid backup format.
            OSError: If the specified backup file cannot be read due to file system
                permissions or if the file does not exist.
            ValidationError: If the backup archive format is invalid or corrupted.

        Important Warnings:
            - **Data Loss**: All existing graphs and data will be permanently deleted
            - **Downtime**: The store may be unavailable during the restoration process
            - **Irreversible**: This operation cannot be undone without another backup
            - **Compatibility**: Ensure backup compatibility with current store version

        Performance Notes:
            - Large backup archives may take significant time to restore
            - The store will be unavailable during the restoration process
            - Network bandwidth and storage I/O will impact restoration duration
            - Memory usage is optimized through streaming file upload

        Use Cases:
            - Disaster recovery from catastrophic data loss
            - Environment synchronization and cloning
            - Rolling back to known good state after issues
            - Migrating data between Corporate Memory instances
            - Testing and development environment setup

        See Also:
            Use export_to_zip() to create backup archives for import with this method.
        """
        url = self._client.config.url_explore_api / "/api/admin/restore/zip"
        files = {"file": ("backup.zip", path.open("rb"), "application/zip")}
        response = self._client.http.post(url=url, files=files)
        response.raise_for_status()

    @property
    def self_information(self) -> StoreInformation:
        """Get metadata and version information about the graph store instance.

        Retrieves information about the Corporate Memory DataPlatform
        graph store, including the store implementation type and version.

        The information is fetched from the store's actuator endpoint, which
        provides real-time metadata about the running graph store instance.

        Returns:
            StoreInformation: A model containing store type and version information.
                The returned object includes the store implementation name
                (e.g., "GRAPHDB", "TENTRIS") and its version string.

        Raises:
            HTTPError: If the information request fails due to network issues,
                server errors, or insufficient permissions to access actuator endpoints.
            ValidationError: If the response cannot be parsed as valid store
                information due to unexpected response format.

        Performance Notes:
            - This property makes a live HTTP request on each access
            - Consider caching the result if accessed frequently
            - The actuator endpoint is typically lightweight and fast-responding
            - Network latency will impact response time for this property

        Security Notes:
            - Actuator endpoints may reveal system information
            - Ensure appropriate access controls on actuator endpoints
            - Store version information should be treated as potentially sensitive
        """
        url = self._client.config.url_explore_api / "/actuator/info"
        content = self._client.http.get(url=url).json().get("store")
        return StoreInformation(**content)

    @property
    def sparql(self) -> SPARQLWrapper:
        """Get a SPARQLWrapper instance for rdflib-based SPARQL queries.

        Returns a SPARQLWrapper component configured with authentication
        for executing SPARQL queries using rdflib. The wrapper provides
        access to the Corporate Memory SPARQL endpoint with automatic
        authentication handling.

        Returns:
            The SPARQLWrapper component instance, created lazily on first access.

        Examples:
            >>> client = Client.from_env()
            >>> sparql_wrapper = client.store.sparql
            >>> # Use with rdflib operations
        """
        try:
            return self._sparql_wrapper
        except AttributeError:
            sparql_endpoint = str(self._client.config.url_explore_api / "/proxy/default/sparql")
            update_endpoint = str(self._client.config.url_explore_api / "/proxy/default/update")
            self._sparql_wrapper = SPARQLWrapper(
                sparql_endpoint=sparql_endpoint, update_endpoint=update_endpoint, client=self._client
            )
            return self._sparql_wrapper
