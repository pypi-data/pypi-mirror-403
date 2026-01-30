"""Corporate Memory project models and metadata.

This module defines models for representing Corporate Memory DataIntegration
projects, including their metadata such as labels, descriptions, and tags.

Projects are the primary organizational unit in Corporate Memory's build
environment, containing datasets, transformations, and other integration
components. The Project model provides validation and serialization for
project data exchanged with the DataIntegration API.
"""

from typing import Any

from pydantic import Field

from cmem_client.models.base import Model, ReadRepositoryItem


class ProjectMetaData(Model):
    """Project Meta Data"""

    label: str | None = None
    description: str | None = None
    tags: list[str] | None = None


def default_metadata() -> ProjectMetaData:
    """Get the current UTC datetime"""
    # empty string is not allowed by DI, so model_post_init will change this to the ID
    return ProjectMetaData(label="")


class Project(ReadRepositoryItem):
    """A Build (DataIntegration) Project"""

    name: str
    meta_data: ProjectMetaData = Field(alias="metaData", default_factory=default_metadata)

    def model_post_init(self, context: Any, /) -> None:  # noqa: ANN401, ARG002
        """Set the label to the name if needed"""
        if self.meta_data.label == "":
            self.meta_data.label = self.name

    def get_id(self) -> str:
        """Get the ID of the project"""
        return self.name
