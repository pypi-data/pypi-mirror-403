import datetime
import logging
from typing import List, Optional

from sqlalchemy import and_, or_, select, func as sql_func, delete
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from eventix.converters import pydantic_to_sqlmodel_task, sqlmodel_to_pydantic_task
from eventix.database import get_session
from eventix.exceptions import NoTaskFoundForUniqueKey, TaskUniqueKeyNotUnique, WrongTaskStatus
from eventix.functions.relay import RelayManager
from eventix.pydantic.task import TEventixTask, EventixTaskStatusEnum
from eventix.sqlmodels.task import EventixTask as SQLTask, EventixTaskStatusEnum as SQLTaskStatus

log = logging.getLogger(__name__)


def utcnow() -> datetime.datetime:
    """Get current UTC datetime with timezone"""
    return datetime.datetime.now(datetime.timezone.utc)


def task_post(task: TEventixTask) -> TEventixTask:
    """Post a new task or update an existing unique task"""
    # Convert to SQLModel
    sql_task = pydantic_to_sqlmodel_task(task)

    # Try to relay
    r = RelayManager.try_relay(task)
    if r is not None:
        return r  # relay successful

    # No relay
    is_unique = sql_task.unique_key is not None

    with get_session() as session:
        if not is_unique:
            # Not unique, just save
            session.add(sql_task)
            session.flush()
            session.refresh(sql_task)
            return sqlmodel_to_pydantic_task(sql_task)

        # Has unique_key - find existing scheduled/retry tasks
        while True:
            stmt = (
                select(SQLTask)
                .where(
                    and_(
                        SQLTask.unique_key == sql_task.unique_key,
                        SQLTask.namespace == sql_task.namespace,
                        SQLTask.status.in_([SQLTaskStatus.scheduled, SQLTaskStatus.retry]),
                    )
                )
                .order_by(SQLTask.priority, SQLTask.eta)
                .limit(1)
            )
            existing_task = session.exec(stmt).first()

            if existing_task is None:
                # No existing scheduled task, create new one
                session.add(sql_task)
                session.flush()
                session.refresh(sql_task)
                return sqlmodel_to_pydantic_task(sql_task)

            # Update existing task
            old_revision = existing_task.revision
            existing_task.unique_update_from(sql_task)
            existing_task.revision = old_revision + 1
            existing_task.updated_at = utcnow()

            try:
                session.add(existing_task)
                session.flush()
                session.refresh(existing_task)
                log.debug(f"Updated task {existing_task.uid}")
                return sqlmodel_to_pydantic_task(existing_task)
            except IntegrityError:
                session.rollback()
                continue  # Try again (optimistic locking conflict)


def task_clean_expired_workers():
    """Release tasks from expired workers"""
    with get_session() as session:
        while True:
            stmt = (
                select(EventixTask)
                .where(
                    and_(
                        EventixTask.worker_expires.isnot(None), EventixTask.worker_expires < utcnow()
                    )
                )
                .limit(1)
            )
            existing_task = session.exec(stmt).first()

            if existing_task is None:
                break

            old_revision = existing_task.revision
            existing_task.status = EventixTaskStatusEnum.scheduled
            existing_task.worker_id = None
            existing_task.worker_expires = None
            existing_task.revision = old_revision + 1
            existing_task.updated_at = utcnow()

            try:
                session.add(existing_task)
                session.flush()
                log.info(f"Released task {existing_task.uid}")
            except IntegrityError:
                session.rollback()
                continue


def task_clean_expired_tasks():
    """Delete expired tasks"""
    with get_session() as session:
        while True:
            stmt = select(EventixTask.uid).where(
                and_(EventixTask.expires.isnot(None), EventixTask.expires < utcnow())
            ).limit(100)

            uids = list(session.exec(stmt).all())

            if len(uids) == 0:
                break

            for uid in uids:
                delete_stmt = delete(EventixTask).where(EventixTask.uid == uid)
                session.exec(delete_stmt)
                log.info(f"Removed expired task {uid}")

            session.flush()


def task_next_scheduled(worker_id: str, namespace: str, expires: int = 300) -> Optional[EventixTask]:
    """Get the next scheduled task for a worker"""
    log.debug(f"[{worker_id}] Worker getting next scheduled task...")

    eta = utcnow()

    with get_session() as session:
        while True:
            stmt = (
                select(EventixTask)
                .where(
                    and_(
                        EventixTask.namespace == namespace,
                        EventixTask.worker_id.is_(None),
                        EventixTask.status.in_([EventixTaskStatusEnum.scheduled, EventixTaskStatusEnum.retry]),
                        EventixTask.eta <= eta,
                    )
                )
                .order_by(EventixTask.priority, EventixTask.eta)
                .limit(1)
                .with_for_update(skip_locked=True)  # PostgreSQL row-level locking
            )

            existing_task = session.exec(stmt).first()

            if existing_task is None:
                return None

            old_revision = existing_task.revision
            existing_task.status = EventixTaskStatusEnum.processing
            existing_task.worker_id = worker_id
            existing_task.worker_expires = utcnow() + datetime.timedelta(seconds=expires)
            existing_task.revision = old_revision + 1
            existing_task.updated_at = utcnow()

            log.debug(f"task_next_scheduled: existing task revision: {existing_task.revision}")

            try:
                session.add(existing_task)
                session.flush()
                session.refresh(existing_task)
                return existing_task
            except IntegrityError:
                session.rollback()
                continue


def tasks_by_status(
    status: Optional[EventixTaskStatusEnum] = None,
    namespace: Optional[str] = None,
    skip: int = 0,
    limit: int = 100,
) -> List[EventixTask]:
    """Get tasks filtered by status and/or namespace"""
    with get_session() as session:
        stmt = select(EventixTask)

        filters = []
        if status is not None:
            filters.append(EventixTask.status == status)
        if namespace is not None:
            filters.append(EventixTask.namespace == namespace)

        if filters:
            stmt = stmt.where(and_(*filters))

        stmt = stmt.order_by(EventixTask.created_at.desc()).offset(skip).limit(limit)

        tasks = list(session.exec(stmt).all())
        return tasks


def tasks_by_task(
    task: str, namespace: Optional[str] = None, skip: int = 0, limit: int = 100
) -> List[EventixTask]:
    """Get tasks by task name"""
    with get_session() as session:
        stmt = select(EventixTask).where(EventixTask.task == task)

        if namespace is not None:
            stmt = stmt.where(EventixTask.namespace == namespace)

        # Custom sorting by status priority then eta
        stmt = stmt.order_by(EventixTask.status, EventixTask.eta.desc()).offset(skip).limit(limit)

        tasks = list(session.exec(stmt).all())
        return tasks


def task_by_unique_key(
    unique_key: str,
    namespace: Optional[str] = None,
    stati: Optional[List[EventixTaskStatusEnum]] = None,
) -> EventixTask:
    """Get task by unique key"""
    if stati is None:
        stati = [EventixTaskStatusEnum.scheduled, EventixTaskStatusEnum.retry]

    with get_session() as session:
        stmt = select(EventixTask).where(EventixTask.unique_key == unique_key)

        if namespace is not None:
            stmt = stmt.where(EventixTask.namespace == namespace)

        stmt = stmt.where(EventixTask.status.in_(stati)).limit(10)

        tasks = list(session.exec(stmt).all())

        if len(tasks) == 0:
            raise NoTaskFoundForUniqueKey(unique_key=unique_key)

        if len(tasks) > 1 and namespace is None:
            raise TaskUniqueKeyNotUnique(unique_key)

        return tasks[0]


def task_reschedule(uid: str, eta: Optional[datetime.datetime] = None) -> EventixTask:
    """Reschedule a task"""
    with get_session() as session:
        stmt = select(EventixTask).where(EventixTask.uid == uid)
        task = session.exec(stmt).first()

        if task is None:
            raise ValueError(f"Task {uid} not found")

        if task.status not in [EventixTaskStatusEnum.error, EventixTaskStatusEnum.retry]:
            raise WrongTaskStatus(uid, task.status)

        if eta is None:
            eta = utcnow()

        task.status = EventixTaskStatusEnum.scheduled
        task.eta = eta
        task.worker_id = None
        task.revision += 1
        task.updated_at = utcnow()

        session.add(task)
        session.flush()
        session.refresh(task)
        return task


def tasks_dump(skip: int = 0, limit: int = 100) -> List[EventixTask]:
    """Dump all tasks"""
    with get_session() as session:
        stmt = select(EventixTask).order_by(EventixTask.id).offset(skip).limit(limit)
        tasks = list(session.exec(stmt).all())
        return tasks


def task_get_by_uid(uid: str) -> EventixTask:
    """Get a task by UID"""
    with get_session() as session:
        stmt = select(EventixTask).where(EventixTask.uid == uid)
        task = session.exec(stmt).first()
        if task is None:
            raise ValueError(f"Task {uid} not found")
        return task


def task_update(task: EventixTask) -> EventixTask:
    """Update a task"""
    with get_session() as session:
        task.revision += 1
        task.updated_at = utcnow()
        session.add(task)
        session.flush()
        session.refresh(task)
        return task


def task_delete_by_uid(uid: str) -> None:
    """Delete a task by UID"""
    with get_session() as session:
        stmt = delete(EventixTask).where(EventixTask.uid == uid)
        session.exec(stmt)
        session.flush()
