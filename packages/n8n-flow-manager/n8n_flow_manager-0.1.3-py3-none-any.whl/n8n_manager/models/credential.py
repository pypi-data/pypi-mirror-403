"""Pydantic models for n8n Credentials."""

from datetime import datetime
from typing import Any, Dict, Optional

from pydantic import BaseModel, ConfigDict, Field


class CredentialType(BaseModel):
    """Credential type information."""

    model_config = ConfigDict(extra="allow")

    name: str = Field(..., description="Credential type name")
    display_name: str = Field(..., alias="displayName", description="Display name")


class Credential(BaseModel):
    """Complete n8n Credential model."""

    model_config = ConfigDict(extra="allow", populate_by_name=True)

    id: Optional[str] = Field(None, description="Credential ID")
    name: str = Field(..., description="Credential name")
    type: str = Field(..., description="Credential type")
    data: Optional[Dict[str, Any]] = Field(None, description="Credential data (encrypted by n8n)")
    nodes_access: Optional[list[Dict[str, str]]] = Field(
        None, alias="nodesAccess", description="Nodes that can access this credential"
    )
    created_at: Optional[datetime] = Field(
        None, alias="createdAt", description="Creation timestamp"
    )
    updated_at: Optional[datetime] = Field(
        None, alias="updatedAt", description="Last update timestamp"
    )

    def to_json_dict(self) -> Dict[str, Any]:
        """Convert to JSON dict for API requests."""
        return self.model_dump(
            by_alias=True, exclude_none=True, exclude={"id", "created_at", "updated_at"}
        )
