"""Data access layer implementing the repository pattern for Corporate Memory resources.

This package provides repository classes for managing different types of Corporate Memory
entities through a consistent interface. Repositories handle data fetching, caching,
CRUD operations, and API communication for various resource types.

Key repository categories:
- Resource repositories: Projects, datasets, graphs, access conditions
- Base classes: Common functionality and abstract base classes
- Protocols: Interface definitions for repository operations

Repositories follow the repository pattern, providing an abstraction layer between
the business logic and the Corporate Memory APIs, with support for both DataIntegration
(build) and DataPlatform (explore) endpoints.
"""
