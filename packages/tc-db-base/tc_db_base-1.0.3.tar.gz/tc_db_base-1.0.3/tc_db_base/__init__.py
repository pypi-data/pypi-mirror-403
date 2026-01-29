"""tc-db-base - Schema-Driven Database Service.

A flexible, schema-driven database module that auto-generates:
- Collection management
- CRUD operations with validation
- Search functions based on schema
- Index management
- Type validation
- Fluent query builder
- Real-time pub/sub with change streams
- Transaction support

Usage:
    from tc_db_base import get_db, get_repository

    # Initialize
    db = get_db()

    # Get auto-generated repository
    users = get_repository('users')

    # Use auto-generated methods
    user = users.create({'user_key': 'usr_123', ...})
    user = users.find_by_user_key('usr_123')
    users_list = users.find_by_account_key('acc_456')

    # Fluent query builder
    active_users = (users.query()
        .where('status', 'active')
        .where_gt('age', 18)
        .order_by('created_at', 'desc')
        .limit(10)
        .get())

    # Transactions (flexible - only when needed)
    with users.transaction() as session:
        users.create({'name': 'John'}, session=session)
        accounts.create({'user_id': user_id}, session=session)
        # Auto-commits on success, auto-rollback on exception

    # Real-time pub/sub
    from tc_db_base import get_pubsub, ChangeType

    pubsub = get_pubsub()

    @pubsub.on_insert('users')
    def on_new_user(event):
        print(f"New user: {event.document}")

    pubsub.start()
"""

__version__ = '1.0.3'

from tc_db_base.client import DatabaseClient, get_db_client
from tc_db_base.service import DatabaseService, get_db, init_db
from tc_db_base.repository import DynamicRepository, get_repository
from tc_db_base.schema import SchemaLoader, get_schema
from tc_db_base.query_builder import QueryBuilder
from tc_db_base.pubsub import (
    PubSub,
    get_pubsub,
    ChangeType,
    ChangeEvent,
    EventEmitter,
    get_emitter
)
from tc_db_base.transaction import (
    TransactionManager,
    TransactionContext,
    TransactionError,
    transaction,
    transactional,
    UnitOfWork,
    get_current_transaction
)

__all__ = [
    '__version__',
    # Client
    'DatabaseClient',
    'get_db_client',
    # Service
    'DatabaseService',
    'get_db',
    'init_db',
    # Repository
    'DynamicRepository',
    'get_repository',
    # Schema
    'SchemaLoader',
    'get_schema',
    # Query Builder
    'QueryBuilder',
    # Transactions
    'TransactionManager',
    'TransactionContext',
    'TransactionError',
    'transaction',
    'transactional',
    'UnitOfWork',
    'get_current_transaction',
    # Pub/Sub
    'PubSub',
    'get_pubsub',
    'ChangeType',
    'ChangeEvent',
    'EventEmitter',
    'get_emitter',
]

