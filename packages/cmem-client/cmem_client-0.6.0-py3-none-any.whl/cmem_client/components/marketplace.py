"""eccenca Marketplace server integration.

This module provides the Marketplace component for interacting with the eccenca
Marketplace server. The component handles package downloads and version queries,
abstracting the marketplace REST API into a convenient Python interface.

The eccenca Marketplace is a central repository for distributing Corporate Memory
packages, including vocabularies, ontologies, and Python plugins. This component
enables automated package retrieval for installation and dependency resolution.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from httpx import HTTPError
from xdg_base_dirs import xdg_cache_home

from cmem_client.exceptions import MarketplaceReadError
from cmem_client.logging_utils import log_method
from cmem_client.models.url import HttpUrl

if TYPE_CHECKING:
    from pathlib import Path

    from eccenca_marketplace_client.fields import PackageIdentifier, PackageVersionIdentifier

    from cmem_client.client import Client

MARKETPLACE_CACHE_DIR = xdg_cache_home() / "eccenca-marketplace"


class Marketplace:
    """Interface for eccenca Marketplace server operations.

    The Marketplace component provides methods for downloading packages from the
    eccenca Marketplace server. It handles version resolution, package retrieval,
    and writing downloaded content to the filesystem.

    Attributes:
        _client: The Corporate Memory client instance used for HTTP communication.
        _marketplace_url: Default marketplace server URL for package operations.
    """

    _client: Client
    """The Corporate Memory client instance."""

    _marketplace_url: HttpUrl
    """The Marketplace server URL for package operations."""

    _cache_dir: Path | None

    def __init__(
        self,
        client: Client,
        marketplace_url: HttpUrl | str = "https://marketplace.eccenca.dev/",
        cache_dir: Path | None = MARKETPLACE_CACHE_DIR,
    ) -> None:
        """Initialize the Marketplace component.

        Args:
            client: The Corporate Memory client instance.
            marketplace_url: Default marketplace server URL. Defaults to the public eccenca Marketplace.
            cache_dir: Directory to use for cached downloads. If set to None, caching is disabled.
        """
        self._client = client
        self.marketplace_url = marketplace_url
        self.cache_dir = cache_dir

        if self.cache_dir is not None:
            self.cache_dir.mkdir(parents=True, exist_ok=True)

        self.logger = logging.getLogger(f"{self._client.logger.name}.{self.__class__.__name__}")

    @log_method
    def download_package(
        self,
        package_id: PackageIdentifier,
        path: Path | None = None,
        package_version: PackageVersionIdentifier | None = None,
        use_cache: bool = True,
    ) -> Path:
        """Download a package from the marketplace server to a specified directory.

        Queries the marketplace server for available versions and downloads the
        requested package version. If no version is specified, downloads the latest
        available version. The package is saved with the naming convention:
        {package_id}-v{version}.cpa

        If the package already exists in the cache, it will be reused instead of
        re-downloading.

        Args:
            path: Target directory where the package will be saved. If None, uses the
                cache directory. Must be a directory, not a file path.
            package_id: Marketplace package identifier (e.g., "semanticarts-gist-vocab").
            package_version: Specific version to download. If None, downloads the latest version.
            use_cache: If True, use cached version if available instead of downloading.

        Returns:
            The full file path where the package was saved (e.g.,
            /path/to/cache/semanticarts-gist-vocab-v13.0.0.cpa).

        Raises:
            MarketplaceReadError: If the marketplace server request fails or the package/version is not found.
        """
        if path is None:
            if self.cache_dir is not None:
                path = self.cache_dir
            else:
                raise MarketplaceReadError("Cannot download without a directory defined.")

        if not path.is_dir():
            path.mkdir(parents=True, exist_ok=True)

        available_versions = self.get_versions_from_package(package_id=package_id)

        version = str(available_versions[0]) if package_version is None else str(package_version)

        filename = f"{package_id}-v{version}.cpa"
        file_path = path / filename

        if file_path.exists() and use_cache:
            return file_path

        url = self._marketplace_url / "api/packages" / package_id / "versions" / version

        try:
            download_response = self._client.http.get(url=url)
            download_response.raise_for_status()
        except HTTPError as e:
            raise MarketplaceReadError(f"Error on downloading package '{package_id}'.") from e

        file_path.write_bytes(download_response.content)
        return file_path

    @log_method
    def get_versions_from_package(
        self,
        package_id: PackageIdentifier,
    ) -> list[PackageVersionIdentifier]:
        """Get the available versions of a package from the marketplace server.

        Args:
            package_id: Marketplace package identifier.

        Returns:
            List of package versions available.
        """
        url = self.marketplace_url / "api/packages" / package_id / "versions"
        try:
            versions_response = self._client.http.get(url=url)
            versions_response.raise_for_status()
            versions = versions_response.json()
        except HTTPError as e:
            raise MarketplaceReadError(f"Error on retrieving package versions for '{package_id}'.") from e

        return sorted([version.get("package_version") for version in versions])

    @property
    def marketplace_url(self) -> HttpUrl:
        """Get the marketplace server URL."""
        return self._marketplace_url

    @marketplace_url.setter
    def marketplace_url(self, marketplace_url: HttpUrl | str) -> None:
        """Set the marketplace server URL."""
        self._marketplace_url = marketplace_url if isinstance(marketplace_url, HttpUrl) else HttpUrl(marketplace_url)

    @property
    def cache_dir(self) -> Path | None:
        """Get the cache directory."""
        return self._cache_dir

    @cache_dir.setter
    def cache_dir(self, cache_dir: Path | None) -> None:
        """Set the cache directory."""
        self._cache_dir = cache_dir
