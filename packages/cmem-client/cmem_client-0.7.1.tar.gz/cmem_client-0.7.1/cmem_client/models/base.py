"""Base model classes for all cmem_client data models.

This module provides the foundational model classes that all other models
inherit from, establishing common patterns for data validation, serialization,
and repository interactions.

The Model class serves as the base for all Pydantic models in the library,
while ReadRepositoryItem provides an additional interface for entities that
can be retrieved from repositories and have identifiable IDs.
"""

from abc import ABC, abstractmethod

from pydantic import BaseModel, ConfigDict


class Model(BaseModel):
    """Base model for all cmem-client models."""

    model_config = ConfigDict(extra="allow")


class ReadRepositoryItem(BaseModel, ABC):
    """Abstract base class for items of a read repository"""

    model_config = ConfigDict(extra="allow")

    @abstractmethod
    def get_id(self) -> str:
        """Get the id of the item."""
