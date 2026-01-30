"""Repository for managing Python packages"""

from __future__ import annotations

from typing import TYPE_CHECKING

from pydantic import TypeAdapter

from cmem_client.models.python_package import PythonPackage
from cmem_client.repositories.base.abc import RepositoryConfig
from cmem_client.repositories.base.plain_list import PlainListRepository
from cmem_client.repositories.protocols.create_item import CreateConfig, CreateItemProtocol
from cmem_client.repositories.protocols.delete_item import DeleteConfig, DeleteItemProtocol

if TYPE_CHECKING:
    from httpx import Response


class PythonPackagesCreateConfig(CreateConfig):
    """Python packages create config"""


class PythonPackagesDeleteConfig(DeleteConfig):
    """Python packages deletion configuration."""


class PythonPackagesRepository(PlainListRepository, DeleteItemProtocol, CreateItemProtocol):
    """Repository for python packages"""

    _dict: dict[str, PythonPackage]
    _config = RepositoryConfig(
        component="build",
        fetch_data_path="/api/python/listPackages",
        fetch_data_adapter=TypeAdapter(list[PythonPackage]),
    )

    def _create_item(self, item: PythonPackage, configuration: PythonPackagesCreateConfig | None = None) -> Response:
        """Install a Python package."""
        _ = configuration
        url = self._url("/api/python/installPackageByName")
        return self._client.http.post(url, params={"name": item.name})

    def _delete_item(self, key: str, configuration: PythonPackagesDeleteConfig | None = None) -> None:
        """Delete item from repository."""
        _ = configuration
        url = self._url("/api/python/uninstallPackage")
        response = self._client.http.post(url, params={"name": key})
        response.raise_for_status()

    def delete_all(self) -> None:
        """Delete all items from the repository

        This overwrites the default protocol method and utilizes an internal behaviour of the server
        to wipe the whole python environment.
        """
        self._delete_item("--all")
        if hasattr(self, "fetch_data"):
            self.fetch_data()
