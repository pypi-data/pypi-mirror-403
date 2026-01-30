"""Protocol interface for repository item import operations.

This module defines the ImportItemProtocol that repositories can implement
to support importing items from files. This is commonly used for importing
exported projects, graphs, or other resources into Corporate Memory.

The protocol supports both replacement of existing items and creation of new
items, with validation to ensure the import operation completes successfully
and the item is available in the repository after import.
"""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, ClassVar, Protocol, TypeVar, runtime_checkable

from httpx import HTTPError

from cmem_client.exceptions import RepositoryModificationError
from cmem_client.logging_utils import log_method
from cmem_client.models.base import Model
from cmem_client.models.item import FileImportItem, ImportItem, ZipImportItem, create_import_item
from cmem_client.repositories.base.abc import ItemType

if TYPE_CHECKING:
    from collections.abc import Sequence
    from pathlib import Path

    from cmem_client.client import Client


class ImportConfig(Model, ABC):
    """Abstract base class for Import Item Configuration Objects

    Attributes:
        use_archive_handler: When True, automatically uses ArchiveHandler to handle
            zip files, directories, and single files transparently. Defaults to True.
    """

    use_archive_handler: bool = True


ImportItemConfig_contra = TypeVar("ImportItemConfig_contra", bound=ImportConfig, contravariant=True)


@runtime_checkable
class ImportItemProtocol(Protocol[ItemType, ImportItemConfig_contra]):
    """Protocol which allows for importing of items from a file path.

    Repositories can optionally declare which ImportItem types they accept by setting:
        _allowed_import_items: ClassVar[Sequence[type[ImportItem]] | None]

    Example:
        _allowed_import_items: ClassVar[Sequence[type[ImportItem]]] = [FileImportItem, ZipImportItem]

    If not defined, defaults to [FileImportItem, ZipImportItem] (excludes DirectoryImportItem).

    Repositories can optionally declare default import configuration by setting:
        _default_import_config: ImportConfig | None = None

    Example:
        _default_import_config: ImportConfig | None = ProjectsImportConfig()

    This is needed for example if the use_archive_handler needs to be turned off.
    If not defined, defaults to None.
    """

    _client: Client
    _dict: dict[str, ItemType]
    _allowed_import_items: ClassVar[Sequence[type[ImportItem]]]
    _default_import_config: ImportConfig | None = None
    _logger: logging.Logger

    @property
    def logger(self) -> logging.Logger:
        """Gets the client logger"""
        if not hasattr(self, "_logger"):
            self._logger = logging.getLogger(f"{self._client.logger.name}.{self.__class__.__name__}")
        return self._logger

    @log_method
    def import_item(
        self,
        path: Path | None = None,
        replace: bool = False,
        key: str | None = None,
        configuration: ImportItemConfig_contra | None = None,
        skip_if_existing: bool = False,
    ) -> str:
        """Import an exported file to the repository

        By default, automatically handles zip files, directories, and single files
        using ImportItem model. Can be disabled by setting use_archive_handler=False
        in the configuration.
        """
        if key and key in self._dict and not replace:
            if not skip_if_existing:
                raise RepositoryModificationError(f"Repository item '{key}' already exists.")
            self.logger.info("Item '%s' already exists. Not importing new item.", key)
            return key
        try:
            if configuration is None:
                configuration = getattr(self, "_default_import_config", None)
            use_handler = configuration.use_archive_handler if configuration else True
            if use_handler and path:
                import_item = create_import_item(path)
                allowed_items = getattr(self, "_allowed_import_items", [FileImportItem, ZipImportItem])
                if allowed_items is not None and not isinstance(import_item, tuple(allowed_items)):
                    raise RepositoryModificationError(f"Import type '{type(import_item).__name__}' is not allowed.")
                with import_item as prepared_path:
                    new_key = self._import_item(
                        path=prepared_path, key=key, replace=replace, configuration=configuration
                    )
            else:
                new_key = self._import_item(path=path, key=key, replace=replace, configuration=configuration)
        except HTTPError as error:
            raise RepositoryModificationError(f"Error on importing path '{path}'.") from error
        if key and key != new_key:
            raise RepositoryModificationError(
                f"Repository import returned different item key than requested: '{key}' != `{new_key}`"
            )
        if key and key not in self._dict:
            raise RepositoryModificationError(f"Repository item '{key}' not there after import.")
        if key:
            return key
        return new_key

    @abstractmethod
    def _import_item(
        self,
        path: Path | None = None,
        replace: bool = False,
        key: str | None = None,
        configuration: ImportItemConfig_contra | None = None,
    ) -> str:
        """Import an item to the repository (concrete implementation)

        This method is responsible for importing the item to the server.
        It needs to return the key of the imported item.
        """
