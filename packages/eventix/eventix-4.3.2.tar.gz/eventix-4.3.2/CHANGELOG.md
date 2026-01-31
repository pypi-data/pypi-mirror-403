# Changelog

All notable changes to this project will be documented in this file.

## [4.4.0] - 2026-01-09

### 🚀 Major Changes

**Complete Migration from MongoDB to PostgreSQL**

This release represents a major architectural shift, moving from MongoDB with `pydantic-db-backend` to PostgreSQL with SQLModel/SQLAlchemy.

### ✨ Added

- **SQLModel Integration**: Modern ORM layer with full type safety
- **PostgreSQL Support**: ACID-compliant relational database backend
- **Row-Level Locking**: Prevents race conditions using `SELECT FOR UPDATE SKIP LOCKED`
- **Database Session Management**: Context managers for clean session handling
- **Migration Guide**: Comprehensive documentation for migrating from MongoDB
- **Converter Layer**: Seamless conversion between Pydantic and SQLModel types

### 🔧 Changed

- **Database Backend**: MongoDB → PostgreSQL 12+
- **ORM Layer**: `pydantic-db-backend` → SQLModel + SQLAlchemy
- **Task Model**: `BackendModel` → SQLModel with proper table definitions
- **Query Interface**: MongoDB aggregations → SQLAlchemy select statements
- **Concurrency**: MongoDB sessions → PostgreSQL transactions
- **Task Args**: Changed from `tuple` to `list` for better JSON compatibility
- **Settings**: Added `DATABASE_URL` configuration option
- **Default Backend**: Changed from `mongodb` to `postgresql`

### 📦 Dependencies

**Added:**
- `sqlmodel>=0.0.22,<0.1.0`
- `psycopg2-binary>=2.9.9,<3.0.0`
- `alembic>=1.13.0,<2.0.0`

**Removed:**
- `pydantic-db-backend[mongodb]`
- `pydantic-db-backend-common`

### 🗂️ New Files

- `eventix/database.py`: Database initialization and session management
- `eventix/sqlmodels/task.py`: SQLModel task table definition
- `eventix/sqlmodels/event.py`: SQLModel event and trigger tables
- `eventix/sqlmodels/schedule.py`: SQLModel schedule table
- `eventix/converters.py`: Pydantic ↔ SQLModel converters
- `MIGRATION_GUIDE.md`: Step-by-step migration documentation

### 🔄 Modified Files

- `eventix/functions/task.py`: Complete rewrite using SQLAlchemy
- `eventix/functions/fastapi.py`: Updated backend initialization
- `eventix/pydantic/task.py`: Simplified to pure Pydantic model
- `eventix/pydantic/settings.py`: Added PostgreSQL configuration
- `eventix/router/task.py`: Updated to use new task functions
- `.env.local.example`: PostgreSQL configuration template
- `pyproject.toml`: Updated dependencies and version
- `README.md`: Updated documentation for PostgreSQL

### 💡 Benefits

1. **Better Performance**: Optimized B-tree indexes and query planning
2. **ACID Compliance**: Full transactional support with rollback
3. **No Race Conditions**: PostgreSQL row locking prevents double-execution
4. **Standard Tooling**: Use pgAdmin, psql, and other PostgreSQL tools
5. **Production Ready**: Battle-tested database with proven scalability
6. **Better Debugging**: SQL queries are easier to understand and debug
7. **Type Safety**: SQLModel provides excellent IDE support and type checking

### ⚠️ Breaking Changes

1. **Configuration**: `MONGODB_URI` → `DATABASE_URL`
2. **Backend Setting**: `EVENTIX_BACKEND="mongodb"` → `EVENTIX_BACKEND="postgresql"`
3. **Database**: Requires PostgreSQL 12+ instead of MongoDB
4. **Model Fields**: Task `args` changed from tuple to list
5. **Dependencies**: MongoDB drivers no longer required

### 📚 Migration

See [MIGRATION_GUIDE.md](MIGRATION_GUIDE.md) for detailed migration instructions.

### 🔒 Security

- Connection pooling with configurable limits
- Parameterized queries prevent SQL injection
- Timezone-aware timestamps for consistency

---

## [4.3.1] - Previous Release

- Updated event execution logic
- Re-enabled skipped tests
- Bug fixes and improvements

## [4.3.0] - Previous Release

- Added HTTP health check middleware
- Updated dependencies
- Bug fixes

## [4.2.0] - Previous Release

- Previous features and improvements
