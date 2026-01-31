"""Pydantic models for n8n Workflows."""

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator


class Position(BaseModel):
    """Node position in the workflow canvas."""

    model_config = ConfigDict(extra="allow")

    x: float = Field(..., description="X coordinate")
    y: float = Field(..., description="Y coordinate")


class NodeParameters(BaseModel):
    """Node parameters configuration."""

    model_config = ConfigDict(extra="allow")

    # Allow any parameters since each node type has different params
    def __init__(self, **data: Any) -> None:
        super().__init__(**data)


class Node(BaseModel):
    """Represents a single node in an n8n workflow."""

    model_config = ConfigDict(extra="allow")

    name: str = Field(..., description="Unique name of the node")
    type: str = Field(..., description="Node type (e.g., n8n-nodes-base.start)")
    position: List[float] = Field(..., description="[x, y] coordinates")
    parameters: Dict[str, Any] = Field(default_factory=dict, description="Node configuration")
    type_version: Optional[float] = Field(
        None, alias="typeVersion", description="Node type version"
    )
    credentials: Optional[Dict[str, Any]] = Field(None, description="Node credentials")
    disabled: Optional[bool] = Field(False, description="Whether node is disabled")


class Connection(BaseModel):
    """Represents connections between nodes."""

    model_config = ConfigDict(extra="allow")

    # n8n uses a complex nested structure for connections
    # Example: {"Node1": {"main": [[{"node": "Node2", "type": "main", "index": 0}]]}}


class Settings(BaseModel):
    """Workflow settings."""

    model_config = ConfigDict(extra="allow")

    save_data_error_execution: Optional[str] = Field(
        None, alias="saveDataErrorExecution", description="Save data on error"
    )
    save_data_success_execution: Optional[str] = Field(
        None, alias="saveDataSuccessExecution", description="Save data on success"
    )
    save_manual_executions: Optional[bool] = Field(
        None, alias="saveManualExecutions", description="Save manual executions"
    )
    timezone: Optional[str] = Field(None, description="Workflow timezone")
    execution_timeout: Optional[int] = Field(
        None, alias="executionTimeout", description="Execution timeout in seconds"
    )


class StaticData(BaseModel):
    """Static data stored with the workflow."""

    model_config = ConfigDict(extra="allow")


class Workflow(BaseModel):
    """Complete n8n Workflow model."""

    model_config = ConfigDict(extra="allow", populate_by_name=True)

    id: Optional[str] = Field(None, description="Workflow ID (assigned by n8n)")
    name: str = Field(..., description="Workflow name")
    active: bool = Field(False, description="Whether workflow is active")
    nodes: List[Node] = Field(..., description="List of workflow nodes")
    connections: Dict[str, Any] = Field(
        default_factory=dict, description="Node connections mapping"
    )
    settings: Optional[Settings] = Field(None, description="Workflow settings")
    static_data: Optional[Dict[str, Any]] = Field(
        None, alias="staticData", description="Static workflow data"
    )
    tags: Optional[List[str]] = Field(None, description="Workflow tags")
    created_at: Optional[datetime] = Field(
        None, alias="createdAt", description="Creation timestamp"
    )
    updated_at: Optional[datetime] = Field(
        None, alias="updatedAt", description="Last update timestamp"
    )

    @field_validator("settings", mode="before")
    @classmethod
    def ensure_settings(cls, v: Any) -> Settings:
        """Ensure settings is always a Settings object, never None."""
        if v is None:
            return Settings()
        if isinstance(v, dict):
            return Settings(**v)
        return v

    def to_json_dict(self, for_create: bool = True) -> Dict[str, Any]:
        """
        Convert to JSON dict for API requests.

        Args:
            for_create: If True, for creating workflows (excludes 'active').
                       If False, for updating workflows (also excludes 'active').

        Note:
            The 'active' field cannot be changed via create/update API.
            Use activate() and deactivate() methods instead.

        Returns:
            Dictionary ready for n8n API
        """
        # Only include fields that n8n accepts in API requests
        # Note: 'active' and 'tags' are excluded because they are read-only
        allowed_fields = {"name", "nodes", "connections", "settings", "staticData"}

        # Get all data with aliases, excluding None values
        data = self.model_dump(
            by_alias=True, exclude_none=True, mode="json", include=allowed_fields
        )

        # Ensure settings is always present (required by n8n)
        if "settings" not in data:
            data["settings"] = {}

        # Clean nodes - remove None values and read-only fields
        if "nodes" in data and isinstance(data["nodes"], list):
            cleaned_nodes = []
            for node in data["nodes"]:
                if isinstance(node, dict):
                    # Remove node-specific read-only fields
                    node.pop("id", None)
                    node.pop("webhookId", None)
                    node.pop("notesInFlow", None)
                    node.pop("notes", None)
                    node.pop("executeOnce", None)
                    node.pop("retryOnFail", None)
                    node.pop("maxTries", None)
                    node.pop("waitBetweenTries", None)
                    node.pop("onError", None)

                    # Remove None values from node
                    cleaned_node = {k: v for k, v in node.items() if v is not None}
                    cleaned_nodes.append(cleaned_node)
            data["nodes"] = cleaned_nodes

        return data
