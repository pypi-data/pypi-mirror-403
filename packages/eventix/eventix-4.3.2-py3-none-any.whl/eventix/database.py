import logging
from contextlib import contextmanager
from typing import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlmodel import SQLModel

from eventix.pydantic.settings import EventixServerSettings

log = logging.getLogger(__name__)

# Global engine and session factory
_engine = None
_SessionLocal = None


def get_database_url() -> str:
    """Get the database URL from settings"""
    settings = EventixServerSettings()
    return settings.database_url


def init_database():
    """Initialize the database engine and create all tables"""
    global _engine, _SessionLocal

    if _engine is not None:
        log.info("Database already initialized")
        return

    database_url = get_database_url()
    log.info(f"Initializing PostgreSQL database connection: {database_url.split('@')[-1] if '@' in database_url else 'local'}")

    _engine = create_engine(
        database_url,
        echo=False,
        pool_pre_ping=True,
        pool_size=10,
        max_overflow=20,
    )

    _SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=_engine)

    # Create all tables
    SQLModel.metadata.create_all(_engine)
    log.info("Database tables created successfully")


def get_engine():
    """Get the database engine"""
    if _engine is None:
        init_database()
    return _engine


def get_session_factory():
    """Get the session factory"""
    if _SessionLocal is None:
        init_database()
    return _SessionLocal


@contextmanager
def get_session() -> Generator[Session, None, None]:
    """Get a database session context manager"""
    SessionLocal = get_session_factory()
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def get_db() -> Generator[Session, None, None]:
    """Dependency for FastAPI to get database session"""
    with get_session() as session:
        yield session
