"""Python package models."""

from eccenca_marketplace_client.fields import PyPiIdentifier
from pydantic import ConfigDict

from cmem_client.models.base import ReadRepositoryItem


class PythonPackage(ReadRepositoryItem):
    """Installed python package.

    Represents a python package installed in Corporate Memory
    """

    name: PyPiIdentifier
    version: str | None = None

    model_config = ConfigDict(arbitrary_types_allowed=True, str_strip_whitespace=True, extra="forbid")

    def get_id(self) -> str:
        """Get the package identifier.

        Returns:
            The python pypi name which uniquely identifies this package.
        """
        return str(self.name)
