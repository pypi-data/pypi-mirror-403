"""Custom exception classes for the cmem_client package.

This module defines all custom exceptions used throughout the cmem_client library,
providing specific error types for different failure scenarios such as authentication,
configuration, and repository operations.
"""


class BaseError(Exception):
    """Base exception for all cmem_client exceptions."""


class ClientNoAuthProviderError(BaseError):
    """Exception raised when no auth provider is given but needed."""


class ClientEnvConfigError(BaseError):
    """Exception raised when an environment key is missing."""


class RepositoryItemNotFoundError(BaseError):
    """Exception raised when a specific item is missing in a repository."""


class RepositoryConfigError(BaseError):
    """Exception raised when a repository configuration is invalid."""


class RepositoryModificationError(BaseError):
    """Exception raised when a repository modification failed or is invalid."""


class RepositoryReadError(BaseError):
    """Exception raised when a repository read operation failed or is invalid."""


class MarketplaceReadError(BaseError):
    """Exception raised when a marketplace read operation failed or is invalid."""


class MarketplaceWriteError(BaseError):
    """Exception raised when a marketplace write operation failed or is invalid."""


class WorkflowReadError(BaseError):
    """Exception raised when a workflow read operation failed or is invalid."""


class WorkflowExecutionError(BaseError):
    """Exception raised when a workflow execution operation failed or is invalid."""


class GraphImportError(RepositoryModificationError):
    """Exception raised when a vocabulary import operation fails."""


class GraphExportError(BaseError):
    """Exception raised when a vocabulary export operation fails."""


class ProjectImportError(RepositoryModificationError):
    """Exception raised when a project import operation fails."""


class ProjectExportError(RepositoryReadError):
    """Exception raised when a project export operation fails."""


class PythonPackageImportError(RepositoryModificationError):
    """Exception raised when a python plugin import fails."""


class MarketplacePackagesImportError(RepositoryModificationError):
    """Exception raised when a marketplace package installation fails."""


class MarketplacePackagesDeleteError(RepositoryModificationError):
    """Exception raised when a marketplace package deletion fails."""


class MarketplacePackagesExportError(BaseError):
    """Exception raised when a marketplace packages export fails."""


class FilesImportError(RepositoryModificationError):
    """Exception raised when a file import fails."""


class FilesDeleteError(RepositoryModificationError):
    """Exception raised when a file import fails."""


class FilesExportError(RepositoryModificationError):
    """Exception raised when a file export fails."""
