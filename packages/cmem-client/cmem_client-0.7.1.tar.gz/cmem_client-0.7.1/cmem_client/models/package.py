"""Marketplace package models."""

from datetime import UTC, datetime

from eccenca_marketplace_client.package_version import PackageVersion
from pydantic import BaseModel, ConfigDict, Field

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


class PackageInstallationMetadata(BaseModel):
    """Metadata about how and when a marketplace package was installed.

    This metadata is stored as JSON in the RDF graph and used to determine
    whether packages can be automatically removed when they are dependencies.
    """

    dependency_level: int = Field(
        ge=0, description="Dependency depth (0 for direct installs, >0 for dependencies", default=0
    )
    installed_at: datetime = Field(description="Timestamp when the package was installed", default=datetime.now(tz=UTC))

    @property
    def is_direct_installed(self) -> bool:
        """Indicates whether this package was installed directly"""
        return self.dependency_level == 0
