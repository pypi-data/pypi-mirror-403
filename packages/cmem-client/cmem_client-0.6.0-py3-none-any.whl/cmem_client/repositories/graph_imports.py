"""Repository for managing Graph Imports"""

from cmem_client.exceptions import RepositoryModificationError
from cmem_client.models.base import ReadRepositoryItem
from cmem_client.repositories.base.abc import Repository
from cmem_client.repositories.protocols.create_item import CreateConfig, CreateItemProtocol
from cmem_client.repositories.protocols.delete_item import DeleteConfig, DeleteItemProtocol

GRAPH_IMPORTS_LIST_SPARQL = """
PREFIX owl: <http://www.w3.org/2002/07/owl#>

SELECT ?from_graph ?to_graph
WHERE
{
  GRAPH ?from_graph {
    ?from_graph owl:imports ?to_graph
  }
}
"""

GRAPH_IMPORTS_CREATE_SPARQL = """
PREFIX owl: <http://www.w3.org/2002/07/owl#>

INSERT DATA {{
  GRAPH <{from_graph}> {{
    <{from_graph}> owl:imports <{to_graph}> .
  }}
}}
"""

GRAPH_IMPORTS_DELETE_SPARQL = """
PREFIX owl: <http://www.w3.org/2002/07/owl#>

DELETE DATA {{
  GRAPH <{from_graph}> {{
    <{from_graph}> owl:imports <{to_graph}> .
  }}
}}
"""


class GraphImportsCreateConfig(CreateConfig):
    """Graph Imports creation configuration"""


class GraphImportsDeleteConfig(DeleteConfig):
    """Graph Imports deletion configuration."""


class GraphImport(ReadRepositoryItem):
    """Graph Import Repository Item"""

    from_graph: str
    to_graph: str

    def get_id(self) -> str:
        """Get the id of the item."""
        return f"{self.from_graph}::::{self.to_graph}"


class GraphImportsRepository(Repository, CreateItemProtocol, DeleteItemProtocol):
    """Repository for managing Graph Imports"""

    _dict: dict[str, GraphImport]

    def fetch_data(self) -> None:
        """Fetch new data and update the repository"""
        items = {}
        results = self._client.store.sparql.query(GRAPH_IMPORTS_LIST_SPARQL)
        for result in results:
            graph_import = GraphImport(
                from_graph=str(result.from_graph),  # type: ignore[union-attr]
                to_graph=str(result.to_graph),  # type: ignore[union-attr]
            )
            items[graph_import.get_id()] = graph_import
        self._dict = items

    def _create_item(self, item: GraphImport, configuration: GraphImportsCreateConfig | None = None) -> None:
        """Create (add) a new graph import"""
        _ = configuration
        if item.from_graph not in self._client.graphs:
            raise RepositoryModificationError(f"Graph does not exist: {item.from_graph} (from_graph).")
        if item.to_graph not in self._client.graphs:
            raise RepositoryModificationError(f"Graph does not exist: {item.to_graph} (to_graph).")
        query = GRAPH_IMPORTS_CREATE_SPARQL.format(from_graph=item.from_graph, to_graph=item.to_graph)
        self._client.store.sparql.update(query)

    def _delete_item(self, key: str, configuration: GraphImportsDeleteConfig | None = None) -> None:
        """Delete a graph import"""
        _ = configuration
        from_graph, to_graph = key.split("::::", maxsplit=2)
        query = GRAPH_IMPORTS_DELETE_SPARQL.format(from_graph=from_graph, to_graph=to_graph)
        self._client.store.sparql.update(query)
