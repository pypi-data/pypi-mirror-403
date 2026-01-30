"""Workflow models"""

from __future__ import annotations

from datetime import datetime  # noqa: TC003  # Pydantic needs this at runtime
from typing import TYPE_CHECKING, Literal

from pydantic import Field, PrivateAttr

from cmem_client.exceptions import BaseError

if TYPE_CHECKING:
    from cmem_client.client import Client

from cmem_client.models.base import Model, ReadRepositoryItem

ACTIVITY_NAME = Literal["ExecuteDefaultWorkflow", "ExecuteLocalWorkflow", "ExecuteWorkflowWithPayload"]


class WorkflowStatus(Model):
    """Workflow execution status"""

    status_name: str = Field(description="Status name (Idle, Running, Finished)", alias="statusName")
    concrete_status: str = Field(description="Concrete status (Successful, Failed, Cancelled)", alias="concreteStatus")
    progress: int | None = Field(description="Progress percentage (0-100)")
    failed: bool = Field(description="Whether the workflow has failed")
    message: str = Field(description="Status message")
    last_update_time: int = Field(description="Last update time", alias="lastUpdateTime")
    project: str = Field(description="Project ID")
    task: str = Field(description="Task")
    activity: str = Field(description="Activity")
    activity_label: str = Field(description="Activity label", alias="activityLabel")
    queue_time: datetime | None = Field(default=None, description="Queue time", alias="queueTime")
    start_time: datetime | None = Field(default=None, description="Start time", alias="startTime")
    is_running: bool = Field(description="Whether the workflow is currently running", alias="isRunning")
    runtime: int | None = Field(default=None, description="Runtime")
    cancelled: bool | None = Field(default=None, description="Cancelled")
    exception_message: str | None = Field(default=None, description="Exception message", alias="exceptionMessage")


class Workflow(Model, ReadRepositoryItem):
    """A workflow"""

    _client: Client | None = PrivateAttr(default=None)

    id: str = Field(description="Workflow ID", alias="id")
    label: str = Field(description="Workflow label")
    project_id: str = Field(description="Project ID", alias="projectId")
    project_label: str = Field(description="Project label", alias="projectLabel")
    variable_inputs: list[str] = Field(description="Workflow variable inputs", alias="variableInputs")
    variable_outputs: list[str] = Field(description="Workflow variable outputs", alias="variableOutputs")
    warnings: list[str] = Field(description="Workflow warnings")

    def get_id(self) -> str:
        """Get the workflow ID"""
        return f"{self.project_id}:{self.id}"

    def set_client(self, client: Client) -> None:
        """Set the client for this workflow"""
        self._client = client

    def execute(self, activity_name: ACTIVITY_NAME = "ExecuteDefaultWorkflow") -> None:
        """Execute the workflow"""
        if self._client is None:
            raise BaseError("Client is not set")
        self._client.workflows.execute(self.get_id(), activity_name)

    def execute_wait_for_completion(
        self, activity_name: ACTIVITY_NAME = "ExecuteDefaultWorkflow", sleep_time: int = 1
    ) -> None:
        """Execute the workflow waiting for completion"""
        if self._client is None:
            raise BaseError("Client is not set")
        self._client.workflows.execute_wait_for_completion(self.get_id(), activity_name, sleep_time)

    def get_status(self, activity_name: ACTIVITY_NAME = "ExecuteDefaultWorkflow") -> WorkflowStatus:
        """Get the status of the workflow execution."""
        if self._client is None:
            raise BaseError("Client is not set")
        return self._client.workflows.get_status(self.get_id(), activity_name)
