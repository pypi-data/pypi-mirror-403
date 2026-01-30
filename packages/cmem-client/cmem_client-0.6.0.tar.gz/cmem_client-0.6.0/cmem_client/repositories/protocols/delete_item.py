"""Protocol interface for repository item deletion operations.

This module defines the DeleteItemProtocol that repositories can implement
to provide item deletion capabilities. It includes validation to ensure items
exist before deletion and provides both individual and bulk deletion methods.

The protocol implements the Python __delitem__ method to support standard
dictionary-style deletion syntax while providing comprehensive error handling
for HTTP communication failures.
"""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Protocol, TypeVar, runtime_checkable

from httpx import HTTPError

from cmem_client.exceptions import RepositoryModificationError
from cmem_client.logging_utils import log_method
from cmem_client.models.base import Model
from cmem_client.repositories.base.abc import ItemType

if TYPE_CHECKING:
    from cmem_client.client import Client


class DeleteConfig(Model, ABC):
    """Abstract base class for repository item deletion configurations."""


DeleteItemConfig_contra = TypeVar("DeleteItemConfig_contra", bound=DeleteConfig, contravariant=True)


@runtime_checkable
class DeleteItemProtocol(Protocol[ItemType, DeleteItemConfig_contra]):
    """Protocol which allows for deletion of items"""

    _client: Client
    _dict: dict[str, ItemType]
    _logger: logging.Logger

    @property
    def logger(self) -> logging.Logger:
        """Gets the client logger"""
        if not hasattr(self, "_logger"):
            self._logger = logging.getLogger(f"{self._client.logger.name}.{self.__class__.__name__}")
        return self._logger

    def __delitem__(self, key: str) -> None:
        """Delete an item from the repository"""
        self.delete_item(key)

    @log_method
    def delete_item(
        self, key: str, skip_if_missing: bool = False, configuration: DeleteItemConfig_contra | None = None
    ) -> None:
        """Delete an item from the repository

        Args:
            key (str): The key of the item to delete
            skip_if_missing (bool, optional): If True, it is ignored if the deleted item even exists
            configuration (DeleteItemConfig, optional): Optional configuration for deletion

        Raises:
            RepositoryModificationError: if an error occurs while creating the item
            HTTPError: for any other http error
        """
        if key not in self._dict:
            if not skip_if_missing:
                raise RepositoryModificationError(f"Repository item '{key}' does not exists.")
            self.logger.info("Item '%s' does not exists, therefore not deleting.", key)
            return
        try:
            self._delete_item(key=key, configuration=configuration)
        except HTTPError as error:
            raise RepositoryModificationError(f"Error on deleting repository item '{key}'.") from error

        del self._dict[key]

    @abstractmethod
    def _delete_item(self, key: str, configuration: DeleteItemConfig_contra | None = None) -> None:
        """Delete an item from the repository (concrete implementation)

        This method is responsible for deleting the item from the server.
        """

    def delete_all(self) -> None:
        """Delete all items from the repository"""
        if hasattr(self, "fetch_data"):
            self.fetch_data()
        for key in list(self._dict):
            self.delete_item(key=key)
