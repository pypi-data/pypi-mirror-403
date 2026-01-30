"""Workflow repository"""

from __future__ import annotations

import time
from typing import TYPE_CHECKING

from httpx import HTTPError
from pydantic import TypeAdapter

from cmem_client.exceptions import WorkflowExecutionError, WorkflowReadError

if TYPE_CHECKING:
    from cmem_client.client import Client

from cmem_client.models.workflow import ACTIVITY_NAME, Workflow, WorkflowStatus
from cmem_client.repositories.base.abc import RepositoryConfig
from cmem_client.repositories.base.plain_list import PlainListRepository


class WorkflowsRepository(PlainListRepository):
    """Repository for managing workflows.

    This repository manages workflows in Corporate Memory.
    """

    _dict: dict[str, Workflow]
    _client: Client
    _config = RepositoryConfig(
        component="build",
        fetch_data_path="api/workflow/info",
        fetch_data_adapter=TypeAdapter(list[Workflow]),
    )

    def __getitem__(self, key: str) -> Workflow:
        """Get workflow by ID and inject client"""
        workflow: Workflow = super().__getitem__(key)
        workflow.set_client(self._client)
        return workflow

    def execute(self, workflow_id: str, activity_name: ACTIVITY_NAME = "ExecuteDefaultWorkflow") -> None:
        """Execute the workflow

        Executing the workflow with this command does not wait for the workflow to be finished.

        Args:
            workflow_id: The workflow to execute (in the form of 'project_id:workflow_id')
            activity_name: Name of the activity

        Raises:
            BaseError: Raised if the workflow execution failed.
            WorkflowExecutionError: Raised if the workflow execution failed.
        """
        project_id, workflow_name = workflow_id.split(":")
        url = (
            self._client.config.url_build_api
            / "workspace/projects"
            / project_id
            / "tasks"
            / workflow_name
            / "activities"
            / activity_name
            / "start"
        )

        try:
            response = self._client.http.post(url)
            response.raise_for_status()
        except HTTPError as e:
            raise WorkflowExecutionError(f"Workflow '{workflow_id}' could not be executed.") from e

    def execute_wait_for_completion(
        self, workflow_id: str, activity_name: ACTIVITY_NAME = "ExecuteDefaultWorkflow", sleep_time: int = 1
    ) -> None:
        """Execute the workflow waiting for completion

        Executing the workflow with this command does wait for the workflow to be finished.

        Args:
            workflow_id: The workflow to execute (in the form of 'project_id:workflow_id')
            activity_name: Activity name. Defaults to "ExecuteDefaultWorkflow".
            sleep_time: Sleep time in seconds for fetching status of the running workflow. Defaults to 1.

        Raises:
            BaseError: If the client is not set.
            WorkflowExecutionError: If workflow execution failed.
        """
        project_id, workflow_name = workflow_id.split(":")
        url = (
            self._client.config.url_build_api
            / "workspace/projects"
            / project_id
            / "tasks"
            / workflow_name
            / "activities"
            / activity_name
            / "start"
        )

        try:
            self._client.http.post(url)
        except HTTPError as e:
            raise WorkflowExecutionError(f"Workflow '{workflow_id}' could not be executed.") from e

        while True:
            status = self.get_status(workflow_id)
            if not status.is_running:
                break
            time.sleep(sleep_time)

    def get_status(self, workflow_id: str, activity_name: ACTIVITY_NAME = "ExecuteDefaultWorkflow") -> WorkflowStatus:
        """Get the status of the workflow execution.

        Args:
            workflow_id: The workflow to get the status from (in the form of 'project_id:workflow_id')
            activity_name: Name of the activity to check status for. Defaults to "ExecuteDefaultWorkflow".

        Returns:
            WorkflowStatus: The current status of the workflow execution.

        Raises:
            BaseError: If client is not set.
            WorkflowReadError: If the status fetch request fails.
        """
        project_id, workflow_name = workflow_id.split(":")
        url = (
            self._client.config.url_build_api
            / "workspace/projects"
            / project_id
            / "tasks"
            / workflow_name
            / "activities"
            / activity_name
            / "status"
        )

        try:
            response = self._client.http.get(url=url)
            response.raise_for_status()
        except HTTPError as e:
            raise WorkflowReadError(f"Workflow status of '{workflow_id}' could not be read.") from e

        return WorkflowStatus(**response.json())
