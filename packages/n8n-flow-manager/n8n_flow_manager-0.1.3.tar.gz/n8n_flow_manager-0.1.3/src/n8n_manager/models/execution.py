"""Pydantic models for n8n Executions."""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, Optional

from pydantic import BaseModel, ConfigDict, Field


class ExecutionStatus(str, Enum):
    """Possible execution statuses."""

    SUCCESS = "success"
    ERROR = "error"
    RUNNING = "running"
    WAITING = "waiting"
    CANCELED = "canceled"
    CRASHED = "crashed"
    NEW = "new"
    UNKNOWN = "unknown"


class ExecutionMode(str, Enum):
    """Execution modes."""

    MANUAL = "manual"
    TRIGGER = "trigger"
    WEBHOOK = "webhook"
    CLI = "cli"
    ERROR = "error"
    RETRY = "retry"


class ExecutionData(BaseModel):
    """Execution data details."""

    model_config = ConfigDict(extra="allow")

    start_data: Optional[Dict[str, Any]] = Field(
        None, alias="startData", description="Execution start data"
    )
    result_data: Optional[Dict[str, Any]] = Field(
        None, alias="resultData", description="Execution result data"
    )
    execution_data: Optional[Dict[str, Any]] = Field(
        None, alias="executionData", description="Additional execution data"
    )


class Execution(BaseModel):
    """Complete n8n Execution model."""

    model_config = ConfigDict(extra="allow", populate_by_name=True)

    id: str = Field(..., description="Execution ID")
    finished: bool = Field(..., description="Whether execution has finished")
    mode: ExecutionMode = Field(..., description="Execution mode")
    retry_of: Optional[str] = Field(
        None, alias="retryOf", description="Parent execution ID if retry"
    )
    retry_success_id: Optional[str] = Field(
        None, alias="retrySuccessId", description="Successful retry execution ID"
    )
    started_at: Optional[datetime] = Field(None, alias="startedAt", description="Start timestamp")
    stopped_at: Optional[datetime] = Field(None, alias="stoppedAt", description="Stop timestamp")
    workflow_id: str = Field(..., alias="workflowId", description="Associated workflow ID")
    workflow_data: Optional[Dict[str, Any]] = Field(
        None, alias="workflowData", description="Workflow snapshot"
    )
    data: Optional[ExecutionData] = Field(None, description="Execution data")
    status: Optional[ExecutionStatus] = Field(None, description="Execution status")
    waiting_for_webhook: Optional[bool] = Field(
        None, alias="waitingForWebhook", description="Waiting for webhook"
    )

    @property
    def is_running(self) -> bool:
        """Check if execution is currently running."""
        return not self.finished and self.status in [
            ExecutionStatus.RUNNING,
            ExecutionStatus.WAITING,
            ExecutionStatus.NEW,
        ]

    @property
    def is_successful(self) -> bool:
        """Check if execution completed successfully."""
        return self.finished and self.status == ExecutionStatus.SUCCESS

    @property
    def is_failed(self) -> bool:
        """Check if execution failed."""
        return self.finished and self.status in [
            ExecutionStatus.ERROR,
            ExecutionStatus.CRASHED,
        ]
