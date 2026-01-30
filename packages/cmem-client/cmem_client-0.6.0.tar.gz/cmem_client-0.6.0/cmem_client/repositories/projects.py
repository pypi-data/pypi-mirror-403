"""Repository for managing Corporate Memory Build (DataIntegration) projects.

Provides ProjectRepository class with CRUD operations including create, delete, and import
functionality for projects from ZIP archives.
"""

from __future__ import annotations

import shutil
import tempfile
from io import BytesIO
from pathlib import Path
from shutil import rmtree
from typing import TYPE_CHECKING, ClassVar, Literal
from zipfile import ZipFile

from pydantic import Field, TypeAdapter

from cmem_client.exceptions import ProjectExportError, ProjectImportError, RepositoryModificationError
from cmem_client.models.base import Model
from cmem_client.models.item import ImportItem, ZipImportItem
from cmem_client.models.project import Project
from cmem_client.repositories.base.abc import RepositoryConfig
from cmem_client.repositories.base.plain_list import PlainListRepository
from cmem_client.repositories.protocols.create_item import CreateConfig, CreateItemProtocol
from cmem_client.repositories.protocols.delete_item import DeleteConfig, DeleteItemProtocol
from cmem_client.repositories.protocols.export_item import ExportConfig, ExportItemProtocol
from cmem_client.repositories.protocols.import_item import ImportConfig, ImportItemProtocol

if TYPE_CHECKING:
    from httpx import Response


class ProjectImportStatus(Model):
    """Response of the project import status endpoint."""

    project_id: str = Field(alias="projectId")
    success: bool | None = None
    failure_message: str | None = Field(alias="failureMessage", default=None)


class ProjectsImportConfig(ImportConfig):
    """Dataset Import Configuration."""

    use_archive_handler: bool = False


class ProjectsExportConfig(ExportConfig):
    """Dataset Export Configuration."""

    marshalling_plugin: Literal["xmlZip", "xmlZipWithoutResources"] = "xmlZip"
    extract_project_zip: bool = False


class ProjectsCreateConfig(CreateConfig):
    """Dataset Create Configuration."""


class ProjectsDeleteConfig(DeleteConfig):
    """Dataset Delete Configuration."""


class ProjectsRepository(
    PlainListRepository, DeleteItemProtocol, CreateItemProtocol, ImportItemProtocol, ExportItemProtocol
):
    """Repository for Build (DataIntegration) projects.

    This repository manages Build (DataIntegration) projects which are described with
    the [Project model][cmem_client.models.project.Project].
    """

    _dict: dict[str, Project]
    _allowed_import_items: ClassVar[list[type[ImportItem]]] = [ZipImportItem]
    _allowed_marshalling_plugins: ClassVar[list[str]] = ["xmlZip", "xmlZipWithoutResources"]
    _default_import_config: ProjectsImportConfig = ProjectsImportConfig()

    _config = RepositoryConfig(
        component="build",
        fetch_data_path="/workspace/projects",
        fetch_data_adapter=TypeAdapter(list[Project]),
    )

    def _delete_item(self, key: str, configuration: ProjectsDeleteConfig | None = None) -> None:
        """Delete an item."""
        _ = configuration
        url = self._url(f"/workspace/projects/{key}")
        response = self._client.http.delete(url)
        response.raise_for_status()

    def _create_item(self, item: Project, configuration: ProjectsCreateConfig | None = None) -> Response:
        """Create a new project

        Note: the payload of this request needs to have an 'id' field (different from model)
        """
        _ = configuration
        url = self._url("/api/workspace/projects")
        data = {"id": item.get_id(), "metaData": item.meta_data.model_dump()}
        return self._client.http.post(url, json=data)

    def _import_item_get_status(self, import_id: str) -> ProjectImportStatus:
        """Get the status of an import item process"""
        url = self._url(f"/api/workspace/projectImport/{import_id}/status")
        params = {"timeout": "1000"}
        response = self._client.http.get(url, params=params).raise_for_status()
        return ProjectImportStatus(**response.json())

    def _import_item(
        self,
        path: Path | None = Path(),
        replace: bool = False,
        key: str | None = None,
        configuration: ProjectsImportConfig | None = None,
    ) -> str:
        """Import project ZIP archive to the repository (concrete implementation)

        This method is responsible for importing the item from the server.
        It needs to return the key of the imported item.
        """
        if path is None:
            raise ProjectImportError("Path must be specified.")

        if configuration is None:
            configuration = ProjectsImportConfig()

        # use a temporary zip file always to ensure zip and directory functionality
        with tempfile.NamedTemporaryFile(suffix=".zip" if path.is_dir() else path.suffix, delete=False) as tmp:
            if path.is_dir():
                shutil.make_archive(
                    tmp.name.removesuffix(".zip"),
                    "zip",
                    base_dir=path.name,
                    root_dir=str(path.parent.absolute()),
                )
                uploaded_file = Path(tmp.name)
            else:
                shutil.copyfile(path, tmp.name)
                uploaded_file = Path(tmp.name)

        # 1. the project file upload
        upload_url = self._url("/api/workspace/projectImport")
        with uploaded_file.open(mode="rb") as file:
            upload_response = self._client.http.post(upload_url, files={"file": file}).raise_for_status()
            project_import_id = upload_response.json()["projectImportId"]

        # unlink the temporary file again
        Path.unlink(Path(uploaded_file))

        # 2. the validation of the uploaded file
        validation_url = self._url(f"/api/workspace/projectImport/{project_import_id}")
        # projectId, label, marshallerId, projectAlreadyExists
        self._client.http.get(validation_url).raise_for_status()

        # 3. the asynchronous execution of the project import
        import_url = self._url(f"/api/workspace/projectImport/{project_import_id}")
        params = {
            "overwriteExisting": "true" if replace else "false",
            "generateNewId": "true" if not key else "false",
            "newProjectId": key if key else None,
        }
        self._client.http.post(import_url, params=params).raise_for_status()

        # 4. wait until finished
        import_status = self._import_item_get_status(import_id=project_import_id)
        while not import_status.success:
            import_status = self._import_item_get_status(import_id=project_import_id)
        if import_status.success:
            self.fetch_data()
            return import_status.project_id
        raise RepositoryModificationError(import_status.failure_message)

    def _export_item(
        self, key: str, path: Path | None, replace: bool = False, configuration: ProjectsExportConfig | None = None
    ) -> Path:
        """Export a project to a specified file path

        Args:
            key: The key of the project to export
            path: The path to which the project gets exported to
            replace: If True, replace the existing project with a new one.
            configuration: Optional configuration for export

        Returns:
            Path to the exported file
        """
        if path is None:
            raise ProjectExportError("Path must be specified.")

        if configuration is None:
            configuration = ProjectsExportConfig()

        if configuration.marshalling_plugin not in self._allowed_marshalling_plugins:
            raise ProjectExportError(f"Invalid marshalling plugin '{configuration.marshalling_plugin}'")

        url = self._url(f"/workspace/projects/{key}/export/{configuration.marshalling_plugin}")
        extracted_project = self._client.http.get(url).raise_for_status()

        if not extracted_project.content:
            raise ProjectExportError(f"Export returned empty content for project '{key}'")

        if configuration.extract_project_zip:
            if path.exists() and not replace:
                raise ProjectExportError(f"Directory '{path}' already exists. Use replace=True to overwrite.")
            if path.exists():
                rmtree(path)
            path.mkdir(parents=True)
            with ZipFile(BytesIO(extracted_project.content), "r") as zip_file:
                zip_file.extractall(path)
        else:
            if path.exists() and not replace:
                raise ProjectExportError(f"File '{path}' already exists. Use replace=True to overwrite.")
            with path.open(mode="wb") as file:
                file.write(extracted_project.content)

        return path
