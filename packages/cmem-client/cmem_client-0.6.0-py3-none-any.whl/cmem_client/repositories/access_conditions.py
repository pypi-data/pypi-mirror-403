"""Repository for managing access conditions in Corporate Memory.

Provides AccessConditionRepository class for managing authorization access conditions
with CRUD operations including create and delete functionality.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from pydantic import TypeAdapter

from cmem_client.models.access_condition import AccessCondition, AccessConditionResultSet
from cmem_client.repositories.base.abc import RepositoryConfig
from cmem_client.repositories.base.paged_list import PagedListRepository
from cmem_client.repositories.protocols.create_item import CreateConfig, CreateItemProtocol
from cmem_client.repositories.protocols.delete_item import DeleteConfig, DeleteItemProtocol

if TYPE_CHECKING:
    from httpx import Response

    from cmem_client.client import Client


class AccessConditionsCreateConfig(CreateConfig):
    """Access condition creation config."""


class AccessConditionsDeleteConfig(DeleteConfig):
    """Access conditions delete config."""


class AccessConditionsRepository(PagedListRepository, DeleteItemProtocol, CreateItemProtocol):
    """Repository for managing authorization access conditions.

    This repository manages access conditions that control authorization for resources
    in Corporate Memory. Access conditions are described with the
    [AccessCondition model][cmem_client.models.access_condition.AccessCondition].

    The repository extends PagedListRepository and implements protocols for creating
    and deleting access conditions.
    """

    _dict: dict[str, AccessCondition]
    _client: Client
    _config = RepositoryConfig(
        component="explore",
        fetch_data_path="/api/authorization",  # used for all requests, not just fetch
        fetch_data_adapter=TypeAdapter(AccessConditionResultSet),
    )

    def _delete_item(self, key: str, configuration: AccessConditionsDeleteConfig | None = None) -> None:
        _ = configuration
        response = self._client.http.delete(url=self._url_fetch_data, params={"resource": key})
        response.raise_for_status()

    def _create_item(
        self, item: AccessCondition, configuration: AccessConditionsCreateConfig | None = None
    ) -> Response:
        # Send a CreateAccessConditionRequest instead of an AccessCondition
        _ = configuration
        return self._client.http.post(url=self._url_fetch_data, json=item.get_create_request())
