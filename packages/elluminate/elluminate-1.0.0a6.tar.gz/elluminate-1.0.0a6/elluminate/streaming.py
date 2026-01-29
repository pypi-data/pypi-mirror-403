"""Server-Sent Events (SSE) streaming support for AsyncClient.

This module provides event schemas and utilities for streaming real-time updates
from long-running operations like experiment generation and batch processing.
"""

from enum import Enum
from typing import Any, Optional

from pydantic import BaseModel, Field

from elluminate.schemas import Experiment


class TaskStatus(str, Enum):
    """Status of a Celery task."""

    PENDING = "PENDING"
    STARTED = "STARTED"
    SUCCESS = "SUCCESS"
    FAILURE = "FAILURE"
    REVOKED = "REVOKED"
    REJECTED = "REJECTED"
    TIMEOUT = "TIMEOUT"  # Emitted when polling exceeds backend time limit (10 hours)


class ExperimentProgress(BaseModel):
    """Progress information for an experiment generation task."""

    responses_generated: int = Field(..., description="Number of responses generated so far")
    responses_rated: int = Field(..., description="Number of responses rated so far")
    total_responses: int = Field(..., description="Total number of responses to generate")

    @property
    def percent_complete(self) -> float:
        """Calculate completion percentage."""
        if self.total_responses == 0:
            return 0.0
        return (self.responses_rated / self.total_responses) * 100.0

    @property
    def generation_complete(self) -> bool:
        """Check if response generation is complete."""
        return self.responses_generated >= self.total_responses

    @property
    def rating_complete(self) -> bool:
        """Check if rating is complete."""
        return self.responses_rated >= self.total_responses


class ExperimentStatusEvent(BaseModel):
    """Event emitted during experiment generation streaming.

    This event is yielded by AsyncClient.stream_experiment() to provide
    real-time updates on experiment progress, logs, and completion.
    """

    status: TaskStatus = Field(..., description="Current task status")
    progress: Optional[ExperimentProgress] = Field(
        None, description="Progress information (available during STARTED)"
    )
    logs_delta: Optional[str] = Field(None, description="New log message since last event (only contains new logs)")
    error_msg: Optional[str] = Field(None, description="Error message (only on FAILURE)")
    result: Optional[Experiment] = Field(None, description="Final experiment with responses (only on SUCCESS)")

    @property
    def is_complete(self) -> bool:
        """Check if this is a terminal event (SUCCESS or FAILURE)."""
        return self.status in {
            TaskStatus.SUCCESS,
            TaskStatus.FAILURE,
            TaskStatus.REVOKED,
            TaskStatus.REJECTED,
            TaskStatus.TIMEOUT,
        }

    @property
    def is_success(self) -> bool:
        """Check if task completed successfully."""
        return self.status == TaskStatus.SUCCESS

    @property
    def is_failure(self) -> bool:
        """Check if task failed."""
        return self.status in {TaskStatus.FAILURE, TaskStatus.REVOKED, TaskStatus.REJECTED, TaskStatus.TIMEOUT}


class BatchProgress(BaseModel):
    """Progress information for batch operations (responses or ratings)."""

    processed: int = Field(..., description="Number of items processed so far")
    total: int = Field(..., description="Total number of items to process")
    failed: int = Field(0, description="Number of failed items")

    @property
    def percent_complete(self) -> float:
        """Calculate completion percentage."""
        if self.total == 0:
            return 0.0
        return (self.processed / self.total) * 100.0

    @property
    def is_complete(self) -> bool:
        """Check if processing is complete."""
        return self.processed >= self.total


class BatchStatusEvent(BaseModel):
    """Event emitted during batch operation streaming.

    Used for both batch response creation and batch rating creation.
    """

    status: TaskStatus = Field(..., description="Current task status")
    progress: Optional[BatchProgress] = Field(None, description="Progress information (available during STARTED)")
    error_msg: Optional[str] = Field(None, description="Error message (only on FAILURE)")
    result: Optional[Any] = Field(None, description="Final result (only on SUCCESS)")

    @property
    def is_complete(self) -> bool:
        """Check if this is a terminal event."""
        return self.status in {
            TaskStatus.SUCCESS,
            TaskStatus.FAILURE,
            TaskStatus.REVOKED,
            TaskStatus.REJECTED,
            TaskStatus.TIMEOUT,
        }

    @property
    def is_success(self) -> bool:
        """Check if task completed successfully."""
        return self.status == TaskStatus.SUCCESS

    @property
    def is_failure(self) -> bool:
        """Check if task failed."""
        return self.status in {TaskStatus.FAILURE, TaskStatus.REVOKED, TaskStatus.REJECTED, TaskStatus.TIMEOUT}
