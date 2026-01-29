"""tc-db-base - Schema-Driven Database Service.

A flexible, schema-driven database module that auto-generates:
- Collection management
- CRUD operations with validation
- Search functions based on schema
- Index management
- Type validation

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
"""

__version__ = '1.0.1'

from tc_db_base.client import DatabaseClient, get_db_client
from tc_db_base.service import DatabaseService, get_db, init_db
from tc_db_base.repository import DynamicRepository, get_repository
from tc_db_base.schema import SchemaLoader, get_schema

__all__ = [
    '__version__',
    'DatabaseClient',
    'get_db_client',
    'DatabaseService',
    'get_db',
    'init_db',
    'DynamicRepository',
    'get_repository',
    'SchemaLoader',
    'get_schema',
]

