"""Repository for managing named graphs in Corporate Memory.

Provides GraphRepository class for managing RDF named graphs with operations for
deletion and import. Supports multiple RDF formats (Turtle, RDF/XML, JSON-LD, N-Triples)
with automatic file type detection.
"""

from __future__ import annotations

import mimetypes
import tempfile
import zipfile
from copy import copy
from pathlib import Path
from tempfile import NamedTemporaryFile
from typing import TYPE_CHECKING, ClassVar
from urllib.parse import quote
from uuid import uuid4

from pydantic import Field, TypeAdapter
from rdflib import Graph as RDFGraph

if TYPE_CHECKING:
    from cmem_client.client import Client

from cmem_client.exceptions import GraphExportError, GraphImportError, RepositoryModificationError
from cmem_client.models.base import Model
from cmem_client.models.graph import Graph
from cmem_client.models.item import FileImportItem, ImportItem, ZipImportItem
from cmem_client.repositories.base.abc import RepositoryConfig
from cmem_client.repositories.base.plain_list import PlainListRepository
from cmem_client.repositories.protocols.delete_item import DeleteConfig, DeleteItemProtocol
from cmem_client.repositories.protocols.export_item import ExportConfig, ExportItemProtocol
from cmem_client.repositories.protocols.import_item import ImportConfig, ImportItemProtocol

if TYPE_CHECKING:
    from collections.abc import Generator


GET_ONTOLOGY_IRI_QUERY = """
PREFIX owl: <http://www.w3.org/2002/07/owl#>
SELECT DISTINCT ?iri
WHERE {
    ?iri a owl:Ontology;
}
"""

GET_PREFIX_DECLARATION = """
PREFIX owl: <http://www.w3.org/2002/07/owl#>
PREFIX vann: <http://purl.org/vocab/vann/>
SELECT DISTINCT ?prefix ?namespace
WHERE {{
    <{ontology_iri}> a owl:Ontology;
        vann:preferredNamespacePrefix ?prefix;
        vann:preferredNamespaceUri ?namespace.
}}
"""

INSERT_CATALOG_ENTRY = """
PREFIX voaf: <http://purl.org/vocommons/voaf#>
PREFIX vann: <http://purl.org/vocab/vann/>
PREFIX dct: <http://purl.org/dc/terms/>
PREFIX skos: <http://www.w3.org/2004/02/skos/core#>
WITH <https://ns.eccenca.com/example/data/vocabs/>
INSERT {{
    <{iri}> a voaf:Vocabulary ;
        skos:prefLabel "{label}"{language} ;
        vann:preferredNamespacePrefix "{prefix}" ;
        vann:preferredNamespaceUri "{namespace}" ;
        dct:description "vocabulary imported with cmem-client" .
}}
WHERE {{}}
"""


class GraphFileSerialization(Model):
    """Supported graph format description"""

    mime_type: str
    file_extensions: list[str]
    encoding: str | None = None
    known_not_supporters: list[str] = Field(default_factory=list)


class GraphImportConfig(ImportConfig):
    """Graph Import Configuration."""

    register_as_vocabulary: bool = False
    serialization: GraphFileSerialization | None = None


class GraphExportConfig(ExportConfig):
    """Graph Export Configuration."""

    register_as_vocabulary: bool = False
    serialization: GraphFileSerialization | None = None


class GraphDeleteConfig(DeleteConfig):
    """Graph Delete Configuration."""


def _extract_vann_metadata(graph: RDFGraph, ontology_iri: str) -> tuple[str, str] | None:
    """Extract vann namespace prefix and URI from an RDF graph.

    Args:
        graph: Parsed RDF graph
        ontology_iri: IRI of the owl:Ontology resource

    Returns:
        Tuple of (prefix, namespace_uri) if vann properties exist, None otherwise
    """
    vann_data = graph.query(GET_PREFIX_DECLARATION.format(ontology_iri=ontology_iri))

    if len(vann_data) == 0:
        return None

    if len(vann_data) > 1:
        raise GraphImportError(f"Multiple vann namespace declarations found for ontology: {ontology_iri}")

    namespace_info = next(iter(vann_data))
    prefix = str(namespace_info[0])  # type: ignore[index]
    namespace_uri = str(namespace_info[1])  # type: ignore[index]

    return prefix, namespace_uri


class GraphsRepository(PlainListRepository, DeleteItemProtocol, ImportItemProtocol, ExportItemProtocol):
    """Repository for graphs.

    This repository manages named graphs which are described with the Graph model.
    Supports both regular graphs and vocabularies through the register_as_vocabulary flag.
    """

    _client: Client

    _dict: dict[str, Graph]
    _allowed_import_items: ClassVar[list[type[ImportItem]]] = [FileImportItem, ZipImportItem]
    _config = RepositoryConfig(
        component="explore",
        fetch_data_path="/graphs/list",
        fetch_data_adapter=TypeAdapter(list[Graph]),
    )
    _formats: ClassVar[dict[str, GraphFileSerialization]] = {
        "turtle": GraphFileSerialization(mime_type="text/turtle", file_extensions=["ttl"]),
        "rdf/xml": GraphFileSerialization(
            mime_type="application/rdf+xml", file_extensions=["rdf", "xml"], known_not_supporters=["TENTRIS"]
        ),
        "json-ld": GraphFileSerialization(
            mime_type="application/ld+json", file_extensions=["jsonld"], known_not_supporters=["TENTRIS"]
        ),
        "n-triples": GraphFileSerialization(mime_type="application/n-triples", file_extensions=["nt"]),
    }

    def export_to_zip(self, key: str, path: Path | None = None, replace: bool = False) -> Path:
        """Export graph to a ZIP file.

        Exports a single RDF file to a ZIP archive.

        Args:
            key: The URI/identifier of the graph to export.
            path: Optional target path for the ZIP file. If None, creates a temporary file.
            replace: Whether to overwrite an existing file at the target path.

        Returns:
            Path to the created ZIP file.

        Raises:
            GraphExportError: If the file already exists and replace is False, or if
                the exported graph is empty.
        """
        if path is None:
            with tempfile.NamedTemporaryFile(delete=False, suffix=".zip") as tmp:
                zip_path = Path(tmp.name)
        else:
            zip_path = path
            if zip_path.exists() and not replace:
                raise GraphExportError(f"File {zip_path} already exists and replace is False")

        with tempfile.TemporaryDirectory() as tmpdir:
            turtle_path = Path(tmpdir) / "graph.ttl"
            self.export_item(key=key, path=turtle_path, replace=True)

            turtle_content = turtle_path.read_bytes()
            if not turtle_content:
                raise GraphExportError("Exported turtle file is empty")

            safe_name = key.split("/")[-1].rstrip("#") or "graph"
            if not safe_name.endswith(".ttl"):
                safe_name += ".ttl"

            with zipfile.ZipFile(zip_path, mode="w", compression=zipfile.ZIP_DEFLATED) as zipf:
                zipf.writestr(safe_name, turtle_content)

        return zip_path

    def _delete_item(self, key: str, configuration: GraphDeleteConfig | None = None) -> None:
        """Delete a named graph from the repository.

        Args:
            key: The URI/identifier of the graph to delete.
            configuration: Optional configuration to delete.

        Raises:
            HTTPError: If the deletion request fails.
        """
        _ = configuration
        url = self._url("/proxy/default/graph")
        params = {"graph": key}
        response = self._client.http.delete(url=url, params=params)
        response.raise_for_status()

    def guess_file_type(self, path: Path) -> GraphFileSerialization:
        """Guess the RDF serialization format from a file path.

        Attempts to determine the appropriate GraphFileSerialization by examining
        the file's MIME type and file extension. Supports compressed files (.gz).

        Args:
            path: Path to the RDF file to analyze.

        Returns:
            GraphFileSerialization: The detected serialization format with
                MIME type, file extensions, and optional encoding information.

        Raises:
            RepositoryModificationError: If the file type cannot be determined
                from the path or extension.
        """
        guessed_file_type: GraphFileSerialization | None = None

        # guess with mime-type python standard lib
        # then guess with file suffix
        content_type, encoding = mimetypes.guess_type(path)
        for _ in self._formats.values():
            if content_type == _.mime_type:
                guessed_file_type = copy(_)
                break
            for suffix in _.file_extensions:
                if path.name.endswith(suffix) or path.name.endswith(f"{suffix}.gz"):
                    guessed_file_type = copy(_)
                    break

        if guessed_file_type is None:
            raise RepositoryModificationError(f"Can not guess file type of {path.name}")

        if encoding is not None:
            guessed_file_type.encoding = encoding
        return guessed_file_type

    @staticmethod
    def byte_generator(file_path: Path, chunk_size: int = 1024) -> Generator[bytes, None, None]:
        """Generate bytes from a file in chunks.

        Args:
            file_path: Path to the file to read
            chunk_size: Size of each chunk in bytes (default: 1024)

        Yields:
            bytes: Chunks of data from the file
        """
        with file_path.open("rb") as opened_file:
            while True:
                chunk = opened_file.read(chunk_size)
                if not chunk:
                    break
                yield chunk

    def _import_item(  # noqa: C901 PLR0912
        self,
        path: Path | None = Path(),
        replace: bool = False,
        key: str | None = None,
        configuration: GraphImportConfig | None = None,
    ) -> str:
        """Import an RDF graph from a file into the repository.

        Uploads an RDF file to Corporate Memory, automatically detecting the
        serialization format and setting appropriate HTTP headers. If no key
        is provided, generates a unique URI for the graph.

        For vocabularies (when register_as_vocabulary=True), extracts vann namespace
        metadata and creates a catalog entry.

        Args:
            path: Path to the RDF file to import.
            replace: Whether to replace an existing graph with the same key.
            key: Optional URI/identifier for the graph. If None, generates
                a unique UUID-based URI.
            configuration: Optional configuration object for the graph to decide
                weather the graph should be imported as a vocabulary.

        Returns:
            str: The URI/identifier of the imported graph.

        Raises:
            RepositoryModificationError: If the file type cannot be detected.
            GraphImportError: If no path is given,
                vocabulary validation fails or vann metadata is missing.
            HTTPError: If the import request fails.
        """
        if path is None:
            raise GraphImportError("Path must be specified.")

        if configuration is None:
            configuration = GraphImportConfig()

        if path.is_dir():
            graph_files = [f for f in path.iterdir() if f.is_file()]
            if len(graph_files) == 0:
                raise GraphImportError(f"No graph files found in directory {path}")
            if len(graph_files) > 1:
                raise GraphImportError(f"Multiple graph files found in directory {path}")
            path = graph_files[0]

        parsed_graph: RDFGraph
        vann_metadata: tuple[str, str] | None = None

        if configuration.register_as_vocabulary:
            parsed_graph = RDFGraph().parse(path)

            if key is None:
                ontology_iris = parsed_graph.query(GET_ONTOLOGY_IRI_QUERY)
                if len(ontology_iris) == 0:
                    raise GraphImportError("There is no owl:Ontology resource described in the RDF file.")
                if len(ontology_iris) > 1:
                    ontology_iris_str = [str(iri[0]) for iri in ontology_iris]  # type: ignore[index]
                    raise GraphImportError(
                        f"There are more than one owl:Ontology resources described in the RDF file: {ontology_iris_str}"
                    )
                key = str(next(iter(ontology_iris))[0])  # type: ignore[index]
            vann_metadata = _extract_vann_metadata(parsed_graph, key)

        if key is None:
            key = str(self._client.config.url_base / f"{uuid4()!s}/")

        encoded_key = quote(key, safe="")
        url = self._url(f"/proxy/default/graph?graph={encoded_key}&replace={str(replace).lower()}")

        file_type = configuration.serialization or self.guess_file_type(path)

        headers = {"Content-Type": file_type.mime_type}
        if file_type.encoding:
            headers["Content-Encoding"] = file_type.encoding

        self._client.http.post(url=url, headers=headers, content=self.byte_generator(file_path=path)).raise_for_status()
        self.fetch_data()

        if configuration.register_as_vocabulary:
            if vann_metadata is not None:
                prefix, namespace = vann_metadata
                label, language = self._resolve_label(iri=key, prefix=prefix)
                self._insert_catalog_entry(iri=key, prefix=prefix, namespace=namespace, label=label, language=language)

            self._reload_vocabularies(key)

        return key

    def _export_item(
        self, key: str, path: Path | None, replace: bool = False, configuration: GraphExportConfig | None = None
    ) -> Path:
        """Export a named graph from the repository to a file.

        Downloads the specified graph from Corporate Memory and saves it to
        the given path as Turtle format. If no path is provided, creates a
        temporary file. OWL imports are not resolved during export.

        Args:
            key: The URI/identifier of the graph to export.
            path: Optional target path for the exported file. If None,
                creates a temporary file with .ttl extension.
            replace: Whether to overwrite an existing file at the target path.
            configuration: Optional configuration object for the graph to decide
                whether the graph should be exported as a vocabulary.

        Returns:
            Path: The path where the graph was exported.

        Raises:
            FileExistsError: If the target file exists and replace is False.
            HTTPError: If the export request fails.
        """
        _ = configuration
        if path and path.exists() and not replace:
            raise FileExistsError(f"File {path.name} already exists and replace is {replace}")
        encoded_key = quote(key, safe="")
        url = self._url(f"/proxy/default/graph?graph={encoded_key}&owlImportsResolution=false")
        with (
            NamedTemporaryFile(delete=False, suffix=".ttl") if path is None else path.open("wb") as opened_file,
            self._client.http.stream(method="GET", url=url) as response,
        ):
            response.raise_for_status()
            for chunk in response.iter_bytes():
                if chunk:
                    opened_file.write(chunk)
            opened_file.close()
            return Path(opened_file.name)

    def _resolve_label(self, iri: str, prefix: str) -> tuple[str, str]:
        """Resolve label for an ontology using the /api/explore/titles endpoint.

        Calls Corporate Memory's title resolution API to get a human-readable label
        for the ontology IRI. Formats the label with the prefix as "prefix: title".

        Args:
            iri: The ontology IRI to resolve
            prefix: The namespace prefix to prepend to the label

        Returns:
            Tuple of (label, language_tag). Language tag is empty if not present.
        """
        url = self._client.config.url_explore_api / "/api/explore/titles"
        headers = {"Content-Type": "application/json", "Accept": "application/json"}
        params = {"contextGraph": iri}
        response = self._client.http.post(url=url, headers=headers, params=params, json=[iri])
        response.raise_for_status()
        results = response.json()

        resolved = results.get(iri, {})
        title = resolved.get("title", iri)
        lang = resolved.get("lang", "")

        label = f"{prefix}: {title}" if not title.startswith(f"{prefix}:") else title

        return label, lang

    def _insert_catalog_entry(self, iri: str, prefix: str, namespace: str, label: str, language: str) -> None:
        """Insert vocabulary catalog entry with vann namespace metadata.

        Creates a catalog entry in the vocabulary catalog graph that links the
        ontology IRI with its preferred namespace prefix and URI.

        Args:
            iri: The ontology IRI
            prefix: The vann:preferredNamespacePrefix
            namespace: The vann:preferredNamespaceUri
            label: The human-readable label for the vocabulary
            language: Optional language tag (e.g., "en", "de")
        """
        language_tag = f"@{language}" if language else ""

        query = INSERT_CATALOG_ENTRY.format(
            iri=iri,
            prefix=prefix,
            namespace=namespace,
            label=label,
            language=language_tag,
        )
        self._client.store.sparql.update(query)

    def _reload_vocabularies(self, iri: str) -> None:
        """Reload the caches and prefixes for vocabularies."""
        reload_prefix_url = self._client.config.url_build_api / "/workspace/reloadPrefixes"
        self._client.http.post(url=reload_prefix_url)
        update_cache_url = self._client.config.url_build_api / "/workspace/updateGlobalVocabularyCache"
        update_cache_data = {"iri": iri}
        update_cache_headers = {"Content-Type": "application/json"}
        self._client.http.post(url=update_cache_url, json=update_cache_data, headers=update_cache_headers)
