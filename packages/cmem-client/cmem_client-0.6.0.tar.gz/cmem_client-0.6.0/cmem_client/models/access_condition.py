"""Access control and authorization models for Corporate Memory.

This module defines models for managing access conditions in Corporate Memory,
which control user and group permissions for graphs, actions, and other resources.
Access conditions form the foundation of Corporate Memory's authorization system.

The AccessCondition model supports both static permissions (defined at creation)
and dynamic permissions (computed via SPARQL queries), providing flexible
access control patterns for different organizational needs.

Access conditions can grant various permissions including graph read/write access,
action execution rights, and management permissions for other access conditions.
"""

from datetime import datetime

from pydantic import Field

from cmem_client.models.base import Model, ReadRepositoryItem
from cmem_client.repositories.base.paged_list import PageDescription

NS_AC = "http://eccenca.com/ac/"
NS_ACTION = "https://vocab.eccenca.com/auth/Action/"


class AccessCondition(Model, ReadRepositoryItem):
    """An access condition"""

    iri: str = Field(description="The IRI of the access condition.", examples=[f"{NS_AC}my-condition"])
    name: str = Field(description="A short name to identify the access condition.", examples=["My Access Condition"])
    comment: str | None = Field(
        default=None,
        description="An optional description to provide more context information of the access condition.",
        examples=["This condition is of me ..."],
    )
    requires_account: str | None = Field(
        alias="requiresAccount",
        default=None,
        description="A specific account IRI required by the access condition.",
        examples=["http://eccenca.com/admin"],
    )
    requires_group: list[str] = Field(
        alias="requiresGroup",
        default=[],
        description="The groups (IRI) the account must be member of to meet the access condition.",
        examples=[["http://eccenca.com/elds-admins"]],
    )
    readable_graphs: list[str] = Field(
        alias="readableGraphs",
        default=[],
        description="Grants read access to a graph - list of Graph IRIs.",
        examples=[["https://vocab.eccenca.com/shacl/", "https://vocab.eccenca.com/auth/AllGraphs"]],
    )
    writable_graphs: list[str] = Field(
        alias="writableGraphs",
        default=[],
        description="Grants read/write access to a graph - list of Graph IRIs.",
        examples=[["https://vocab.eccenca.com/shacl/", "https://vocab.eccenca.com/auth/AllGraphs"]],
    )
    allowed_actions: list[str] = Field(
        alias="allowedActions",
        default=[],
        description="Grants permission to execute an action - list of Action IRIs.",
        examples=[[f"{NS_ACTION}Build", f"{NS_ACTION}AllActions"]],
    )
    grant_allowed_actions: list[str] = Field(
        alias="grantAllowedActions",
        default=[],
        description="Grants management of conditions granting action allowance for actions matching"
        " the defined pattern.",
        examples=[[f"{NS_ACTION}Build*", "*"]],
    )
    grant_read_patterns: list[str] = Field(
        alias="grantReadPatterns",
        default=[],
        description="Grants management of conditions granting read access on graphs matching the defined pattern.",
        examples=[["https://example.org/*", "*"]],
    )
    grant_write_patterns: list[str] = Field(
        alias="grantWritePatterns",
        default=[],
        description="Grants management of conditions granting write access on graphs matching the defined pattern.",
        examples=[["https://example.org/*", "*"]],
    )
    query: str | None = Field(
        alias="dynamicAccessConditionQuery",
        default=None,
        description="A SPARQL SELECT query which returns the following projection variables: user, group,"
        " readGraph, and writeGraph.",
        examples=[
            """
PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
PREFIX dct: <http://purl.org/dc/terms/>
PREFIX void: <http://rdfs.org/ns/void#>

SELECT  ?user ?group ?readGraph ?writeGraph
WHERE
{
  GRAPH ?writeGraph {
    ?writeGraph rdf:type void:Dataset .
    ?writeGraph dct:creator ?user .
  }
}
        """
        ],
    )
    creator: str | None = Field(
        default=None,
        description="The IRI of the account which created the access condition.",
        examples=["http://eccenca.com/admin"],
    )
    created: datetime | None = Field(
        default=None, description="The time when the access condition was created.", examples=["2025-09-12T09:09:48Z"]
    )

    def get_id(self) -> str:
        """Get the IRI of the access condition"""
        return self.iri

    def set_iri(self, local_name: str) -> None:
        """Set the IRI of the access condition based on a new local name

        this just adds the namespace prefix
        """
        self.iri = f"{NS_AC}{local_name}"

    def get_create_request(self) -> dict:
        """Create a CreateAccessConditionRequest dict

        This object is used to create new access condition.
        """
        if not self.get_id().startswith(NS_AC):
            raise ValueError(f"Access condition ID must start with '{NS_AC}'")
        data = self.model_dump(by_alias=True)
        data["staticId"] = self.get_id().replace(NS_AC, "")
        for key in ["iri", "creator", "created"]:
            # remove not needed keys if present
            if key in data:
                del data[key]
        return data


class AccessConditionResultSet(Model):
    """An access condition result set"""

    content: list[AccessCondition]
    page: PageDescription
