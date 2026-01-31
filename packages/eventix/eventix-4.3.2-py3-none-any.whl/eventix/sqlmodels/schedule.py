from __future__ import annotations

import datetime
import uuid
from typing import Any, List, Optional

from pydantic import Field
from sqlmodel import Column, DateTime, JSON, SQLModel
from sqlalchemy.sql import func


class EventixSchedule(SQLModel, table=True):
    __tablename__ = "eventix_schedule"

    # Primary key
    id: Optional[int] = Field(default=None, primary_key=True)
    uid: str = Field(default_factory=lambda: str(uuid.uuid4()), unique=True, index=True)

    # Schedule identity
    name: Optional[str] = Field(default=None, index=True)
    task: str = Field(index=True)

    # Schedule configuration
    schedule: str = Field()  # cron expression
    args: List[Any] = Field(default_factory=list, sa_column=Column(JSON))
    kwargs: dict = Field(default_factory=dict, sa_column=Column(JSON))
    priority: int = Field(default=0)

    # Schedule tracking
    last_schedule: Optional[datetime.datetime] = Field(
        default=None, sa_column=Column(DateTime(timezone=True), nullable=True)
    )
    next_schedule: Optional[datetime.datetime] = Field(
        default=None, sa_column=Column(DateTime(timezone=True), nullable=True, index=True)
    )

    # Audit
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

    class Config:
        validate_assignment = True
