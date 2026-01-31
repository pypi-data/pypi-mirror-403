"""Pydantic data models for Corporate Memory entities.

This package contains all data models used throughout the cmem_client library,
implementing structured data validation and serialization using Pydantic v2.
These models represent various Corporate Memory entities and API responses.

Key model categories:
- Base models: Common base classes and interfaces
- Business entities: Projects, datasets, graphs, access conditions
- Authentication: Token models for OAuth flows
- API responses: Error models and result sets
- Utilities: URL handling and validation

All models inherit from either Model (for general data) or ReadRepositoryItem
(for entities that can be retrieved from repositories).
"""
