"""Repository implementation for paginated API endpoints.

This module provides PagedListRepository, a repository implementation that
handles paginated API responses commonly used in Corporate Memory's DataPlatform
(explore) APIs. It automatically fetches all pages of results and provides
a unified dictionary-like interface.

The PagedListRepository is typically used for endpoints that return results
in a paginated format with metadata about page size, number, and totals.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Generic

from pydantic import Field

from cmem_client.logging_utils import log_method
from cmem_client.models.base import Model
from cmem_client.repositories.base.abc import ItemType, Repository, RepositoryConfig

if TYPE_CHECKING:
    from cmem_client.client import Client


class PageDescription(Model):
    """A description of a paged list.

    {"size":10,"number":0,"totalElements":0,"totalPages":0}
    """

    size: int
    number: int
    total_elements: int = Field(alias="totalElements")
    total_pages: int = Field(alias="totalPages")


class PagedListRepository(Repository, Generic[ItemType]):
    """Repository that uses a paged list endpoint."""

    _dict: dict[str, ItemType]
    _client: Client
    _config: RepositoryConfig

    @log_method
    def fetch_data(self) -> None:
        """Fetch a paged list from a JSON endpoint via a type adapter.

        Use this method to fetch data if your result set is a pageable spring endpoint.
        """
        items = {}
        page = 0
        while True:
            response = self._client.http.get(self._url_fetch_data, params={"page": page})
            response.raise_for_status()
            content = response.content.decode(encoding="utf-8")
            result_set = self._config.fetch_data_adapter.validate_json(content)
            for item in result_set.content:
                items[item.get_id()] = item
            if len(result_set.content) < result_set.page.size:
                break
            page += 1
        self._dict = items
