"""A file resource model"""

from pydantic import Field

from cmem_client.models.base import Model, ReadRepositoryItem


class ResourceResponse(Model):
    """API response model for a file resource"""

    name: str = Field(description="Resource name")
    full_path: str = Field(description="Path of the resource", alias="fullPath")
    modified: str = Field(description="Resource last modified time")
    size: int = Field(description="Resource size")


class Resource(Model, ReadRepositoryItem):
    """A file resource."""

    file_id: str
    project_id: str

    def get_id(self) -> str:
        """Get the resource ID in format 'project_id:file_id'"""
        return f"{self.project_id}:{self.file_id}"
