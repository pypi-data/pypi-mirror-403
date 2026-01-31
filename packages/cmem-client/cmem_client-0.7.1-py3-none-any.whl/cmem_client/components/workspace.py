"""Corporate Memory DataIntegration (build) workspace management.

This module provides the BuildWorkspace component for managing Corporate Memory's
DataIntegration workspace. The workspace contains projects, datasets, transformations,
and other integration artifacts organized in a hierarchical structure.

The BuildWorkspace component provides high-level operations for workspace backup
and restoration, allowing entire workspace snapshots to be exported and imported
as ZIP archives. This is essential for deployment, migration, and disaster recovery
scenarios.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from cmem_client.logging_utils import log_method

if TYPE_CHECKING:
    from pathlib import Path

    from httpx import Response

    from cmem_client.client import Client


class BuildWorkspace:
    """High-level interface for Corporate Memory DataIntegration workspace operations.

    The BuildWorkspace component provides administrative and operational methods for
    managing the Corporate Memory DataIntegration (build) workspace. It handles
    workspace-level operations including complete backup and restoration of all
    workspace contents as ZIP archives.

    The workspace contains all DataIntegration artifacts including:
    - Projects and their configurations
    - Datasets and data sources
    - Transformation workflows and mapping rules
    - Workflow definitions and scheduling configurations

    This component abstracts the complexities of the DataIntegration API and provides
    a convenient interface for workspace-wide administrative tasks.

    Attributes:
        _client: The Corporate Memory client instance used for API communication.

    Administrative Operations:
        - Complete workspace backup and restoration
        - Environment synchronization and migration
        - Disaster recovery and rollback capabilities
        - Deployment automation and CI/CD integration

    See Also:
        For individual project operations, use the repositories.projects module
        which provides CRUD operations for specific DataIntegration projects.
    """

    _client: Client
    """The Corporate Memory client instance used for making API requests to the DataIntegration API."""

    def __init__(self, client: Client) -> None:
        """Initialize a new BuildWorkspace component instance.

        Creates a BuildWorkspace component that uses the provided client for
        API communication with the DataIntegration workspace endpoints.

        Args:
            client: A configured Corporate Memory client instance with
                authentication and endpoint configuration.

        Note:
            This constructor is typically called automatically by the
            Client class when accessing the workspace property. Direct
            instantiation is rarely needed in normal usage.
        """
        self._client = client
        self.logger = logging.getLogger(f"{self._client.logger.name}.{self.__class__.__name__}")

    @log_method
    def import_from_zip(self, path: Path) -> Response:
        """Import and restore a complete workspace backup from a ZIP archive.

        Warning: This operation overwrites existing workspace content.
        All projects, datasets, transformations, and other workspace artifacts will be
        replaced or removed during the import process.

        Restores a Corporate Memory DataIntegration workspace from a ZIP backup
        archive created by export_to_zip(). The import process loads all workspace
        artifacts including projects, datasets, transformations, vocabularies,
        and configurations from the archive into the current workspace.

        Args:
            path: The file system path to the ZIP backup archive to import.
                The file must be a valid workspace backup archive created by
                export_to_zip() or compatible with the DataIntegration workspace format.

        Returns:
            Response: The HTTP response object from the import operation.
                Check response.status_code for success (200) and response.json()
                for detailed import results and any warnings or errors.

        Raises:
            HTTPError: If the import request fails due to network issues, server
                errors, insufficient permissions, or invalid archive format.
            OSError: If the specified backup file cannot be read due to file system
                permissions or if the file does not exist.

        Important Considerations:
            - **Data Validation**: Invalid configurations in the archive may cause failures
            - **Dependency Resolution**: Project dependencies must be satisfied after import

        Performance Notes:
            - Large workspace archives may take significant time to import
            - The workspace may be partially unavailable during import
            - Network bandwidth affects upload speed for large archives
            - Import processing time depends on workspace complexity

        Use Cases:
            - Environment synchronization between development and production
            - Workspace migration between Corporate Memory instances
            - Disaster recovery from workspace backups
            - Deployment automation and CI/CD pipeline integration
            - Team collaboration and workspace sharing

        See Also:
            Use export_to_zip() to create workspace archives for import with this method.
        """
        url = self._client.config.url_build_api / "/workspace/import/xmlZip"
        files = {"file": (path.name, path.open("rb"), "application/octet-stream")}
        response = self._client.http.post(url=url, files=files)
        response.raise_for_status()
        return response

    @log_method
    def export_to_zip(self, path: Path) -> None:
        """Export a complete backup of the workspace as a ZIP archive.

        Creates a comprehensive backup of the entire Corporate Memory DataIntegration
        workspace, including all projects, datasets, transformations, vocabularies,
        workflows, and configurations. The backup is streamed directly to the
        specified file path as a compressed ZIP archive.

        This operation creates a point-in-time snapshot of the complete workspace
        that can be used for:
        - Environment migration and synchronization
        - Disaster recovery and backup strategies
        - Development and testing environment setup
        - Deployment automation and CI/CD pipelines
        - Team collaboration and workspace sharing

        Args:
            path: The file system path where the ZIP workspace archive will be saved.
                The path should include the .zip extension and the parent directory
                must exist and be writable.

        Raises:
            HTTPError: If the export request fails due to network issues, server
                errors, or insufficient permissions.
            OSError: If the specified path cannot be written to due to file system
                permissions or disk space issues.

        Performance Notes:
            - The export is streamed directly to disk to minimize memory usage
            - Large workspaces may take significant time to export completely
            - Network bandwidth and storage I/O will impact export duration
            - The operation blocks until the entire workspace is exported
            - Export size depends on workspace complexity and resource files

        Security Considerations:
            - Workspace archives contain all project data and configurations
            - May include database connection strings and access credentials
            - Should be stored securely with appropriate access controls
            - Consider encryption for sensitive workspace data
            - Review archive contents before sharing or transferring

        Use Cases:
            - **Environment Promotion**: Move workspace from dev to production
            - **Disaster Recovery**: Regular backups for business continuity
            - **Team Onboarding**: Share workspace setups with new team members
            - **CI/CD Integration**: Automated workspace deployment pipelines
            - **Migration Support**: Transfer workspaces between instances
            - **Version Control**: Track workspace state changes over time

        See Also:
            Use import_from_zip() to restore workspace archives created by this method.
        """
        url = self._client.config.url_build_api / "/workspace/export/xmlZip"
        with (
            path.open("wb") as download_file,
            self._client.http.stream(method="GET", url=url) as response,
        ):
            for chunk in response.iter_bytes():
                download_file.write(chunk)
