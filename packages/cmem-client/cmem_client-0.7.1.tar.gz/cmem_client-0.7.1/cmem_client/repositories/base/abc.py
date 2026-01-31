"""Abstract base classes and configuration for CMEM repositories.

This module provides the foundational classes for building repositories in the CMEM client:

- RepositoryConfig: Configuration class that defines component type, fetch paths, and data adapters
- Repository: Abstract base class implementing a lazy-loading, read-only, dictionary-like interface
  for accessing CMEM resources with automatic data fetching and caching capabilities
"""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from collections.abc import ItemsView, Iterator, KeysView, Mapping, ValuesView
from typing import TYPE_CHECKING, Generic, Literal, TypeVar

from cmem_client.exceptions import RepositoryConfigError
from cmem_client.models.base import ReadRepositoryItem

if TYPE_CHECKING:
    from pydantic import TypeAdapter

    from cmem_client.client import Client
    from cmem_client.models.url import HttpUrl

ItemType = TypeVar("ItemType", bound=ReadRepositoryItem)
KeysViewType = KeysView[str]
ItemsViewType = ItemsView[str, ItemType]
ValuesViewType = ValuesView[ItemType]


class RepositoryConfig:
    """Configuration class for a read repository.

    This class defines the essential configuration parameters needed to set up
    a repository that can fetch data from CMEM components:

    - component: Specifies whether to use the "build" or "explore" API endpoint
    - fetch_data_path: The specific API path for retrieving repository data
    - fetch_data_adapter: Pydantic TypeAdapter for deserializing the API response
    """

    component: Literal["build", "explore"]
    fetch_data_path: str
    fetch_data_adapter: TypeAdapter

    def __init__(
        self,
        component: Literal["build", "explore"],
        fetch_data_path: str,
        fetch_data_adapter: TypeAdapter,
    ) -> None:
        self.component = component
        self.fetch_data_path = fetch_data_path
        self.fetch_data_adapter = fetch_data_adapter


class Repository(ABC, Mapping, Generic[ItemType]):
    """ABC of a lazy loading, read-only, dictionary-mimicking repository"""

    _dict: dict[str, ItemType]
    """the dict"""

    _client: Client
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

    def __init__(self, client: Client) -> None:
        self._client = client
        self.fetch_data()
        self._post_init()

    def _post_init(self) -> None:
        """Additional code to initialize the repository."""

    @property
    def _url_fetch_data(self) -> HttpUrl:
        """Get the endpoint url for fetching the repository data"""
        return self._url_base / self._config.fetch_data_path

    @property
    def _url_base(self) -> HttpUrl:
        """Get the base url for the repository"""
        match self._config.component:
            case "build":
                return self._client.config.url_build_api
            case "explore":
                return self._client.config.url_explore_api
            case _:
                raise RepositoryConfigError(f"Unknown component ID: {self._config.component}")

    def _url(self, path: str) -> HttpUrl:
        """Get the url for a path (based on the component)"""
        return self._url_base / path

    def __len__(self) -> int:
        """Get the number of items in the repository"""
        return len(self._dict)

    def __getitem__(self, key: str) -> ItemType:
        """Get an item by key (ID or IRI, depending on the type)"""
        return self._dict[key]

    def __iter__(self) -> Iterator[ItemType]:
        """Get the iterator over the items in the repository"""
        return iter(self._dict)  # type: ignore[arg-type]

    def __repr__(self) -> str:
        """Get a string representation of the repository"""
        return repr(self._dict)

    def __contains__(self, key: object) -> bool:
        """Check if an item is in the repository"""
        return key in self.keys()

    def keys(self) -> KeysViewType:
        """Get the keys of the repository"""
        return self._dict.keys()

    def values(self) -> ValuesViewType:
        """Get the values of the repository"""
        return self._dict.values()

    def items(self) -> ItemsViewType:
        """Get the items of the repository"""
        return self._dict.items()
