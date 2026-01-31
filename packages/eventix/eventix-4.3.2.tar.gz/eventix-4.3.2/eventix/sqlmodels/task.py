from __future__ import annotations

import datetime
import uuid
from enum import Enum
from typing import Any, Dict, Optional

from pydantic import Field
from sqlmodel import Column, DateTime, JSON, SQLModel
from sqlalchemy.sql import func


class EventixTaskStatusEnum(str, Enum):
    scheduled = "scheduled"
    processing = "processing"
    done = "done"
    error = "error"
    retry = "retry"


class EventixTask(SQLModel, table=True):
    __tablename__ = "eventix_task"

    # Primary key
    id: Optional[int] = Field(default=None, primary_key=True)
    uid: str = Field(default_factory=lambda: str(uuid.uuid4()), unique=True, index=True)

    # Task identity
    unique_key: Optional[str] = Field(default=None, index=True)
    task: str = Field(index=True)
    namespace: str = Field(default="default", index=True)

    # Scheduling
    eta: datetime.datetime = Field(
        default_factory=lambda: datetime.datetime.now(datetime.timezone.utc),
        sa_column=Column(DateTime(timezone=True), nullable=False, index=True),
    )
    scheduled: datetime.datetime = Field(
        default_factory=lambda: datetime.datetime.now(datetime.timezone.utc),
        sa_column=Column(DateTime(timezone=True), nullable=False),
    )
    status: EventixTaskStatusEnum = Field(default=EventixTaskStatusEnum.scheduled, index=True)
    priority: int = Field(default=0, index=True)

    # Task arguments
    args: list = Field(default_factory=list, sa_column=Column(JSON))
    kwargs: Dict[str, Any] = Field(default_factory=dict, sa_column=Column(JSON))

    # Worker management
    worker_id: Optional[str] = Field(default=None)
    worker_expires: Optional[datetime.datetime] = Field(
        default=None, sa_column=Column(DateTime(timezone=True), nullable=True)
    )

    # Retry configuration
    retry: bool = Field(default=True)
    max_retries: Optional[int] = Field(default=None)
    error_eta_inc: int = Field(default=15)
    error_eta_max: int = Field(default=300)
    store_result: bool = Field(default=True)

    # Result and expiration
    result: Optional[Any] = Field(default=None, sa_column=Column(JSON))
    error_expires: Optional[int] = Field(default=None)
    result_expires: Optional[int] = Field(default=604800)  # 7 days
    expires: Optional[datetime.datetime] = Field(
        default=None, sa_column=Column(DateTime(timezone=True), nullable=True)
    )

    # Audit fields
    operator: str = Field(default="unknown")
    created_at: datetime.datetime = Field(
        default_factory=lambda: datetime.datetime.now(datetime.timezone.utc),
        sa_column=Column(DateTime(timezone=True), nullable=False, server_default=func.now()),
    )
    updated_at: datetime.datetime = Field(
        default_factory=lambda: datetime.datetime.now(datetime.timezone.utc),
        sa_column=Column(
            DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
        ),
    )
    revision: int = Field(default=1)

    def unique_update_from(self, task: "EventixTask"):
        """Update this task from another task with the same unique_key"""
        self.eta = min([task.eta, self.eta])
        self.priority = min([task.priority, self.priority])
        self.args = task.args
        self.kwargs = task.kwargs
        self.status = task.status
        self.error_eta_inc = task.error_eta_inc

    class Config:
        use_enum_values = True
        validate_assignment = True
