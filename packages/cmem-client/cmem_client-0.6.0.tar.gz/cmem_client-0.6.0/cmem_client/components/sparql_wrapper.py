"""SPARQL Wrapper for eccenca Corporate Memory"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from rdflib.plugins.stores.sparqlconnector import SPARQLConnector

from cmem_client.logging_utils import log_method

if TYPE_CHECKING:
    from rdflib.query import Result

    from cmem_client.client import Client


class SPARQLWrapper(SPARQLConnector):
    """Sparql wrapper class"""

    def __init__(self, sparql_endpoint: str, update_endpoint: str, client: Client) -> None:
        self._client = client

        access_token = client.auth.get_access_token()
        headers = {"Authorization": f"Bearer {access_token}"}

        super().__init__(
            query_endpoint=sparql_endpoint,
            update_endpoint=update_endpoint,
            headers=headers,
            method="POST",
        )
        self.logger = logging.getLogger(f"{self._client.logger.name}.{self.__class__.__name__}")

    @log_method
    def query(
        self,
        query: str,
        default_graph: str | None = None,
        named_graph: str | None = None,
    ) -> Result:
        """Query a SPARQL endpoint. This method overwrites the original for logging."""
        return super().query(query, default_graph=default_graph, named_graph=named_graph)

    @log_method
    def update(
        self,
        query: str,
        default_graph: str | None = None,
        named_graph: str | None = None,
    ) -> None:
        """Perform update SPARQL query. This method overwrites the original for logging."""
        return super().update(query, default_graph=default_graph, named_graph=named_graph)
