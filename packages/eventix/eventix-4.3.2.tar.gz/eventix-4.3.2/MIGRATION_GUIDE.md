# Migration Guide: MongoDB to PostgreSQL

This guide will help you migrate from the MongoDB-based backend to the new PostgreSQL + SQLModel backend.

## What Changed

### Major Changes

1. **Database Backend**: MongoDB → PostgreSQL 12+
2. **ORM Layer**: `pydantic-db-backend` → SQLModel + SQLAlchemy
3. **Data Models**: BackendModel → SQLModel with proper table definitions
4. **Query Interface**: MongoDB queries → SQLAlchemy queries
5. **Transactions**: MongoDB sessions → PostgreSQL ACID transactions
6. **Concurrency Control**: MongoDB optimistic locking → PostgreSQL row-level locking with `SELECT FOR UPDATE SKIP LOCKED`

### Benefits

- **ACID Compliance**: Full transactional support
- **Better Performance**: Optimized indexes and query planning
- **Row-Level Locking**: No more race conditions when workers claim tasks
- **Better Tooling**: Standard SQL tools for debugging and monitoring
- **Type Safety**: Better type checking with SQLModel

## Migration Steps

### 1. Update Dependencies

```bash
# Remove old dependencies
uv remove pydantic-db-backend pydantic-db-backend-common

# Install new dependencies (already in pyproject.toml)
uv sync
```

### 2. Set Up PostgreSQL

#### Option A: Docker (Recommended for Development)

```bash
docker run -d \
  --name eventix-postgres \
  -e POSTGRES_USER=eventix \
  -e POSTGRES_PASSWORD=eventix \
  -e POSTGRES_DB=eventix \
  -p 5432:5432 \
  postgres:16
```

#### Option B: Local Installation

```bash
# Ubuntu/Debian
sudo apt-get install postgresql-16

# macOS
brew install postgresql@16

# Create database and user
psql postgres
CREATE USER eventix WITH PASSWORD 'eventix';
CREATE DATABASE eventix OWNER eventix;
```

### 3. Update Configuration

Update your `.env.local` file:

```env
# Old MongoDB configuration (remove these)
# MONGODB_URI=mongodb://localhost:27017/eventix
# EVENTIX_BACKEND=mongodb

# New PostgreSQL configuration
DATABASE_URL=postgresql://eventix:eventix@localhost:5432/eventix
EVENTIX_BACKEND=postgresql
```

### 4. Data Migration (if needed)

If you have existing data in MongoDB that you want to migrate:

```python
# migration_script.py
import os
from pymongo import MongoClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

# Connect to MongoDB
mongo_client = MongoClient(os.getenv("MONGODB_URI"))
mongo_db = mongo_client.eventix

# Connect to PostgreSQL
from eventix.database import get_session
from eventix.sqlmodels.task import EventixTask

# Migrate tasks
with get_session() as session:
    for task_doc in mongo_db.task.find():
        # Convert MongoDB document to PostgreSQL model
        task = EventixTask(
            uid=task_doc["uid"],
            task=task_doc["task"],
            namespace=task_doc.get("namespace", "default"),
            status=task_doc["status"],
            priority=task_doc.get("priority", 0),
            eta=task_doc.get("eta"),
            args=task_doc.get("args", []),
            kwargs=task_doc.get("kwargs", {}),
            # ... map other fields
        )
        session.add(task)
```

### 5. Update Custom Code

If you have custom code that directly uses the database:

#### Before (MongoDB):
```python
from pydantic_db_backend.backend import Backend
from eventix.pydantic.task import TEventixTask

client = Backend.client()
task = client.get_instance(TEventixTask, uid)
```

#### After (PostgreSQL):
```python
from eventix.functions.task import task_get_by_uid

task = task_get_by_uid(uid)
```

### 6. Test Your Application

```bash
# Run tests
pytest

# Start the server
python main.py

# Start a worker
python worker.py
```

### 7. Update Docker Compose (if applicable)

```yaml
version: '3.8'

services:
  postgres:
    image: postgres:16
    environment:
      POSTGRES_USER: eventix
      POSTGRES_PASSWORD: eventix
      POSTGRES_DB: eventix
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data

  eventix-api:
    build: .
    environment:
      DATABASE_URL: postgresql://eventix:eventix@postgres:5432/eventix
      EVENTIX_BACKEND: postgresql
    depends_on:
      - postgres
    ports:
      - "8000:8000"

volumes:
  postgres_data:
```

## Breaking Changes

### API Changes

The REST API remains compatible, but some internal behaviors have changed:

1. **Task IDs**: Now using auto-incrementing integer `id` plus UUID `uid`
2. **Timestamps**: All timestamps are now timezone-aware (UTC)
3. **Revision Field**: Still supported for optimistic locking
4. **Args Field**: Changed from `tuple` to `list` for JSON compatibility

### Configuration Changes

- `MONGODB_URI` → `DATABASE_URL`
- `EVENTIX_BACKEND`: `mongodb` → `postgresql`

### Code Changes

If you extended Eventix:

1. **Model Inheritance**: `BackendModel` → `SQLModel`
2. **Queries**: MongoDB query syntax → SQLAlchemy
3. **Indexes**: Defined in SQLModel table schema
4. **Context Managers**: Use `get_session()` for database access

## Rollback Plan

If you need to rollback:

1. Restore previous version from git
2. Switch back to MongoDB in configuration
3. Restore MongoDB backup if data was migrated

## Performance Tuning

### PostgreSQL Configuration

For production, tune these PostgreSQL settings:

```sql
-- Increase connection pool
max_connections = 200

-- Increase shared buffers (25% of RAM)
shared_buffers = 4GB

-- Increase work memory
work_mem = 16MB

-- Enable parallel queries
max_parallel_workers_per_gather = 4
```

### Eventix Configuration

```env
# Connection pool settings (in database.py)
# pool_size = 10
# max_overflow = 20
```

## Troubleshooting

### Connection Issues

```bash
# Test PostgreSQL connection
psql -h localhost -U eventix -d eventix

# Check if PostgreSQL is running
sudo systemctl status postgresql
```

### Migration Errors

```bash
# Drop and recreate tables (development only!)
python -c "from eventix.database import get_engine; from sqlmodel import SQLModel; engine = get_engine(); SQLModel.metadata.drop_all(engine); SQLModel.metadata.create_all(engine)"
```

### Performance Issues

```sql
-- Check slow queries
SELECT * FROM pg_stat_statements ORDER BY total_exec_time DESC LIMIT 10;

-- Analyze tables
ANALYZE eventix_task;
```

## Support

For issues or questions:
- Open an issue on GitHub
- Check existing documentation
- Review PostgreSQL and SQLModel documentation

## Version Compatibility

- Eventix 4.4.0+: PostgreSQL only
- Eventix 4.3.x: MongoDB (legacy)
