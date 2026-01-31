"""Execution API operations."""

import asyncio
from typing import Any, Dict, List, Optional

import httpx

from ..exceptions import N8NAPIError, N8NNotFoundError, N8NTimeoutError
from ..models.execution import Execution, ExecutionStatus


class ExecutionAPI:
    """Handles all execution-related API operations."""

    def __init__(
        self,
        client: httpx.AsyncClient,
        poll_interval: int = 2,
        max_poll_timeout: int = 300,
    ) -> None:
        self.client = client
        self.poll_interval = poll_interval
        self.max_poll_timeout = max_poll_timeout

    async def list(
        self,
        workflow_id: Optional[str] = None,
        limit: int = 100,
        status: Optional[ExecutionStatus] = None,
    ) -> List[Execution]:
        """
        List executions.

        Args:
            workflow_id: Filter by workflow ID
            limit: Maximum number of results
            status: Filter by execution status

        Returns:
            List of Execution objects
        """
        params: Dict[str, Any] = {"limit": limit}
        if workflow_id:
            params["workflowId"] = workflow_id
        if status:
            params["status"] = status.value

        try:
            response = await self.client.get("/executions", params=params)
            response.raise_for_status()
            data = response.json()

            # n8n returns {"data": [...]} structure
            executions_data = data.get("data", [])
            return [Execution(**ex) for ex in executions_data]

        except httpx.HTTPStatusError as e:
            raise N8NAPIError(
                f"Failed to list executions: {e}",
                status_code=e.response.status_code,
                response=e.response.json() if e.response.content else None,
            )

    async def get(self, execution_id: str, include_data: bool = True) -> Execution:
        """
        Get a specific execution by ID.

        Args:
            execution_id: Execution ID
            include_data: Include execution data in response

        Returns:
            Execution object
        """
        params = {}
        if not include_data:
            params["includeData"] = "false"

        try:
            response = await self.client.get(f"/executions/{execution_id}", params=params)
            response.raise_for_status()
            data = response.json()
            return Execution(**data)

        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                raise N8NNotFoundError(
                    f"Execution {execution_id} not found",
                    details={"execution_id": execution_id},
                )
            raise N8NAPIError(
                f"Failed to get execution: {e}",
                status_code=e.response.status_code,
                response=e.response.json() if e.response.content else None,
            )

    async def delete(self, execution_id: str) -> bool:
        """
        Delete an execution.

        Args:
            execution_id: Execution ID to delete

        Returns:
            True if deleted successfully
        """
        try:
            response = await self.client.delete(f"/executions/{execution_id}")
            response.raise_for_status()
            return True

        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                raise N8NNotFoundError(
                    f"Execution {execution_id} not found",
                    details={"execution_id": execution_id},
                )
            raise N8NAPIError(
                f"Failed to delete execution: {e}",
                status_code=e.response.status_code,
                response=e.response.json() if e.response.content else None,
            )

    async def retry(self, execution_id: str) -> Execution:
        """
        Retry a failed execution.

        Args:
            execution_id: Execution ID to retry

        Returns:
            New Execution object for the retry
        """
        try:
            response = await self.client.post(f"/executions/{execution_id}/retry")
            response.raise_for_status()
            data = response.json()
            return Execution(**data)

        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                raise N8NNotFoundError(
                    f"Execution {execution_id} not found",
                    details={"execution_id": execution_id},
                )
            raise N8NAPIError(
                f"Failed to retry execution: {e}",
                status_code=e.response.status_code,
                response=e.response.json() if e.response.content else None,
            )

    async def trigger_workflow(
        self,
        workflow_id: str,
        input_data: Optional[Dict[str, Any]] = None,
    ) -> Execution:
        """
        Manually trigger a workflow execution.

        Args:
            workflow_id: Workflow ID to execute
            input_data: Optional input data for the workflow

        Returns:
            Execution object
        """
        payload = {}
        if input_data:
            payload["data"] = input_data

        try:
            # Use POST to /workflows/{id}/execute endpoint
            response = await self.client.post(
                f"/workflows/{workflow_id}/execute",
                json=payload if payload else None,
            )
            response.raise_for_status()
            data = response.json()
            return Execution(**data)

        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                raise N8NNotFoundError(
                    f"Workflow {workflow_id} not found",
                    details={"workflow_id": workflow_id},
                )
            raise N8NAPIError(
                f"Failed to trigger workflow: {e}",
                status_code=e.response.status_code,
                response=e.response.json() if e.response.content else None,
            )

    async def wait_for_execution(
        self,
        execution_id: str,
        timeout: Optional[int] = None,
        poll_interval: Optional[int] = None,
    ) -> Execution:
        """
        Wait for an execution to complete (smart polling).

        Args:
            execution_id: Execution ID to monitor
            timeout: Maximum time to wait in seconds (uses max_poll_timeout if not specified)
            poll_interval: Seconds between polls (uses instance default if not specified)

        Returns:
            Completed Execution object

        Raises:
            N8NTimeoutError: If execution doesn't complete within timeout
        """
        timeout = timeout or self.max_poll_timeout
        poll_interval = poll_interval or self.poll_interval

        start_time = asyncio.get_event_loop().time()

        while True:
            execution = await self.get(execution_id, include_data=True)

            # Check if execution is finished
            if not execution.is_running:
                return execution

            # Check timeout
            elapsed = asyncio.get_event_loop().time() - start_time
            if elapsed >= timeout:
                raise N8NTimeoutError(
                    f"Execution {execution_id} did not complete within {timeout}s",
                    details={"execution_id": execution_id, "timeout": timeout},
                )

            # Wait before next poll
            await asyncio.sleep(poll_interval)

    async def run_and_wait(
        self,
        workflow_id: str,
        input_data: Optional[Dict[str, Any]] = None,
        timeout: Optional[int] = None,
    ) -> Execution:
        """
        Trigger a workflow and wait for it to complete (convenience method).

        Args:
            workflow_id: Workflow ID to execute
            input_data: Optional input data for the workflow
            timeout: Maximum time to wait in seconds

        Returns:
            Completed Execution object
        """
        execution = await self.trigger_workflow(workflow_id, input_data)
        return await self.wait_for_execution(execution.id, timeout=timeout)
