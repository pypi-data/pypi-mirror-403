from __future__ import annotations

import datetime
import uuid
from typing import Any, Optional

from pydantic import Field
from sqlmodel import Column, DateTime, JSON, SQLModel
from sqlalchemy.sql import func


class EventixEvent(SQLModel, table=True):
    __tablename__ = "eventix_event"

    # Primary key
    id: Optional[int] = Field(default=None, primary_key=True)
    uid: str = Field(default_factory=lambda: str(uuid.uuid4()), unique=True, index=True)

    # Event identity
    name: str = Field(index=True)
    namespace: str = Field(default="default", index=True)

    # Event data
    payload: dict = Field(default_factory=dict, sa_column=Column(JSON))
    timestamp: datetime.datetime = Field(
        default_factory=lambda: datetime.datetime.now(datetime.timezone.utc),
        sa_column=Column(DateTime(timezone=True), nullable=False, index=True),
    )
    priority: int = Field(default=0)

    # Audit
    operator: str = Field(default="unknown")
    created_at: datetime.datetime = Field(
        default_factory=lambda: datetime.datetime.now(datetime.timezone.utc),
        sa_column=Column(DateTime(timezone=True), nullable=False, server_default=func.now()),
    )

    class Config:
        validate_assignment = True


class EventixEventTrigger(SQLModel, table=True):
    __tablename__ = "eventix_event_trigger"

    # Primary key
    id: Optional[int] = Field(default=None, primary_key=True)
    uid: str = Field(default_factory=lambda: str(uuid.uuid4()), unique=True, index=True)

    # Trigger identity
    name: str = Field(unique=True, index=True)
    event_name: str = Field(index=True)
    trigger_type: str = Field(default="default")
    namespace: str = Field(default="default", index=True)

    # Trigger code
    code: Optional[str] = Field(default=None)

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
