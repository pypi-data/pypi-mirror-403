"""Converters between Pydantic models and SQLModel database models"""

from eventix.pydantic.task import TEventixTask as PydanticTask
from eventix.sqlmodels.task import EventixTask as SQLTask


def pydantic_to_sqlmodel_task(pydantic_task: PydanticTask) -> SQLTask:
    """Convert Pydantic TEventixTask to SQLModel EventixTask"""
    data = pydantic_task.model_dump(exclude_none=False)

    # Handle id field - SQLModel uses 'id', Pydantic might not have it
    if "id" not in data:
        data["id"] = None

    return SQLTask(**data)


def sqlmodel_to_pydantic_task(sql_task: SQLTask) -> PydanticTask:
    """Convert SQLModel EventixTask to Pydantic TEventixTask"""
    data = sql_task.model_dump()

    # Remove SQLModel-specific fields that Pydantic doesn't need
    data.pop("id", None)

    return PydanticTask(**data)
