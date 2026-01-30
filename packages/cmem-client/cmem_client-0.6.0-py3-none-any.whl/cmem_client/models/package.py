"""Marketplace package models."""

from eccenca_marketplace_client.package_version import PackageVersion
from pydantic import ConfigDict

from cmem_client.models.base import Model, ReadRepositoryItem


class PackageMetadata(Model):
    """Package metadata."""

    name: str
    description: str
    comment: str | None = None


class Package(ReadRepositoryItem):
    """Installed marketplace package.

    Represents a package installed in Corporate Memory with all its
    metadata, file specifications, and version information as stored
    in the marketplace catalog graph.
    """

    package_version: PackageVersion

    model_config = ConfigDict(arbitrary_types_allowed=True, str_strip_whitespace=True, extra="forbid")

    def get_id(self) -> str:
        """Get the package identifier.

        Returns:
            The package_id which uniquely identifies this package.
        """
        return str(self.package_version.manifest.package_id)
