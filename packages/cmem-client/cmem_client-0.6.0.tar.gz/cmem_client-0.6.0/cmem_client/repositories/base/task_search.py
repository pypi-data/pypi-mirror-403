"""Repository implementation for Corporate Memory task search endpoints.

This module provides TaskSearchRepository, a specialized repository that uses
Corporate Memory's DataIntegration task search API to find and retrieve items.
The search functionality allows for flexible querying with filters, facets,
and text search capabilities.
"""

from __future__ import annotations

import json
from typing import TYPE_CHECKING, Generic, Literal

from cmem_client.repositories.base.abc import ItemType, Repository, RepositoryConfig

if TYPE_CHECKING:
    from pydantic import TypeAdapter

    from cmem_client.client import Client


class TaskSearchRepositoryConfig(RepositoryConfig):
    """Configuration class for a Task Search read repository"""

    component: Literal["build", "explore"]
    fetch_data_path: str
    fetch_data_adapter: TypeAdapter
    item_type: str

    def __init__(
        self,
        fetch_data_adapter: TypeAdapter,
        item_type: str,
        component: Literal["build", "explore"] = "build",
        fetch_data_path: str = "/api/workspace/searchItems",
    ) -> None:
        self.item_type = item_type
        super().__init__(component, fetch_data_path, fetch_data_adapter)


class TaskSearchRepository(Repository, Generic[ItemType]):
    """Subclass of a ReadRepository that uses the task search endpoint."""

    _dict: dict[str, ItemType]
    _client: Client
    _config: TaskSearchRepositoryConfig

    def fetch_data(self) -> None:
        """Fetch a list from the DI task search endpoint via a type adapter."""
        search_config = {
            "limit": 1000000,
            "offset": 0,
            "itemType": self._config.item_type,
            "project": None,
            "textQuery": "",
            "facets": None,
            "addTaskParameters": True,
        }
        response = self._client.http.post(
            self._url_fetch_data,
            content=json.dumps(search_config),
            headers={"Content-Type": "application/json"},
        )
        response.raise_for_status()
        content = response.content.decode(encoding="utf-8")
        items = {}
        result_set = self._config.fetch_data_adapter.validate_json(content)
        for item in result_set.results:
            items[item.get_id()] = item
        self._dict = items
