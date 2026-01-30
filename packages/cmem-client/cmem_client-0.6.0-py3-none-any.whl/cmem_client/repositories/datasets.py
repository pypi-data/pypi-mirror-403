"""Repository for managing Corporate Memory datasets within projects.

This module provides the DatasetRepository class for managing datasets in
Corporate Memory's DataIntegration (build) environment. Datasets represent
data sources and sinks used in integration workflows, configured through
various plugins.
"""

from __future__ import annotations

from pydantic import TypeAdapter

from cmem_client.models.dataset import Dataset, DatasetSearchResultSet
from cmem_client.repositories.base.task_search import (
    TaskSearchRepository,
    TaskSearchRepositoryConfig,
)
from cmem_client.repositories.protocols.delete_item import DeleteConfig, DeleteItemProtocol


class DatasetDeleteConfig(DeleteConfig):
    """Dataset deletion configuration."""


class DatasetsRepository(TaskSearchRepository, DeleteItemProtocol):
    """Repository for datasets."""

    _dict: dict[str, Dataset]
    _config = TaskSearchRepositoryConfig(fetch_data_adapter=TypeAdapter(DatasetSearchResultSet), item_type="dataset")

    def _delete_item(self, key: str, configuration: DatasetDeleteConfig | None = None) -> None:
        _ = configuration
        to_delete: Dataset = self._dict[key]
        url = self._url(f"/workspace/projects/{to_delete.project_id}/datasets/{to_delete.id}")
        response = self._client.http.delete(url)
        response.raise_for_status()
