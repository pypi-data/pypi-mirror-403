"""Repository implementation for simple list API endpoints.

This module provides PlainListRepository, a repository implementation for
API endpoints that return a simple array of objects without pagination.
It's commonly used with Corporate Memory's DataIntegration (build) APIs
that provide straightforward list responses.

The PlainListRepository fetches the entire list in a single request and
provides dictionary-like access to the items by their ID.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Generic

from cmem_client.logging_utils import log_method
from cmem_client.repositories.base.abc import ItemType, Repository, RepositoryConfig

if TYPE_CHECKING:
    from cmem_client.client import Client


class PlainListRepository(Repository, Generic[ItemType]):
    """Subclass of a ReadRepository that uses a plain list endpoint."""

    _dict: dict[str, ItemType]
    _client: Client
    _config: RepositoryConfig

    @log_method
    def fetch_data(self) -> None:
        """Fetch simple list from a JSON endpoint via a type adapter

        Use this method to fetch data when your result set is an array of objects.
        """
        response = self._client.http.get(self._url_fetch_data)
        response.raise_for_status()
        content = response.content.decode(encoding="utf-8")
        self._dict = {item.get_id(): item for item in self._config.fetch_data_adapter.validate_json(content)}
