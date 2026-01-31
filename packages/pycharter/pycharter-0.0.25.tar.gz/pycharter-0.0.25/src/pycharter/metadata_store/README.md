# Metadata Store Implementations

PyCharter provides multiple metadata store implementations to suit different use cases:

## Available Implementations

### 1. InMemoryMetadataStore
**Use case**: Testing, development, prototyping

**Dependencies**: None (built-in)

**Example**:
```python
from pycharter import InMemoryMetadataStore

store = InMemoryMetadataStore()
store.connect()

schema_id = store.store_schema("user", {"type": "object"}, version="1.0")
schema = store.get_schema(schema_id)
```

---

### 2. MongoDBMetadataStore
**Use case**: Document-based storage, flexible schema evolution

**Dependencies**: `pymongo`
```bash
pip install pymongo
```

**Connection string format**: `mongodb://[username:password@]host[:port][/database]`

**Example**:
```python
from pycharter import MongoDBMetadataStore

store = MongoDBMetadataStore(
    connection_string="mongodb://localhost:27017/pycharter",
    database_name="pycharter"
)
store.connect()

schema_id = store.store_schema("user", {"type": "object"}, version="1.0")
schema = store.get_schema(schema_id)
```

---

### 3. PostgresMetadataStore
**Use case**: Relational data, ACID transactions, complex queries

**Dependencies**: `psycopg2-binary`
```bash
pip install psycopg2-binary
```

**Connection string format**: `postgresql://[user[:password]@][host][:port][/database]`

**Example**:
```python
from pycharter import PostgresMetadataStore

store = PostgresMetadataStore(
    connection_string="postgresql://user:password@localhost/pycharter"
)
store.connect()

schema_id = store.store_schema("user", {"type": "object"}, version="1.0")
schema = store.get_schema(schema_id)
```

**Schema Management**: 
- Schema is automatically initialized and validated on `connect()`
- Version tracking ensures schema compatibility
- Use `store.get_schema_info()` to check schema status
- See [SCHEMA_MANAGEMENT.md](SCHEMA_MANAGEMENT.md) for details

**CLI Tools**:
```bash
# Initialize schema manually
pycharter db init postgresql://user:pass@localhost/pycharter

# Upgrade to latest version
pycharter db upgrade postgresql://user:pass@localhost/pycharter

# Check current revision
pycharter db current postgresql://user:pass@localhost/pycharter

# See migration history
pycharter db history
```

---

### 4. SQLiteMetadataStore
**Use case**: Development, testing, small projects, embedded applications

**Dependencies**: None (sqlite3 is built into Python)

**Connection string format**: `sqlite:///path/to/database.db` or `sqlite:///:memory:`

**Example**:
```python
from pycharter import SQLiteMetadataStore

# File-based database
store = SQLiteMetadataStore("sqlite:///pycharter.db")
store.connect()

# In-memory database (for testing)
store = SQLiteMetadataStore("sqlite:///:memory:")
store.connect()

schema_id = store.store_schema("user", {"type": "object"}, version="1.0")
schema = store.get_schema(schema_id)
```

**Schema Management**: 
- Schema is automatically initialized and validated on `connect()`
- Uses SQLAlchemy models (same as PostgreSQL)
- Supports Alembic migrations
- Use `store.get_schema_info()` to check schema status

**CLI Tools**:
```bash
# Initialize schema manually
pycharter db init sqlite:///pycharter.db

# Run migrations
pycharter db upgrade sqlite:///pycharter.db
```

**Notes**:
- SQLite databases are file-based - easy to backup, share, and version control
- Perfect for development and testing (no server setup required)
- Good for small to medium projects
- Limited concurrent writes (fine for read-heavy workloads)
- Single-machine only (no network access)

---

### 5. RedisMetadataStore
**Use case**: High-performance caching, fast lookups, temporary storage

**Dependencies**: `redis`
```bash
pip install redis
```

**Connection string format**: `redis://[password@]host[:port][/database]`

**Example**:
```python
from pycharter import RedisMetadataStore

store = RedisMetadataStore(
    connection_string="redis://localhost:6379/0",
    key_prefix="pycharter"
)
store.connect()

schema_id = store.store_schema("user", {"type": "object"}, version="1.0")
schema = store.get_schema(schema_id)
```

---

## Common Usage Pattern

All implementations follow the same interface:

```python
from pycharter import InMemoryMetadataStore  # or any other implementation

# Initialize and connect
store = InMemoryMetadataStore()
store.connect()

# Store schema
schema_id = store.store_schema(
    schema_name="user",
    schema={"type": "object", "properties": {"name": {"type": "string"}}},
    version="1.0"
)

# Store ownership and governance rules via metadata
metadata = {
    "title": "User Schema",
    "business_owners": ["data-team@example.com"],
    "governance_rules": {
        "pii_encryption": {"type": "encrypt", "fields": ["email"]}
    }
}
store.store_metadata(schema_id, metadata, "schema")

# Retrieve data
schema = store.get_schema(schema_id)
retrieved_metadata = store.get_metadata(schema_id, "schema")
ownership = retrieved_metadata.get("business_owners") if retrieved_metadata else None
rules = retrieved_metadata.get("governance_rules") if retrieved_metadata else None

# List all schemas
all_schemas = store.list_schemas()

# Disconnect
store.disconnect()
```

## Context Manager Usage

All stores support context manager syntax:

```python
with InMemoryMetadataStore() as store:
    schema_id = store.store_schema("user", {"type": "object"})
    schema = store.get_schema(schema_id)
    # Automatically disconnects on exit
```

## Choosing the Right Store

- **InMemoryMetadataStore**: Testing, development, demos (zero dependencies, no persistence)
- **SQLiteMetadataStore**: Development, testing, small projects (file-based, no server needed)
- **MongoDBMetadataStore**: Flexible document storage, schema evolution
- **PostgresMetadataStore**: Production systems, complex queries, ACID guarantees
- **RedisMetadataStore**: High-performance caching, temporary storage, fast lookups

