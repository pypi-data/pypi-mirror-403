# tc-db-base - Schema-Driven Database Service

A flexible, schema-driven database module that auto-generates repositories with CRUD operations, search functions, and index management based on a JSON schema.

## Installation

```bash
# Install from PyPI
pip install tc-db-base

# Or with Flask support
pip install tc-db-base[flask]
```

## Features

- **Schema-Driven**: Define collections in JSON, get auto-generated methods
- **Auto-Generated Finders**: `find_by_{field}()` for unique/searchable fields
- **Compound Queries**: `find_by_x_and_y()`, `find_by_x_or_y()`, `find_by_x_not_y()`
- **Fluent Query Builder**: Chain methods like `.where().order_by().limit().get()`
- **Transactions**: Flexible transaction support - use only when needed via `session` parameter
- **Real-Time Pub/Sub**: MongoDB Change Streams for live notifications
- **Validation**: Automatic validation against schema
- **Soft Delete**: Optional soft delete support per collection
- **Timestamps**: Auto-managed `created_at` / `updated_at`
- **Index Management**: Auto-create indexes from schema
- **Search**: Built-in search across searchable fields
- **Aggregation Shortcuts**: `sum()`, `avg()`, `min()`, `max()`, `group_by()`
- **Bulk Operations**: `update()`, `delete()`, `increment()` on query results
- **Unit of Work**: Group multiple operations into atomic transactions
- **Event Emitter**: Local pub/sub without MongoDB dependency

## Getting Started

### 1. Create Schema Files

Create your schema in `resources/schema/`:

```
your_project/
├── resources/
│   └── schema/
│       ├── dbs.json           # Main config
│       └── dbs/
│           └── app_db.json    # Database schema
└── app.py
```

See `examples/` folder for sample schema files.

### 2. Define Your Database Schema

**resources/schema/dbs.json:**
```json
{
  "version": "1.0.0",
  "databases": ["app_db"],
  "settings": {
    "auto_timestamps": true,
    "default_limit": 100
  }
}
```

**resources/schema/dbs/app_db.json:**
```json
{
  "db_name": "app_db",
  "collections": {
    "users": {
      "fields": {
        "user_id": {"type": "string", "required": true},
        "email": {"type": "string", "required": true, "format": "email"},
        "name": {"type": "string"},
        "status": {"type": "string", "enum": ["active", "inactive"], "default": "active"},
        "created_at": {"type": "datetime", "auto": "create"},
        "updated_at": {"type": "datetime", "auto": "update"}
      },
      "unique_fields": ["user_id", "email"],
      "searchable_fields": ["user_id", "email", "name", "status"],
      "soft_delete": true
    }
  }
}
```

### 3. Use the Auto-Generated Repository

```python
from tc_db_base import init_db, get_repository

# Initialize and connect
db = init_db()

# Get auto-generated repository
users = get_repository('users')

# Create (with auto-validation and timestamps)
user_id = users.create({
    'user_id': 'usr_123',
    'email': 'john@example.com',
    'name': 'John Doe'
})

# Auto-generated finders (from unique_fields)
user = users.find_by_user_id('usr_123')
user = users.find_by_email('john@example.com')

# Auto-generated finders (from searchable_fields)
active_users = users.find_by_status('active')

# Search across searchable fields
results = users.search('john', limit=10)

# Standard CRUD
user = users.find_by_id(user_id)
users.update_by_id(user_id, {'name': 'John Smith'})
users.delete_by_id(user_id)  # Soft delete if enabled
```

## Schema Definition (dbs.json)

```json
{
  "dbs": {
    "user_db": {
      "users": {
        "description": "User accounts",
        "fields": {
          "user_key": {"type": "string", "required": true},
          "email": {"type": "string", "required": true, "format": "email"},
          "name": {"type": "string"},
          "status": {"type": "string", "enum": ["active", "inactive"], "default": "active"},
          "created_at": {"type": "datetime", "auto": "create"},
          "updated_at": {"type": "datetime", "auto": "update"}
        },
        "unique_fields": ["user_key", "email"],
        "indexes": {
          "user_key_idx": {"fields": ["user_key"], "unique": true},
          "email_idx": {"fields": ["email"], "unique": true}
        },
        "searchable_fields": ["user_key", "email", "name"],
        "soft_delete": true,
        "timestamps": true
      }
    }
  }
}
```

## Auto-Generated Methods

For each collection, these methods are auto-generated:

### CRUD Operations
```python
repo.create(data)                    # Insert with validation
repo.create_many(documents)          # Bulk insert
repo.find_by_id(id)                  # Find by _id
repo.find_one(query)                 # Find single
repo.find_many(query, skip, limit)   # Find multiple
repo.update_one(query, data)         # Update single
repo.update_by_id(id, data)          # Update by ID
repo.delete_one(query)               # Delete (soft if enabled)
repo.delete_by_id(id)                # Delete by ID
repo.hard_delete(query)              # Permanent delete
repo.restore(query)                  # Restore soft-deleted
repo.count(query)                    # Count documents
repo.exists(query)                   # Check existence
```

### Dynamic Finders (auto-generated from schema)
```python
# For unique_fields: ["user_key", "email"]
repo.find_by_user_key(value)         # Returns single doc
repo.find_by_email(value)            # Returns single doc

# For searchable_fields: ["account_key", "name"]
repo.find_by_account_key(value)      # Returns list
repo.find_by_name(value)             # Returns list

# Compound queries (AND, OR, NOT)
repo.find_by_user_key_and_account_key(uk, ak)     # AND
repo.find_by_user_key_or_account_key(uk, ak)      # OR
repo.find_by_account_key_not_user_key(ak, uk)     # NOT
```

### Fluent Query Builder
```python
# Complex queries with fluent API
results = (repo.query()
    .where('status', 'active')
    .where_gt('age', 18)
    .where_in('role', ['admin', 'manager'])
    .where_between('created_at', start, end)
    .where_like('name', '%john%')
    .or_where('is_vip', True)
    .order_by('created_at', 'desc')
    .skip(10)
    .limit(20)
    .select(['name', 'email'])
    .get())

# Single document
user = repo.query().where('email', 'test@example.com').first()

# Existence check
exists = repo.query().where('email', 'test@example.com').exists()

# Count
count = repo.query().where('status', 'active').count()

# Aggregations
total = repo.query().where('status', 'active').sum('amount')
avg = repo.query().where('status', 'active').avg('age')

# Bulk operations
repo.query().where('status', 'pending').update({'status': 'active'})
repo.query().where('status', 'deleted').delete()

# Array operations
repo.query().where('user_key', 'u123').push('tags', 'new_tag')
repo.query().where('user_key', 'u123').increment('login_count')

# Pagination
results = repo.query().where('status', 'active').page(2, per_page=20).get()

# Nested conditions
results = (repo.query()
    .where('status', 'active')
    .where_or(lambda q: q.where('role', 'admin').where('role', 'manager'))
    .get())
```

### Search & Aggregation
```python
repo.search(text, fields, limit)     # Search searchable_fields
repo.search_by_fields(field=value)   # Multi-field search
repo.aggregate(pipeline)             # Run aggregation
repo.group_by(field, match)          # Group by field
repo.count_by(field)                 # Count grouped
repo.distinct(field, query)          # Distinct values
```

### Index Management
```python
repo.ensure_indexes()                # Create indexes from schema
repo.get_indexes()                   # List current indexes
```

## Query Builder Reference

### Where Conditions
| Method | Description | Example |
|--------|-------------|---------|
| `where(field, value)` | Equals | `.where('status', 'active')` |
| `where_eq(field, value)` | Equals | `.where_eq('age', 25)` |
| `where_ne(field, value)` | Not equals | `.where_ne('status', 'deleted')` |
| `where_gt(field, value)` | Greater than | `.where_gt('age', 18)` |
| `where_gte(field, value)` | Greater or equal | `.where_gte('score', 100)` |
| `where_lt(field, value)` | Less than | `.where_lt('price', 50)` |
| `where_lte(field, value)` | Less or equal | `.where_lte('quantity', 10)` |
| `where_in(field, list)` | In list | `.where_in('status', ['a', 'b'])` |
| `where_not_in(field, list)` | Not in list | `.where_not_in('role', ['guest'])` |
| `where_like(field, pattern)` | SQL LIKE | `.where_like('name', '%john%')` |
| `where_regex(field, pattern)` | Regex match | `.where_regex('email', '.*@gmail')` |
| `where_between(field, a, b)` | Between values | `.where_between('age', 18, 65)` |
| `where_null(field)` | Is null | `.where_null('deleted_at')` |
| `where_not_null(field)` | Not null | `.where_not_null('email')` |
| `where_exists(field)` | Field exists | `.where_exists('profile')` |

### Execution Methods
| Method | Description |
|--------|-------------|
| `get()` / `all()` | Get all results |
| `first()` | Get first result |
| `first_or_fail()` | Get first or raise |
| `last()` | Get last result |
| `count()` | Count results |
| `exists()` | Check if exists |
| `distinct(field)` | Get distinct values |
| `pluck(field)` | Get field values only |

### Modification Methods
| Method | Description |
|--------|-------------|
| `update(data)` | Update matching docs |
| `delete()` | Delete matching docs |
| `increment(field, n)` | Increment field |
| `decrement(field, n)` | Decrement field |
| `push(field, value)` | Push to array |
| `pull(field, value)` | Remove from array |

## Transactions

Flexible transaction support - use only when needed by passing `session` parameter.

### Basic Usage (Context Manager)
```python
users = get_repository('users')
accounts = get_repository('accounts')

# Transactions only when you need them
with users.transaction() as session:
    user_id = users.create({'name': 'John', 'email': 'john@example.com'}, session=session)
    accounts.create({'user_id': user_id, 'balance': 0}, session=session)
    # Auto-commits on success
    # Auto-rollback on any exception
```

### Callback Style
```python
def create_user_with_account(session):
    user_id = users.create({'name': 'John'}, session=session)
    accounts.create({'user_id': user_id}, session=session)
    return user_id

result = users.with_transaction(create_user_with_account)
```

### Using @transactional Decorator
```python
from tc_db_base import transactional

@transactional
def create_order(customer_id, items, txn=None):
    order_id = orders.create({
        'customer_id': customer_id,
        'items': items,
        'status': 'pending'
    }, session=txn.session)
    
    # Update inventory
    for item in items:
        inventory.update_one(
            {'product_id': item['product_id']},
            {'quantity': item['quantity']},
            session=txn.session
        )
    
    return order_id

# Call normally - transaction is automatic
order_id = create_order('c123', [{'product_id': 'p1', 'quantity': 2}])
```

### Unit of Work Pattern
```python
from tc_db_base import UnitOfWork

uow = UnitOfWork()

# Register operations (not executed yet)
uow.register_new('users', {'name': 'John', 'email': 'john@example.com'})
uow.register_new('accounts', {'user_id': 'temp', 'balance': 0})
uow.register_update('settings', {'user_id': 'u123'}, {'theme': 'dark'})
uow.register_delete('sessions', {'user_id': 'u123'})

# Execute all in single transaction
results = uow.commit()
print(f"Inserted: {results['inserted_ids']}")
print(f"Modified: {results['modified_count']}")
print(f"Deleted: {results['deleted_count']}")
```

### Standalone Transaction Manager
```python
from tc_db_base import transaction

# Works across multiple repositories
with transaction() as txn:
    users.create({...}, session=txn.session)
    orders.create({...}, session=txn.session)
    payments.create({...}, session=txn.session)
```

### Key Points
- **Flexible**: Normal operations don't use transactions (faster)
- **Opt-in**: Pass `session=session` only when needed
- **Auto-rollback**: Any exception triggers rollback
- **Cross-collection**: Same session works across different repositories

## Real-Time Pub/Sub

Built-in pub/sub using MongoDB Change Streams for real-time notifications.

### Basic Usage
```python
from tc_db_base import get_pubsub, ChangeType, ChangeEvent

pubsub = get_pubsub()

# Subscribe to all changes
def on_user_change(event: ChangeEvent):
    print(f"User {event.document_id} was {event.change_type.value}")
    print(f"Document: {event.document}")

sub_id = pubsub.subscribe('users', on_user_change)

# Subscribe to specific operations
sub_id = pubsub.subscribe(
    'users',
    on_user_change,
    change_types=[ChangeType.INSERT, ChangeType.UPDATE]
)

# Subscribe with filter (only active users)
sub_id = pubsub.subscribe(
    'users',
    on_user_change,
    filter_query={'status': 'active'}
)

# Start listening
pubsub.start()

# Unsubscribe
pubsub.unsubscribe(sub_id)

# Stop
pubsub.stop()
```

### Decorator Syntax
```python
@pubsub.on('users', [ChangeType.INSERT])
def handle_new_user(event: ChangeEvent):
    print(f"New user created: {event.document}")

@pubsub.on_insert('orders')
def handle_new_order(event: ChangeEvent):
    # Send notification, update inventory, etc.
    pass

@pubsub.on_update('users')
def handle_user_update(event: ChangeEvent):
    # event.update_description contains changed fields
    pass

@pubsub.on_delete('sessions')
def handle_session_end(event: ChangeEvent):
    pass
```

### Change Event Properties
```python
event.change_type      # ChangeType enum (INSERT, UPDATE, DELETE, etc.)
event.collection       # Collection name
event.document_id      # Document _id as string
event.document         # Full document (on insert/update with lookup)
event.update_description  # {updatedFields: {...}, removedFields: [...]}
event.timestamp        # When the change occurred
event.raw_event        # Original MongoDB change event
```

### Local Event Emitter
For pub/sub without MongoDB (in-memory):
```python
from tc_db_base import get_emitter

emitter = get_emitter()

# Subscribe
emitter.on('user:created', lambda data: print(f"User: {data}"))
emitter.once('app:ready', lambda: print("App is ready!"))

# Publish
emitter.emit('user:created', {'name': 'John'})

# Unsubscribe
emitter.off('user:created')
```

## Field Types

| Type | Python Type | Description |
|------|-------------|-------------|
| `string` | str | Text values |
| `number` | int/float | Numeric values |
| `boolean` | bool | True/False |
| `array` | list | Lists |
| `object` | dict | Nested objects |
| `datetime` | datetime | Timestamps |

## Field Options

| Option | Description |
|--------|-------------|
| `required` | Field is mandatory |
| `default` | Default value |
| `enum` | Allowed values list |
| `format` | Validation format (email, url, phone) |
| `sensitive` | Excluded from query results |
| `auto` | Auto-set: "create" or "update" |

## REST API (Standalone Server)

```bash
# Using module
python -m tc_db_base.server --port 5002

# Or using installed command
tc-db-server --port 5002
```

### Endpoints

```
GET  /health                         # Health check
GET  /schema                         # Full schema
GET  /schema/{collection}            # Collection schema

GET  /api/v1/{collection}            # List documents
GET  /api/v1/{collection}/{id}       # Get by ID
POST /api/v1/{collection}            # Create
PUT  /api/v1/{collection}/{id}       # Update
DELETE /api/v1/{collection}/{id}     # Delete

GET  /api/v1/{collection}/search?q=text  # Search
POST /api/v1/{collection}/aggregate      # Aggregation
GET  /api/v1/{collection}/count-by/{field}  # Count by field
```

## Project Structure

```
tc_db_base/
├── __init__.py          # Package exports
├── client.py            # MongoDB client
├── service.py           # DatabaseService
├── repository.py        # DynamicRepository
├── query_builder.py     # Fluent query builder
├── pubsub.py            # Real-time pub/sub
├── server.py            # REST API server
└── schema/
    ├── __init__.py      # SchemaLoader
    ├── validator.py     # SchemaValidator
    └── dbs.json         # Database schema
```

## Configuration

Uses `task_circuit_base` for configuration (if available), otherwise falls back to environment variables.

Schema files are loaded from (in priority order):
1. `SCHEMA_PATH` environment variable
2. `{cwd}/resources/schema/`
3. Parent directories `/resources/schema/`
4. Package default `tc_db_base/schema/`

```python
# Via environment variables
MONGO_URI=mongodb://localhost:27017
SCHEMA_PATH=/path/to/custom/schema

# Via resources/config.yaml (if using task_circuit_base)
database:
  mongo_uri: mongodb://localhost:27017
  connection:
    max_pool_size: 100
```

