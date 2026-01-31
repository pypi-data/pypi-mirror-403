"""RDF graph models for Corporate Memory knowledge graphs.

This module defines models for representing RDF graphs in Corporate Memory's
DataPlatform (explore) environment. Graphs contain semantic data and are
the primary storage units for knowledge graphs.

The Graph model includes metadata about graph permissions, assigned semantic
classes, and access control, providing the foundation for graph-based
operations in the explore APIs.
"""

from pydantic import Field

from cmem_client.models.base import Model, ReadRepositoryItem


class Graph(Model, ReadRepositoryItem):
    """A graph"""

    iri: str
    writeable: bool
    assigned_classes: list[str] = Field(alias="assignedClasses")

    def get_id(self) -> str:
        """Get the IRI of the graph"""
        return self.iri
