"""Workflow API operations."""

from typing import Any, Dict, List, Optional

import httpx

from ..exceptions import N8NAPIError, N8NNotFoundError, N8NValidationError
from ..models.workflow import Workflow


class WorkflowAPI:
    """Handles all workflow-related API operations."""

    def __init__(self, client: httpx.AsyncClient) -> None:
        self.client = client

    async def list(
        self,
        active: Optional[bool] = None,
        tags: Optional[List[str]] = None,
    ) -> List[Workflow]:
        """
        List all workflows.

        Args:
            active: Filter by active status
            tags: Filter by tags

        Returns:
            List of Workflow objects
        """
        params: Dict[str, Any] = {}
        if active is not None:
            params["active"] = str(active).lower()
        if tags:
            params["tags"] = ",".join(tags)

        try:
            response = await self.client.get("/workflows", params=params)
            response.raise_for_status()
            data = response.json()

            # n8n returns {"data": [...]} structure
            workflows_data = data.get("data", [])
            return [Workflow(**wf) for wf in workflows_data]

        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                raise N8NNotFoundError(
                    "Workflows endpoint not found", details={"url": str(e.request.url)}
                )
            raise N8NAPIError(
                f"Failed to list workflows: {e}",
                status_code=e.response.status_code,
                response=e.response.json() if e.response.content else None,
            )

    async def get(self, workflow_id: str) -> Workflow:
        """
        Get a specific workflow by ID.

        Args:
            workflow_id: Workflow ID

        Returns:
            Workflow object
        """
        try:
            response = await self.client.get(f"/workflows/{workflow_id}")
            response.raise_for_status()
            data = response.json()
            return Workflow(**data)

        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                raise N8NNotFoundError(
                    f"Workflow {workflow_id} not found",
                    details={"workflow_id": workflow_id},
                )
            raise N8NAPIError(
                f"Failed to get workflow: {e}",
                status_code=e.response.status_code,
                response=e.response.json() if e.response.content else None,
            )

    async def create(self, workflow: Workflow) -> Workflow:
        """
        Create a new workflow.

        Args:
            workflow: Workflow object to create

        Returns:
            Created Workflow with ID assigned
        """
        try:
            payload = workflow.to_json_dict(for_create=True)
            response = await self.client.post("/workflows", json=payload)
            response.raise_for_status()
            data = response.json()
            return Workflow(**data)

        except httpx.HTTPStatusError as e:
            if e.response.status_code == 400:
                raise N8NValidationError(
                    f"Invalid workflow data: {e}",
                    details={"response": e.response.json() if e.response.content else None},
                )
            raise N8NAPIError(
                f"Failed to create workflow: {e}",
                status_code=e.response.status_code,
                response=e.response.json() if e.response.content else None,
            )

    async def create_from_json(self, workflow_data: Dict[str, Any]) -> Workflow:
        """
        Create a workflow from a JSON dict.

        Args:
            workflow_data: Raw workflow JSON data

        Returns:
            Created Workflow
        """
        workflow = Workflow(**workflow_data)
        return await self.create(workflow)

    async def update(self, workflow_id: str, workflow: Workflow) -> Workflow:
        """
        Update an existing workflow.

        Args:
            workflow_id: Workflow ID to update
            workflow: Updated workflow data

        Returns:
            Updated Workflow
        """
        try:
            payload = workflow.to_json_dict(for_create=False)
            # n8n uses PUT instead of PATCH
            response = await self.client.put(f"/workflows/{workflow_id}", json=payload)
            response.raise_for_status()
            data = response.json()
            return Workflow(**data)

        except httpx.HTTPStatusError as e:
            error_detail = None
            try:
                error_detail = e.response.json()
            except Exception:
                error_detail = e.response.text

            if e.response.status_code == 404:
                raise N8NNotFoundError(
                    f"Workflow {workflow_id} not found",
                    details={"workflow_id": workflow_id},
                )
            if e.response.status_code == 400:
                raise N8NValidationError(
                    f"Invalid workflow data: {error_detail}",
                    details={"response": error_detail, "payload": payload},
                )
            raise N8NAPIError(
                f"Failed to update workflow: {e}",
                status_code=e.response.status_code,
                response=error_detail,
            )

    async def delete(self, workflow_id: str) -> bool:
        """
        Delete a workflow.

        Args:
            workflow_id: Workflow ID to delete

        Returns:
            True if deleted successfully
        """
        try:
            response = await self.client.delete(f"/workflows/{workflow_id}")
            response.raise_for_status()
            return True

        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                raise N8NNotFoundError(
                    f"Workflow {workflow_id} not found",
                    details={"workflow_id": workflow_id},
                )
            raise N8NAPIError(
                f"Failed to delete workflow: {e}",
                status_code=e.response.status_code,
                response=e.response.json() if e.response.content else None,
            )

    async def activate(self, workflow_id: str) -> Workflow:
        """
        Activate a workflow.

        Args:
            workflow_id: Workflow ID to activate

        Returns:
            Updated Workflow with active=True
        """
        workflow = await self.get(workflow_id)
        workflow.active = True
        return await self.update(workflow_id, workflow)

    async def deactivate(self, workflow_id: str) -> Workflow:
        """
        Deactivate a workflow.

        Args:
            workflow_id: Workflow ID to deactivate

        Returns:
            Updated Workflow with active=False
        """
        workflow = await self.get(workflow_id)
        workflow.active = False
        return await self.update(workflow_id, workflow)
