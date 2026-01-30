"""Corporate Memory dataset models for data integration.

This module defines models for representing datasets within Corporate Memory
projects. Datasets are data sources or sinks used in data integration workflows,
connecting to various external systems through plugins.

The Dataset model represents the configuration and metadata of datasets within
the DataIntegration environment, including their association with projects
and the plugins that handle their data access.
"""

from pydantic import Field

from cmem_client.models.base import Model, ReadRepositoryItem


class Dataset(ReadRepositoryItem):
    """A Dataset Description (Build)"""

    id: str
    project_id: str = Field(alias="projectId")
    plugin_id: str = Field(alias="pluginId")

    def get_id(self) -> str:
        """Get the ID of the dataset"""
        return f"{self.project_id}:{self.id}"


class DatasetSearchResultSet(Model):
    """A dataset search result set"""

    results: list[Dataset]
