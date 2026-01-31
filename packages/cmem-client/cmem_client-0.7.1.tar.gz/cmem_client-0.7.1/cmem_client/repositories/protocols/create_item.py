"""Protocol interface for repository item creation operations.

This module defines the CreateItemProtocol that repositories can implement
to provide item creation capabilities. It includes comprehensive error handling
for different API response formats and automatic repository refresh after
successful creation.

The protocol handles both DataIntegration (build) and DataPlatform (explore)
API error formats, providing consistent error reporting across different
Corporate Memory components.
"""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from http import HTTPStatus
from typing import TYPE_CHECKING, Protocol, TypeVar, runtime_checkable

from httpx import HTTPError, Response
from pydantic import ValidationError

from cmem_client.exceptions import RepositoryModificationError
from cmem_client.logging_utils import log_method
from cmem_client.models.base import Model
from cmem_client.models.error import ErrorResult, Problem
from cmem_client.repositories.base.abc import ItemType, RepositoryConfig

if TYPE_CHECKING:
    from cmem_client.client import Client


class CreateConfig(Model, ABC):
    """Abstract base class for repository item creation configurations."""


CreateItemConfig_contra = TypeVar("CreateItemConfig_contra", bound=CreateConfig, contravariant=True)


@runtime_checkable
class CreateItemProtocol(Protocol[ItemType, CreateItemConfig_contra]):
    """Protocol which allows for creation of new items"""

    _client: Client
    _dict: dict[str, ItemType]
    _config: RepositoryConfig
    _logger: logging.Logger

    @property
    def logger(self) -> logging.Logger:
        """Gets the client logger"""
        if not hasattr(self, "_logger"):
            self._logger = logging.getLogger(f"{self._client.logger.name}.{self.__class__.__name__}")
        return self._logger

    @abstractmethod
    def fetch_data(self) -> None:
        """Fetch new data and update the repository"""

    @log_method
    def create_item(
        self, item: ItemType, skip_if_existing: bool = False, configuration: CreateItemConfig_contra | None = None
    ) -> None:
        """Create (add) a new item to the repository

        Args:
            item (ItemType): The item to add to the repository
            skip_if_existing (bool, optional): If true, creating already existing items will be ignored
            configuration (CreateItemConfig_contra | None): Optional configuration

        Raises:
            RepositoryModificationError: if an error occurs while creating the item
            HTTPError: for any other http error
        """
        _ = configuration
        if item.get_id() in self._dict:
            if not skip_if_existing:
                raise RepositoryModificationError(f"Item with id {item.get_id()} already exists.")
            self.logger.info("Item '%s' already exists. Not creating new item.", item.get_id())
            return
        response = self._create_item(item)
        if isinstance(response, Response):
            self.raise_modification_error(response)
        self.fetch_data()

    def raise_modification_error(self, response: Response) -> None:
        """Raise an exception if needed"""
        if response.status_code == HTTPStatus.CREATED:
            return

        # some endpoint return OK instead of CREATED
        # - /api/python/installPackageByName
        if response.status_code == HTTPStatus.OK:
            return

        if self._config.component == "explore":
            try:
                problem = Problem.model_validate_json(response.content)
                raise RepositoryModificationError(problem.get_exception_message())
            except ValidationError as error:
                raise RepositoryModificationError(response.content) from error

        if self._config.component == "build":
            try:
                error_result = ErrorResult.model_validate_json(response.content)
                raise RepositoryModificationError(f"{error_result.title}: {error_result.detail}")
            except ValidationError as error:
                raise RepositoryModificationError(response.content) from error

        try:
            response.raise_for_status()
        except HTTPError as error:
            raise RepositoryModificationError(str(error)) from error

    @abstractmethod
    def _create_item(self, item: ItemType, configuration: CreateItemConfig_contra | None = None) -> Response | None:
        """Create (add) a new item to the repository (concrete implementation)

        Args:
            item (ItemType): The item to add to the repository
            configuration (CreateItemConfig_contra | None): Optional configuration

        Return:
            Response: The response from the update request
        """
