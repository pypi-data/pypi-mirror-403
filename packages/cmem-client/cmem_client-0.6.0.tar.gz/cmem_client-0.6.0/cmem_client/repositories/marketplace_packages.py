"""Repository for eccenca marketplace package operations.

This module provides the PackagesRepository class for managing marketplace packages
in Corporate Memory.
"""

from __future__ import annotations

import shutil
import tempfile
from pathlib import Path
from typing import TYPE_CHECKING, ClassVar
from zipfile import BadZipFile, ZipFile

from eccenca_marketplace_client.models.dependencies import MarketplacePackageDependency, PythonPackageDependency
from eccenca_marketplace_client.models.files import GraphFileSpec, ImageFileSpec, ProjectFileSpec, TextFileSpec
from eccenca_marketplace_client.ontology import (
    NS_IRI,
    get_data_graph_iri,
    get_delete_query,
    get_fetch_query,
    get_ontology_graph,
)
from eccenca_marketplace_client.package_graph import PackageGraph
from eccenca_marketplace_client.package_version import PackageVersion

from cmem_client.exceptions import (
    BaseError,
    MarketplacePackagesExportError,
    MarketplacePackagesImportError,
)
from cmem_client.models.project import Project, ProjectMetaData
from cmem_client.models.python_package import PythonPackage
from cmem_client.repositories.files import FilesImportConfig
from cmem_client.repositories.graph_imports import GraphImport

if TYPE_CHECKING:
    from collections.abc import Sequence

from eccenca_marketplace_client.fields import PackageVersionIdentifier  # noqa: TC002  # Pydantic needs this at runtime

from cmem_client.models.item import DirectoryImportItem, FileImportItem, ImportItem, ZipImportItem
from cmem_client.models.package import Package
from cmem_client.repositories.base.abc import Repository
from cmem_client.repositories.graphs import GraphImportConfig
from cmem_client.repositories.protocols.delete_item import DeleteConfig, DeleteItemProtocol
from cmem_client.repositories.protocols.export_item import ExportConfig, ExportItemProtocol
from cmem_client.repositories.protocols.import_item import ImportConfig, ImportItemProtocol

MAX_DEPENDENCY_DEPTH = 5
MARKETPLACE_PROJECT_ID = "marketplace-packages"


class MarketplacePackagesImportConfig(ImportConfig):
    """Configuration for marketplace package import operations.

    Attributes:
        ignore_dependencies: If True, skips installation of package dependencies.
        install_from_marketplace: If True, downloads packages from the marketplace server.
            If False, loads packages from local filesystem.
        package_version: Specific version to install. If None, installs the latest version.
        dependency_level: Current recursion depth for dependency resolution. Used internally
            to prevent infinite recursion. Should not be set manually.
        use_cache: Weather to use the cache directory to look packages up which have already been downloaded.
            To prevent the cache entirely, set this up in the marketplace component.
    """

    ignore_dependencies: bool = False
    install_from_marketplace: bool = True
    package_version: PackageVersionIdentifier | None = None
    dependency_level: int = 0
    use_cache: bool = True


class MarketplacePackagesExportConfig(ExportConfig):
    """Package export configuration"""

    export_as_zip: bool = True


class MarketplacePackagesDeleteConfig(DeleteConfig):
    """Package deletion configuration"""

    skip_missing_dependencies: bool = True
    skip_missing_graphs: bool = True
    skip_missing_projects: bool = True


class MarketplacePackagesRepository(Repository, ImportItemProtocol, ExportItemProtocol, DeleteItemProtocol):
    """Repository for marketplace package operations."""

    _dict: dict[str, Package]
    _allowed_import_items: ClassVar[Sequence[type[ImportItem]]] = [FileImportItem, ZipImportItem, DirectoryImportItem]
    _graph: PackageGraph

    def fetch_data(self) -> None:
        """Fetch installed packages from the config graph via SPARQL query.

        Queries the config graph for all installed packages and their metadata.
        """
        result = self._client.store.sparql.query(get_fetch_query())

        self._dict = {}
        self._graph = PackageGraph()
        for row in result:
            manifest_json = str(row[0])  # type: ignore[index]
            package_version = PackageVersion.from_json(manifest_json)
            package_id = package_version.manifest.package_id
            package = Package(package_version=package_version)
            self._dict[package_id] = package
            self._graph.add_package(package.package_version)

    def _add_marketplace_vocabulary(self) -> None:
        """Ensure the package vocabulary/ontology is imported into CMEM.

        Checks if the marketplace ontology graph exists. If not, generates the
        ontology from the marketplace client models and imports it as a vocabulary.
        """
        ontology_graph = get_ontology_graph()

        self._client.graphs.fetch_data()

        if NS_IRI not in self._client.graphs:
            with tempfile.NamedTemporaryFile(mode="wb", suffix=".ttl", delete=False) as tmp_file:
                tmp_path = Path(tmp_file.name)
                tmp_file.write(ontology_graph.serialize(format="turtle").encode("utf-8"))

            try:
                get_ontology_graph()
                self._client.graphs.import_item(
                    path=tmp_path,
                    replace=False,
                    key=NS_IRI,
                )
            finally:
                tmp_path.unlink(missing_ok=True)

    def _import_item(  # noqa: C901, PLR0912, PLR0915
        self,
        path: Path | None = None,
        replace: bool = False,
        key: str | None = None,
        configuration: MarketplacePackagesImportConfig | None = None,
    ) -> str:
        """Import a marketplace package from archive or marketplace server.

        Extracts the package manifest from the archive, adds package metadata to the
        config graph as RDF triples, then delegates to the appropriate repositories
        based on the package.

        If the import fails, all imported resources (graphs, projects, imports, packages)
        are automatically rolled back to maintain consistency.

        Args:
            path: Path to the package archive file (.cpa) or directory. Required when
                configuration.install_from_marketplace is False.
            replace: Whether to replace an existing package with the same ID.
            key: Package identifier for marketplace installation. Required when
                configuration.install_from_marketplace is True.
            configuration: Import configuration controlling source (marketplace vs. local),
                dependency resolution, and version selection.

        Returns:
            The package_id of the successfully imported package.

        Raises:
            MarketplacePackagesImportError: If required parameters are missing, the package
                already exists (when replace=False), or the import fails.
        """
        if configuration is None:
            configuration = MarketplacePackagesImportConfig()

        if path is None and not configuration.install_from_marketplace:
            raise MarketplacePackagesImportError("No import path specified.")

        package_version = self._get_package_version(configuration, key, path)

        manifest = package_version.manifest

        imported_graphs: list[str] = []
        imported_projects: list[str] = []
        imported_imports: list[str] = []
        imported_python_packages: list[str] = []
        imported_vocabulary_packages: list[str] = []
        imported_files: list[str] = []

        if manifest.package_id in self._dict:
            if replace:
                self.delete_item(manifest.package_id)
            else:
                raise MarketplacePackagesImportError("Package already imported. Try replace.")

        self._create_assets_project()

        if not configuration.ignore_dependencies:
            # import python package dependencies first
            for dependency in manifest.dependencies:
                if isinstance(dependency, PythonPackageDependency):
                    self._client.python_packages.create_item(
                        item=PythonPackage(name=dependency.pypi_id), skip_if_existing=True
                    )
                    imported_python_packages.append(dependency.pypi_id)

            for dependency in manifest.dependencies:
                if isinstance(dependency, MarketplacePackageDependency) and dependency.package_id not in self._dict:
                    if configuration.dependency_level >= MAX_DEPENDENCY_DEPTH:
                        self.logger.warning(
                            "Skipping dependency '%s' because the max depth of '%s' was reached.",
                            dependency,
                            MAX_DEPENDENCY_DEPTH,
                        )
                        continue
                    self._client.marketplace_packages.import_item(
                        key=dependency.package_id,
                        configuration=MarketplacePackagesImportConfig(
                            dependency_level=configuration.dependency_level + 1,
                        ),
                        skip_if_existing=True,
                    )
                    imported_vocabulary_packages.append(dependency.package_id)

        try:
            # import graphs first
            for graph in manifest.get_graphs():
                graph_iri = self._client.graphs.import_item(
                    key=str(graph.graph_iri),
                    path=package_version.get_file_path(graph.file_path),
                    replace=replace,
                    configuration=GraphImportConfig(register_as_vocabulary=graph.register_as_vocabulary),
                )
                imported_graphs.append(graph_iri)

            # import projects after graphs
            for project in manifest.get_projects():
                project_id = self._client.projects.import_item(
                    key=str(project.project_id),
                    path=package_version.get_file_path(project.file_path),
                    replace=replace,
                )
                imported_projects.append(project_id)

            # add graph imports
            for graph in manifest.get_graphs():
                to_graph = str(graph.graph_iri)
                for from_graph in graph.import_into:
                    new_import = GraphImport(from_graph=str(from_graph), to_graph=to_graph)
                    self._client.graph_imports.create_item(item=new_import, skip_if_existing=True)
                    imported_imports.append(new_import.get_id())

            for file in manifest.files:
                file_resource_path = f"{manifest.package_id}/{file.file_path}"
                composite_key = f"{MARKETPLACE_PROJECT_ID}:{file_resource_path}"
                self._client.files.import_item(
                    path=package_version.get_file_path(file.file_path),
                    key=composite_key,
                    replace=True,
                    configuration=FilesImportConfig(use_archive_handler=False),
                )
                imported_files.append(composite_key)

            self._add_package_triples(package_version)

        # Rollback graphs + imports, projects, python packages
        except (BaseError, BadZipFile) as error:
            self._client.logger.exception("Failed to import package '%s'", package_version.manifest.package_id)
            self._client.logger.warning("Deleting all imports from this package.")
            for graph_import in imported_imports:
                self._client.graph_imports.delete_item(key=graph_import, skip_if_missing=True)
            for graph_iri in imported_graphs:
                self._client.graphs.delete_item(key=graph_iri, skip_if_missing=True)
            for project_id in imported_projects:
                self._client.projects.delete_item(key=project_id, skip_if_missing=True)
            for python_package_id in imported_python_packages:
                self._client.python_packages.delete_item(key=python_package_id, skip_if_missing=True)
            for vocabulary_id in imported_vocabulary_packages:
                self._client.marketplace_packages.delete_item(key=vocabulary_id, skip_if_missing=True)
            for file in imported_files:
                self._client.files.delete_item(key=file, skip_if_missing=True)
            raise MarketplacePackagesImportError(f"Failed to import package ({error!s})") from error

        self.fetch_data()
        return str(manifest.package_id)

    def _export_item(  # noqa: C901
        self,
        key: str,
        path: Path | None,
        replace: bool = False,
        configuration: MarketplacePackagesExportConfig | None = None,
    ) -> Path:
        """Export a marketplace package from eccenca Corporate Memory.

        Args:
            key: The package identifier.
            path: The file path where the item should be exported. If None, a path
                should be generated by the implementation.
            replace: Whether to replace existing files at the target path.
            configuration: Optional configuration for export behavior.

        Returns:
            The exported file path.
        """
        if configuration is None:
            configuration = MarketplacePackagesExportConfig()

        if key not in self._dict:
            raise MarketplacePackagesExportError("Key is not a valid package identifier")

        package = self._dict[key]
        manifest_json_str = self._get_manifest_json(package.package_version.manifest.package_id)
        manifest = PackageVersion.from_json(manifest_json_str).manifest

        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            exported_files: list[tuple[Path, str]] = []

            for file_spec in manifest.files:
                if isinstance(file_spec, GraphFileSpec):
                    file_path = tmp_path / file_spec.file_path
                    file_path.parent.mkdir(parents=True, exist_ok=True)
                    exported_path = self._client.graphs.export_item(
                        key=str(file_spec.graph_iri),
                        path=file_path,
                    )
                    exported_files.append((exported_path, file_spec.file_path))

                if isinstance(file_spec, ProjectFileSpec):
                    file_path = tmp_path / file_spec.file_path
                    file_path.parent.mkdir(parents=True, exist_ok=True)
                    exported_path = self._client.projects.export_item(
                        key=file_spec.project_id,
                        path=file_path,
                    )
                    exported_files.append((exported_path, file_spec.file_path))

                if isinstance(file_spec, (ImageFileSpec, TextFileSpec)):
                    file_path = tmp_path / file_spec.file_path
                    file_path.parent.mkdir(parents=True, exist_ok=True)
                    file_resource_path = f"{manifest.package_id}/{file_spec.file_path}"
                    composite_key = f"{MARKETPLACE_PROJECT_ID}:{file_resource_path}"
                    self._client.files.export_item(key=composite_key, path=file_path)
                    exported_files.append((file_path, file_spec.file_path))

            manifest_path = tmp_path / "manifest.json"
            manifest_path.write_text(manifest_json_str, encoding="utf-8")

            if path is None:
                path = Path.cwd() / (
                    f"{manifest.package_id}.zip" if configuration.export_as_zip else manifest.package_id
                )

            if path.exists() and not replace:
                item_type = "File" if configuration.export_as_zip else "Directory"
                raise MarketplacePackagesExportError(f"{item_type} {path} already exists and replace is False")

            if configuration.export_as_zip:
                with ZipFile(path, mode="w") as zipf:
                    for file_path, file_name in exported_files:
                        zipf.write(file_path, file_name)
                    zipf.write(manifest_path, "manifest.json")
            else:
                path.mkdir(parents=True, exist_ok=True)
                for file_path, file_name in exported_files:
                    file_dest = path / file_name
                    file_dest.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy(file_path, file_dest)
                shutil.copy(manifest_path, path / "manifest.json")

        return path

    def _delete_item(self, key: str, configuration: MarketplacePackagesDeleteConfig | None = None) -> None:  # noqa: C901
        """Delete a package by its package_id.

        This method need be extended for new FileSpecs.

        Args:
            key: The package_id of the package to delete.
            configuration: Optional configuration to delete.
        """
        if not configuration:
            # apply default configuration
            configuration = MarketplacePackagesDeleteConfig()
        package = self._dict[key]
        manifest = package.package_version.manifest
        package_id = manifest.package_id
        package_iri = package.package_version.iri()

        for dependency in manifest.dependencies:
            if isinstance(dependency, PythonPackageDependency):
                dependants = self._graph.get_python_dependants(dependency.pypi_id)
                dependants.remove(package_id)
                if len(dependants) > 0:
                    self._logger.warning(
                        f"Python plugin '{dependency.pypi_id}' can not be removed since it is in"
                        f"use by other packages: {', '.join(dependants)}"
                    )
                    continue
                self._client.python_packages.delete_item(
                    key=dependency.pypi_id, skip_if_missing=configuration.skip_missing_dependencies
                )

            if isinstance(dependency, MarketplacePackageDependency):
                dependants = self._graph.get_package_dependants(dependency.package_id)
                dependants.remove(package_id)
                if len(dependants) > 0:
                    self._logger.warning(
                        f"Package '{dependency.package_id}' can not be removed since it is in"
                        f"use by other packages: {', '.join(dependants)}"
                    )
                    continue
                self._client.marketplace_packages.delete_item(
                    key=dependency.package_id, skip_if_missing=configuration.skip_missing_dependencies
                )

        for project in manifest.get_projects():
            self._client.projects.delete_item(
                key=project.project_id, skip_if_missing=configuration.skip_missing_projects
            )

        for graph in manifest.get_graphs():
            self._client.graphs.delete_item(key=str(graph.graph_iri), skip_if_missing=configuration.skip_missing_graphs)
            for from_graph in graph.import_into:
                deleted_import = GraphImport(from_graph=str(from_graph), to_graph=str(graph.graph_iri))
                self._client.graph_imports.delete_item(key=deleted_import.get_id(), skip_if_missing=True)

        for file in manifest.files:
            file_resource_path = f"{manifest.package_id}/{file.file_path}"
            composite_key = f"{MARKETPLACE_PROJECT_ID}:{file_resource_path}"
            self._client.files.delete_item(key=composite_key, skip_if_missing=True)

        self._client.store.sparql.update(get_delete_query(package_iri))

        # Remaining package is removed by the protocol, marketplace vocabulary and project can be deleted safely
        if len(self._dict) == 1 and key in self._dict:
            self._client.graphs.delete_item(NS_IRI, skip_if_missing=True)
            self._client.projects.delete_item(MARKETPLACE_PROJECT_ID, skip_if_missing=True)

    def _add_package_triples(self, package: PackageVersion) -> None:
        """Add a package to the data config graph in the Corporate Memory instance.

        Converts the package metadata to RDF triples and inserts them into the
        config data graph using SPARQL UPDATE. Uses rdflib to programmatically
        construct the RDF graph, avoiding manual string escaping.

        Args:
            package: The package metadata to add to the catalog.
        """
        self._add_marketplace_vocabulary()
        g = package.to_rdf_graph()

        triples = g.serialize(format="nt")

        sparql_update = f"""
        INSERT DATA {{
            GRAPH <{get_data_graph_iri()}> {{
                {triples}
            }}
        }}
        """

        self._client.store.sparql.update(sparql_update)

    def _get_manifest_json(self, package_id: str) -> str:
        """Fetch manifest JSON from config graph via SPARQL for a specific package_id."""
        package_iri = f"{get_data_graph_iri()}{package_id}"
        query = f"""
        PREFIX eccm: <{NS_IRI}>
        SELECT ?manifest_json
        WHERE {{
            GRAPH <{get_data_graph_iri()}> {{
                <{package_iri}> eccm:property_manifest_json ?manifest_json .
            }}
        }}
        """
        response = self._client.http.get(
            url=self._client.config.url_explore_api / "/proxy/default/sparql",
            headers={"Accept": "application/sparql-results+json"},
            params={"query": query},
        )
        response.raise_for_status()
        bindings = response.json()["results"]["bindings"]
        return str(bindings[0]["manifest_json"]["value"])

    def _get_package_version(
        self, configuration: MarketplacePackagesImportConfig, key: str | None, path: Path | None
    ) -> PackageVersion:
        """Load package version from marketplace server or local filesystem.

        When installing from the marketplace server, the package is downloaded into the cache directory if path is
        set to None. The method then returns the path to the cached file so it can be reused later.
        If path is provided, the package is downloaded to that location instead.

        When installing from the local filesystem, path must point directly to the package to be installed.

        Args:
            configuration: Import configuration specifying the package source and version.
            key: Package identifier for marketplace downloads. Required when
                configuration.install_from_marketplace is True.
            path: Local filesystem path for non-marketplace installations. Required when
                configuration.install_from_marketplace is False.

        Returns:
            The package version from marketplace server or local filesystem.

        Raises:
            MarketplacePackagesImportError: If path is None when loading from local filesystem.
        """
        if configuration.install_from_marketplace:
            if key is None:
                raise MarketplacePackagesImportError("No key was provided to download from marketplace.")

            downloaded_package_path = self._client.marketplace.download_package(
                path=path,
                package_id=key,
                package_version=configuration.package_version,
                use_cache=configuration.use_cache,
            )
            package_version = PackageVersion.from_archive(downloaded_package_path)
        else:
            if path is None:
                raise MarketplacePackagesImportError("No package path specified")
            package_version = (
                PackageVersion.from_directory(path) if path.is_dir() else PackageVersion.from_archive(path)
            )

        return package_version

    def _create_assets_project(self) -> None:
        """Create the assets project for the marketplace."""
        if MARKETPLACE_PROJECT_ID in self._client.projects:
            return
        mp_assets = Project(
            name=MARKETPLACE_PROJECT_ID,
            metaData=ProjectMetaData(
                label="Marketplace Packages",
                description="""This project contains all files that were installed via Marketplace packages.

This project was created when you installed your first package.
It will be deleted after the last package is uninstalled.

For more information about marketplace packages, have a look at
[documentation.eccenca.com](https://go.eccenca.com/feature/marketplace-packages).
""",
            ),
        )
        self._client.projects.create_item(mp_assets)
        self._client.projects.fetch_data()
