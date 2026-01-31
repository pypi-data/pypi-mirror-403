"""Credential API operations."""

from typing import Any, Dict, List, Optional

import httpx

from ..exceptions import N8NAPIError, N8NNotFoundError, N8NValidationError
from ..models.credential import Credential


class CredentialAPI:
    """Handles all credential-related API operations."""

    def __init__(self, client: httpx.AsyncClient) -> None:
        self.client = client

    async def list(self, credential_type: Optional[str] = None) -> List[Credential]:
        """
        List all credentials.

        Args:
            credential_type: Filter by credential type

        Returns:
            List of Credential objects
        """
        params: Dict[str, Any] = {}
        if credential_type:
            params["type"] = credential_type

        try:
            response = await self.client.get("/credentials", params=params)
            response.raise_for_status()
            data = response.json()

            # n8n returns {"data": [...]} structure
            credentials_data = data.get("data", [])
            return [Credential(**cred) for cred in credentials_data]

        except httpx.HTTPStatusError as e:
            raise N8NAPIError(
                f"Failed to list credentials: {e}",
                status_code=e.response.status_code,
                response=e.response.json() if e.response.content else None,
            )

    async def get(self, credential_id: str) -> Credential:
        """
        Get a specific credential by ID.

        Note: Sensitive data is usually encrypted/masked by n8n.

        Args:
            credential_id: Credential ID

        Returns:
            Credential object
        """
        try:
            response = await self.client.get(f"/credentials/{credential_id}")
            response.raise_for_status()
            data = response.json()
            return Credential(**data)

        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                raise N8NNotFoundError(
                    f"Credential {credential_id} not found",
                    details={"credential_id": credential_id},
                )
            raise N8NAPIError(
                f"Failed to get credential: {e}",
                status_code=e.response.status_code,
                response=e.response.json() if e.response.content else None,
            )

    async def create(self, credential: Credential) -> Credential:
        """
        Create a new credential.

        Args:
            credential: Credential object to create

        Returns:
            Created Credential with ID assigned
        """
        try:
            payload = credential.to_json_dict()
            response = await self.client.post("/credentials", json=payload)
            response.raise_for_status()
            data = response.json()
            return Credential(**data)

        except httpx.HTTPStatusError as e:
            if e.response.status_code == 400:
                raise N8NValidationError(
                    f"Invalid credential data: {e}",
                    details={"response": e.response.json() if e.response.content else None},
                )
            raise N8NAPIError(
                f"Failed to create credential: {e}",
                status_code=e.response.status_code,
                response=e.response.json() if e.response.content else None,
            )

    async def update(self, credential_id: str, credential: Credential) -> Credential:
        """
        Update an existing credential.

        Args:
            credential_id: Credential ID to update
            credential: Updated credential data

        Returns:
            Updated Credential
        """
        try:
            payload = credential.to_json_dict()
            response = await self.client.patch(f"/credentials/{credential_id}", json=payload)
            response.raise_for_status()
            data = response.json()
            return Credential(**data)

        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                raise N8NNotFoundError(
                    f"Credential {credential_id} not found",
                    details={"credential_id": credential_id},
                )
            if e.response.status_code == 400:
                raise N8NValidationError(
                    f"Invalid credential data: {e}",
                    details={"response": e.response.json() if e.response.content else None},
                )
            raise N8NAPIError(
                f"Failed to update credential: {e}",
                status_code=e.response.status_code,
                response=e.response.json() if e.response.content else None,
            )

    async def delete(self, credential_id: str) -> bool:
        """
        Delete a credential.

        Args:
            credential_id: Credential ID to delete

        Returns:
            True if deleted successfully
        """
        try:
            response = await self.client.delete(f"/credentials/{credential_id}")
            response.raise_for_status()
            return True

        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                raise N8NNotFoundError(
                    f"Credential {credential_id} not found",
                    details={"credential_id": credential_id},
                )
            raise N8NAPIError(
                f"Failed to delete credential: {e}",
                status_code=e.response.status_code,
                response=e.response.json() if e.response.content else None,
            )
