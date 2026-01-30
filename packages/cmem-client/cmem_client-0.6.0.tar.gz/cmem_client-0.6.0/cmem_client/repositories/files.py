"""Files Repository."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, ClassVar

from httpx import HTTPError
from pydantic import TypeAdapter

from cmem_client.repositories.protocols.export_item import ExportConfig, ExportItemProtocol

if TYPE_CHECKING:
    from collections.abc import Sequence

    from cmem_client.client import Client

from cmem_client.exceptions import FilesDeleteError, FilesExportError, FilesImportError
from cmem_client.models.item import FileImportItem, ImportItem
from cmem_client.models.resource import Resource, ResourceResponse
from cmem_client.repositories.base.plain_list import PlainListRepository
from cmem_client.repositories.protocols.delete_item import DeleteConfig, DeleteItemProtocol
from cmem_client.repositories.protocols.import_item import ImportConfig, ImportItemProtocol


class FilesImportConfig(ImportConfig):
    """Files Import Configuration."""


class FilesExportConfig(ExportConfig):
    """Files Export Configuration."""


class FilesDeleteConfig(DeleteConfig):
    """Files Delete Configuration."""


class FilesRepository(PlainListRepository, ImportItemProtocol, DeleteItemProtocol, ExportItemProtocol):
    """Repository for files"""

    _client: Client
    _dict: dict[str, Resource]
    _allowed_import_items: ClassVar[Sequence[type[ImportItem]]] = [FileImportItem]

    def fetch_data(self) -> None:
        """Fetch all file resources from all projects."""
        self._dict = {}
        for project_id in self._client.projects:
            for resource_data in self._get_resources(project_id):
                resource = Resource(file_id=resource_data.full_path, project_id=project_id)
                self._dict[resource.get_id()] = resource

    def _get_resources(self, project_id: str) -> list[ResourceResponse]:
        """GET retrieve list of resources."""
        url = self._client.config.url_build_api / "workspace/projects" / project_id / "resources"
        response = self._client.http.get(url=url)
        response.raise_for_status()
        adapter = TypeAdapter(list[ResourceResponse])
        return adapter.validate_json(response.content)

    def _import_item(
        self,
        path: Path | None = None,
        replace: bool = False,
        key: str | None = None,
        configuration: FilesImportConfig | None = None,
    ) -> str:
        """Import a file to a specific project.

        Args:
            path: Local file path to upload
            replace: Whether to replace existing file
            key: Composite key in format 'project_id:file_path'
            configuration: Import configuration

        Returns:
            Composite key in format 'project_id:file_path'
        """
        _ = configuration

        if path is None:
            raise FilesImportError("Path to file necessary.")

        if key is None:
            raise FilesImportError("Key in format 'project_id:file_path' is required.")

        if ":" not in key:
            raise FilesImportError(f"Invalid key format. Expected 'project_id:file_path', got '{key}'")

        project_id, resource_name = key.split(":", 1)

        if not replace and key in self._dict:
            raise FilesImportError(f"File {key} already exists. Try replace.")

        url = self._client.config.url_build_api / "workspace/projects" / project_id / "files"

        with path.open("rb") as file:
            try:
                response = self._client.http.put(url, params={"path": resource_name}, content=file)
                response.raise_for_status()
            except HTTPError as e:
                raise FilesImportError(f"Could not upload file '{resource_name}' to project '{project_id}'.") from e

        self.fetch_data()
        return key

    def _delete_item(self, key: str, configuration: FilesDeleteConfig | None = None) -> None:
        """Delete a file.

        Args:
            key: Composite key in format 'project_id:file_path'
            configuration: Delete configuration
        """
        _ = configuration

        if ":" not in key:
            raise FilesDeleteError(f"Invalid key format. Expected 'project_id:file_path', got '{key}'")

        project_id, file_path = key.split(":", 1)

        url = self._client.config.url_build_api / "workspace/projects" / project_id / "files"
        try:
            response = self._client.http.delete(url=url, params={"path": file_path})
            response.raise_for_status()
        except HTTPError as e:
            raise FilesDeleteError(f"Could not delete file '{file_path}' from project '{project_id}'.") from e

    def _export_item(
        self,
        key: str,
        path: Path | None,
        replace: bool = False,
        configuration: FilesExportConfig | None = None,
    ) -> Path:
        """Export a file from a specific project.

        Args:
            key: Composite key in format 'project_id:file_path'
            path: Target export path
            replace: Whether to replace existing file
            configuration: Export configuration
        """
        _ = configuration

        if key is None:
            raise FilesExportError("No resource key specified.")

        if ":" not in key:
            raise FilesExportError(f"Invalid key format. Expected 'project_id:file_path', got '{key}'")

        project_id, file_path = key.split(":", 1)

        if path is None:
            target_path = Path(file_path)
        elif path.is_dir():
            target_path = path / file_path
        else:
            target_path = path

        if target_path.exists() and not replace:
            raise FilesExportError(f"File '{target_path}' already exists. Try replace=True.")

        url = self._client.config.url_build_api / "workspace/projects" / project_id / "files"

        try:
            with self._client.http.stream(
                "GET",
                url,
                params={"path": file_path},
            ) as response:
                response.raise_for_status()

                target_path.parent.mkdir(parents=True, exist_ok=True)
                with target_path.open("wb") as file:
                    for chunk in response.iter_bytes():
                        file.write(chunk)

        except HTTPError as e:
            raise FilesExportError(f"Could not export file '{file_path}' from project '{project_id}'.") from e

        return target_path
