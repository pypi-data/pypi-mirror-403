"""Error response models for Corporate Memory API error handling.

This module defines models for parsing and handling error responses from
both the DataIntegration (build) and DataPlatform (explore) APIs. Different
API endpoints return different error response formats, and these models
provide a unified way to handle them.

The Problem model handles DataPlatform API errors, while ErrorResult handles
DataIntegration API errors. Both include methods for generating human-readable
error messages for debugging and user feedback.
"""

from typing import Literal

from pydantic import Field

from cmem_client.models.base import Model


class Violation(Model):
    """A data violation, communicated with a problem"""

    field: str
    message: str


class Problem(Model):
    """A problem, communicated by the server

    This type of response is returned by the explore APIs (DataPlatform)
    """

    type: str
    title: str
    status: int
    details: str = Field(default="")
    violations: list[Violation] = Field(default=[])

    def get_exception_message(self) -> str:
        """Get error message"""
        text = f"{self.title} ({self.status}) - "
        if self.details:
            text += f" {self.details}"
        if len(self.violations) > 0:
            text += f" with {len(self.violations)} violation(s) -"
            for violation in self.violations:
                text += f" {violation.message} ({violation.field})"
        return text


class ErrorResultIssue(Model):
    """An issue listed with an ErrorResult"""

    type: Literal["Error", "Warning", "Info"]
    message: str
    id: str


class ErrorResult(Model):
    """An error result, communicated by the server

    returned by the build APIs (DataIntegration)
    """

    title: str
    detail: str
    issues: list[ErrorResultIssue] | None
