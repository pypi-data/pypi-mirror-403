"""Dynamic Repository - Auto-generated repository with schema-driven methods."""

import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Callable
from functools import partial
from contextlib import contextmanager

from bson import ObjectId
from pymongo import ASCENDING, DESCENDING
from pymongo.client_session import ClientSession

from tc_db_base.schema import get_schema
from tc_db_base.schema.validator import SchemaValidator, ValidationError
from tc_db_base.client import get_db_client

logger = logging.getLogger(__name__)


class DynamicRepository:
    """Schema-driven repository with auto-generated methods.

    Based on the schema, this repository auto-generates:
    - find_by_{unique_field}() for each unique field
    - find_by_{searchable_field}() for each searchable field
    - Validation on create/update
    - Soft delete support
    - Timestamp management
    - Transaction support (optional)

    Transaction Usage:
        # Method 1: Pass session parameter
        with repo.transaction() as session:
            repo.create({...}, session=session)
            repo.update_one({...}, {...}, session=session)

        # Method 2: Use transactional repository
        txn_repo = get_repository('users', transactional=True)
        with txn_repo.transaction() as session:
            txn_repo.create({...}, session=session)
    """

    def __init__(self, db_name: str, collection_name: str, transactional: bool = False):
        """Initialize repository.

        Args:
            db_name: Database name
            collection_name: Collection name
            transactional: If True, enables transaction support methods
        """
        self.db_name = db_name
        self.collection_name = collection_name
        self._transactional = transactional

        self._client = get_db_client()
        self._schema_loader = get_schema()
        self._schema = self._schema_loader.get_collection(collection_name)
        self._validator = SchemaValidator(collection_name)

        # Get collection reference
        self._collection = self._client.get_collection(db_name, collection_name)

        # Schema-derived settings
        self._soft_delete = self._schema_loader.has_soft_delete(collection_name)
        self._timestamps = self._schema_loader.has_timestamps(collection_name)
        self._unique_fields = self._schema_loader.get_unique_fields(collection_name)
        self._searchable_fields = self._schema_loader.get_searchable_fields(collection_name)

        # Generate dynamic methods
        self._generate_finders()

    @property
    def collection(self):
        """Get MongoDB collection."""
        if self._collection is None:
            self._collection = self._client.get_collection(self.db_name, self.collection_name)
        return self._collection

    def _generate_finders(self):
        """Generate find_by_X methods for unique and searchable fields."""
        # Generate find_by_{field} for unique fields
        for field in self._unique_fields:
            method_name = f'find_by_{field}'
            if not hasattr(self, method_name):
                setattr(self, method_name, partial(self._find_by_field, field, unique=True))

        # Generate find_by_{field} for searchable fields (if not already created)
        for field in self._searchable_fields:
            method_name = f'find_by_{field}'
            if not hasattr(self, method_name):
                setattr(self, method_name, partial(self._find_by_field, field, unique=False))

    def __getattr__(self, name: str) -> Callable:
        """Dynamically handle compound finder methods.

        Supports patterns like:
        - find_by_field1_and_field2(value1, value2) - AND condition
        - find_by_field1_or_field2(value1, value2) - OR condition
        - find_by_field1_not_field2(value1, value2) - field1=value1 AND field2 != value2
        - find_by_field1_and_field2_or_field3(v1, v2, v3) - complex conditions

        Args:
            name: Method name

        Returns:
            Callable finder method

        Raises:
            AttributeError: If method pattern is not recognized
        """
        if name.startswith('find_by_'):
            return partial(self._compound_find, name)
        raise AttributeError(f"'{type(self).__name__}' object has no attribute '{name}'")

    def _parse_compound_fields(self, method_name: str) -> List[Dict[str, Any]]:
        """Parse compound method name into field operations.

        Args:
            method_name: Method name like 'find_by_user_key_and_account_key'

        Returns:
            List of dicts with 'field', 'operator' keys
            operator: 'eq' (equals), 'ne' (not equals), 'or' (or condition)
        """
        # Remove 'find_by_' prefix
        fields_part = method_name[8:]  # len('find_by_') = 8

        # Split by _and_, _or_, _not_
        # We need to parse carefully to handle field names with underscores

        all_fields = set(self._unique_fields) | set(self._searchable_fields)
        parsed = []
        current_pos = 0
        current_operator = 'eq'  # Default operator for first field

        while current_pos < len(fields_part):
            # Find the next operator
            remaining = fields_part[current_pos:]

            # Try to match a field name
            matched_field = None
            for field in sorted(all_fields, key=len, reverse=True):  # Longest match first
                if remaining.startswith(field):
                    matched_field = field
                    break

            if matched_field:
                parsed.append({
                    'field': matched_field,
                    'operator': current_operator
                })
                current_pos += len(matched_field)

                # Check for next operator
                remaining = fields_part[current_pos:]
                if remaining.startswith('_and_'):
                    current_operator = 'eq'
                    current_pos += 5  # len('_and_')
                elif remaining.startswith('_or_'):
                    current_operator = 'or'
                    current_pos += 4  # len('_or_')
                elif remaining.startswith('_not_'):
                    current_operator = 'ne'
                    current_pos += 5  # len('_not_')
                elif remaining == '':
                    break
                else:
                    # Unknown pattern, skip one character and try again
                    current_pos += 1
            else:
                # No field matched, skip one character
                current_pos += 1

        return parsed

    def _compound_find(self, method_name: str, *args, **kwargs) -> Any:
        """Execute compound find query.

        Args:
            method_name: Method name with field patterns
            *args: Values for fields in order
            **kwargs: Field=value pairs (alternative to positional args)

        Returns:
            Document(s)
        """
        parsed_fields = self._parse_compound_fields(method_name)

        if not parsed_fields:
            raise ValueError(f"Could not parse fields from method: {method_name}")

        # Build values list from args and kwargs
        values = list(args)

        # Extract special kwargs
        unique = kwargs.pop('unique', False)
        limit = kwargs.pop('limit', 100)
        skip = kwargs.pop('skip', 0)

        # Add kwargs values in field order
        for i, pf in enumerate(parsed_fields):
            if pf['field'] in kwargs:
                if i < len(values):
                    values[i] = kwargs[pf['field']]
                else:
                    values.append(kwargs[pf['field']])

        if len(values) < len(parsed_fields):
            raise ValueError(
                f"Expected {len(parsed_fields)} values for fields "
                f"{[p['field'] for p in parsed_fields]}, got {len(values)}"
            )

        # Build query based on operators
        and_conditions = []
        or_conditions = []

        for i, pf in enumerate(parsed_fields):
            field = pf['field']
            operator = pf['operator']
            value = values[i]

            if operator == 'eq':
                and_conditions.append({field: value})
            elif operator == 'ne':
                and_conditions.append({field: {'$ne': value}})
            elif operator == 'or':
                or_conditions.append({field: value})

        # Combine conditions
        if or_conditions and and_conditions:
            # Mix of AND and OR: (and_conditions) OR (or_conditions)
            query = {
                '$or': [
                    {'$and': and_conditions} if len(and_conditions) > 1 else and_conditions[0],
                    *or_conditions
                ]
            }
        elif or_conditions:
            query = {'$or': or_conditions}
        elif len(and_conditions) > 1:
            query = {'$and': and_conditions}
        elif and_conditions:
            query = and_conditions[0]
        else:
            query = {}

        # Add soft delete filter
        if self._soft_delete:
            if '$and' in query:
                query['$and'].append({'is_deleted': {'$ne': True}})
            elif '$or' in query:
                query = {'$and': [query, {'is_deleted': {'$ne': True}}]}
            else:
                query['is_deleted'] = {'$ne': True}

        if unique:
            return self.find_one(query)
        return self.find_many(query, skip=skip, limit=limit)

    def _find_by_field(self, field: str, value: Any, unique: bool = False) -> Any:
        """Generic find by field method.

        Args:
            field: Field name
            value: Field value
            unique: If True, return single document

        Returns:
            Document(s)
        """
        query = {field: value}

        # Add soft delete filter
        if self._soft_delete:
            query['is_deleted'] = {'$ne': True}

        if unique:
            return self.find_one(query)
        return self.find_many(query)

    # =========================================================================
    # TRANSACTION Support
    # =========================================================================

    @contextmanager
    def transaction(self):
        """Context manager for database transactions.

        Usage:
            with repo.transaction() as session:
                repo.create({'name': 'John'}, session=session)
                repo.create({'name': 'Jane'}, session=session)
                # Auto-commits on success, auto-rollback on exception

        Yields:
            ClientSession for use in operations
        """
        client = self._client.client
        if not client:
            raise RuntimeError("MongoDB client not available")

        session = client.start_session()
        try:
            session.start_transaction()
            yield session
            session.commit_transaction()
            logger.debug("Transaction committed successfully")
        except Exception as e:
            session.abort_transaction()
            logger.error(f"Transaction rolled back: {e}")
            raise
        finally:
            session.end_session()

    def with_transaction(self, operations: Callable[[ClientSession], Any]) -> Any:
        """Execute operations within a transaction.

        Args:
            operations: Callable that receives session and performs operations

        Returns:
            Result of operations callable

        Usage:
            def my_operations(session):
                repo.create({'name': 'John'}, session=session)
                repo.create({'name': 'Jane'}, session=session)
                return 'done'

            result = repo.with_transaction(my_operations)
        """
        with self.transaction() as session:
            return operations(session)

    # =========================================================================
    # QUERY BUILDER
    # =========================================================================

    def query(self) -> 'QueryBuilder':
        """Get a query builder for fluent queries.

        Returns:
            QueryBuilder instance

        Usage:
            results = (repo.query()
                .where('status', 'active')
                .where_gt('age', 18)
                .order_by('created_at', 'desc')
                .limit(10)
                .get())
        """
        from tc_db_base.query_builder import QueryBuilder
        return QueryBuilder(self)

    def where(self, field: str, value: Any = None, operator: str = 'eq') -> 'QueryBuilder':
        """Start a query with a where condition.

        Shortcut for repo.query().where(...)

        Args:
            field: Field name
            value: Field value
            operator: Comparison operator

        Returns:
            QueryBuilder instance
        """
        return self.query().where(field, value, operator)

    # =========================================================================
    # CREATE Operations
    # =========================================================================

    def create(self, data: Dict[str, Any], validate: bool = True, session=None) -> str:
        """Create a new document.

        Args:
            data: Document data
            validate: Validate against schema
            session: MongoDB session for transactions

        Returns:
            Inserted document ID as string

        Raises:
            ValidationError: If validation fails
        """
        if validate:
            self._validator.validate_or_raise(data)

        # Apply defaults and auto fields
        doc = self._validator.apply_defaults(data)
        doc = self._validator.apply_auto_fields(doc, is_update=False)

        result = self.collection.insert_one(doc, session=session)
        return str(result.inserted_id)

    def create_many(self, documents: List[Dict[str, Any]], validate: bool = True, session=None) -> List[str]:
        """Create multiple documents.

        Args:
            documents: List of documents
            validate: Validate against schema
            session: MongoDB session for transactions

        Returns:
            List of inserted IDs
        """
        prepared_docs = []
        for doc in documents:
            if validate:
                self._validator.validate_or_raise(doc)

            prepared = self._validator.apply_defaults(doc)
            prepared = self._validator.apply_auto_fields(prepared, is_update=False)
            prepared_docs.append(prepared)

        result = self.collection.insert_many(prepared_docs, session=session)
        return [str(id) for id in result.inserted_ids]

    # =========================================================================
    # READ Operations
    # =========================================================================

    def find_by_id(self, id: str, exclude_sensitive: bool = True) -> Optional[Dict]:
        """Find document by ID.

        Args:
            id: Document ID
            exclude_sensitive: Exclude sensitive fields

        Returns:
            Document or None
        """
        try:
            projection = self._validator.get_projection(exclude_sensitive)
            doc = self.collection.find_one({'_id': ObjectId(id)}, projection or None)
            if doc:
                return self._validator.sanitize(doc, remove_sensitive=False)
            return None
        except Exception:
            return None

    def find_one(self, query: Dict[str, Any], exclude_sensitive: bool = True) -> Optional[Dict]:
        """Find single document.

        Args:
            query: Query filter
            exclude_sensitive: Exclude sensitive fields

        Returns:
            Document or None
        """
        # Add soft delete filter
        if self._soft_delete and 'is_deleted' not in query:
            query = {**query, 'is_deleted': {'$ne': True}}

        projection = self._validator.get_projection(exclude_sensitive)
        doc = self.collection.find_one(query, projection or None)
        if doc:
            return self._validator.sanitize(doc, remove_sensitive=False)
        return None

    def find_many(
        self,
        query: Dict[str, Any] = None,
        skip: int = 0,
        limit: int = 100,
        sort: List[tuple] = None,
        exclude_sensitive: bool = True
    ) -> List[Dict]:
        """Find multiple documents.

        Args:
            query: Query filter
            skip: Documents to skip
            limit: Maximum documents
            sort: Sort specification [(field, direction), ...]
            exclude_sensitive: Exclude sensitive fields

        Returns:
            List of documents
        """
        query = query or {}

        # Add soft delete filter
        if self._soft_delete and 'is_deleted' not in query:
            query['is_deleted'] = {'$ne': True}

        # Apply limit cap
        settings = self._schema_loader.settings
        max_limit = settings.get('max_limit', 1000)
        limit = min(limit, max_limit)

        projection = self._validator.get_projection(exclude_sensitive)
        cursor = self.collection.find(query, projection or None)

        if sort:
            cursor = cursor.sort(sort)
        if skip:
            cursor = cursor.skip(skip)
        if limit:
            cursor = cursor.limit(limit)

        return [self._validator.sanitize(doc, remove_sensitive=False) for doc in cursor]

    def find(self, query: Dict[str, Any] = None):
        """Find documents (returns cursor for chaining).

        Args:
            query: Query filter

        Returns:
            PyMongo cursor
        """
        query = query or {}
        if self._soft_delete and 'is_deleted' not in query:
            query['is_deleted'] = {'$ne': True}
        return self.collection.find(query)

    def count(self, query: Dict[str, Any] = None) -> int:
        """Count documents.

        Args:
            query: Query filter

        Returns:
            Document count
        """
        query = query or {}
        if self._soft_delete and 'is_deleted' not in query:
            query['is_deleted'] = {'$ne': True}

        if query:
            return self.collection.count_documents(query)
        return self.collection.estimated_document_count()

    def exists(self, query: Dict[str, Any]) -> bool:
        """Check if document exists.

        Args:
            query: Query filter

        Returns:
            True if exists
        """
        if self._soft_delete:
            query = {**query, 'is_deleted': {'$ne': True}}
        return self.collection.find_one(query, {'_id': 1}) is not None

    # =========================================================================
    # UPDATE Operations
    # =========================================================================

    def update_one(
        self,
        query: Dict[str, Any],
        data: Dict[str, Any],
        upsert: bool = False,
        validate: bool = True,
        session=None
    ) -> int:
        """Update single document.

        Args:
            query: Query filter
            data: Fields to update
            upsert: Create if not exists
            validate: Validate against schema
            session: MongoDB session for transactions

        Returns:
            Modified count
        """
        if validate:
            self._validator.validate_or_raise(data, partial=True)

        # Apply auto fields (updated_at)
        update_data = self._validator.apply_auto_fields(data, is_update=True)

        result = self.collection.update_one(query, {'$set': update_data}, upsert=upsert, session=session)
        return result.modified_count

    def update_many(
        self,
        query: Dict[str, Any],
        data: Dict[str, Any],
        validate: bool = True,
        session=None
    ) -> int:
        """Update multiple documents.

        Args:
            query: Query filter
            data: Fields to update
            validate: Validate against schema
            session: MongoDB session for transactions

        Returns:
            Modified count
        """
        if validate:
            self._validator.validate_or_raise(data, partial=True)

        update_data = self._validator.apply_auto_fields(data, is_update=True)
        result = self.collection.update_many(query, {'$set': update_data})
        return result.modified_count

    def update_by_id(self, id: str, data: Dict[str, Any], validate: bool = True) -> int:
        """Update document by ID.

        Args:
            id: Document ID
            data: Fields to update
            validate: Validate against schema

        Returns:
            Modified count
        """
        try:
            return self.update_one({'_id': ObjectId(id)}, data, validate=validate)
        except Exception:
            return 0

    def upsert(self, query: Dict[str, Any], data: Dict[str, Any]) -> bool:
        """Update or insert document.

        Args:
            query: Query filter
            data: Document data

        Returns:
            True if upserted
        """
        return self.update_one(query, data, upsert=True) >= 0

    # =========================================================================
    # DELETE Operations
    # =========================================================================

    def delete_one(self, query: Dict[str, Any], session=None) -> int:
        """Delete single document (soft delete if enabled).

        Args:
            query: Query filter
            session: MongoDB session for transactions

        Returns:
            Deleted/modified count
        """
        if self._soft_delete:
            return self.update_one(query, {'is_deleted': True}, validate=False, session=session)
        result = self.collection.delete_one(query, session=session)
        return result.deleted_count

    def delete_many(self, query: Dict[str, Any], session=None) -> int:
        """Delete multiple documents (soft delete if enabled).

        Args:
            query: Query filter
            session: MongoDB session for transactions

        Returns:
            Deleted/modified count
        """
        if self._soft_delete:
            return self.update_many(query, {'is_deleted': True}, validate=False, session=session)
        result = self.collection.delete_many(query, session=session)
        return result.deleted_count

    def delete_by_id(self, id: str, session=None) -> bool:
        """Delete document by ID.

        Args:
            id: Document ID
            session: MongoDB session for transactions

        Returns:
            True if deleted
        """
        try:
            return self.delete_one({'_id': ObjectId(id)}, session=session) > 0
        except Exception:
            return False

    def hard_delete(self, query: Dict[str, Any], session=None) -> int:
        """Permanently delete documents (bypass soft delete).

        Args:
            query: Query filter
            session: MongoDB session for transactions

        Returns:
            Deleted count
        """
        result = self.collection.delete_many(query, session=session)
        return result.deleted_count

    def restore(self, query: Dict[str, Any], session=None) -> int:
        """Restore soft-deleted documents.

        Args:
            query: Query filter
            session: MongoDB session for transactions

        Returns:
            Restored count
        """
        if not self._soft_delete:
            return 0
        return self.collection.update_many(
            {**query, 'is_deleted': True},
            {'$set': {'is_deleted': False, 'updated_at': datetime.now(timezone.utc)}},
            session=session
        ).modified_count

    # =========================================================================
    # SEARCH Operations
    # =========================================================================

    def search(
        self,
        text: str,
        fields: List[str] = None,
        limit: int = 20
    ) -> List[Dict]:
        """Search across searchable fields.

        Args:
            text: Search text
            fields: Fields to search (defaults to searchable_fields)
            limit: Maximum results

        Returns:
            List of matching documents
        """
        fields = fields or self._searchable_fields
        if not fields:
            return []

        # Build $or query with regex for each field
        or_conditions = []
        for field in fields:
            or_conditions.append({field: {'$regex': text, '$options': 'i'}})

        query = {'$or': or_conditions}
        if self._soft_delete:
            query['is_deleted'] = {'$ne': True}

        return self.find_many(query, limit=limit)

    def search_by_fields(self, **kwargs) -> List[Dict]:
        """Search by multiple field values.

        Args:
            **kwargs: Field=value pairs

        Returns:
            List of matching documents
        """
        query = {}
        for field, value in kwargs.items():
            if field in self._searchable_fields or field in self._unique_fields:
                query[field] = value

        return self.find_many(query)

    # =========================================================================
    # AGGREGATION Operations
    # =========================================================================

    def aggregate(self, pipeline: List[Dict]) -> List[Dict]:
        """Run aggregation pipeline.

        Args:
            pipeline: Aggregation pipeline

        Returns:
            Aggregation results
        """
        results = list(self.collection.aggregate(pipeline))
        return [self._validator.sanitize(doc) for doc in results]

    def group_by(
        self,
        field: str,
        match: Dict = None,
        count_field: str = 'count'
    ) -> List[Dict]:
        """Group documents by field.

        Args:
            field: Field to group by
            match: Optional match filter
            count_field: Name for count field

        Returns:
            List of {_id: field_value, count: n}
        """
        pipeline = []

        if match:
            if self._soft_delete:
                match = {**match, 'is_deleted': {'$ne': True}}
            pipeline.append({'$match': match})
        elif self._soft_delete:
            pipeline.append({'$match': {'is_deleted': {'$ne': True}}})

        pipeline.append({
            '$group': {
                '_id': f'${field}',
                count_field: {'$sum': 1}
            }
        })

        return self.aggregate(pipeline)

    def count_by(self, field: str, match: Dict = None) -> Dict[str, int]:
        """Count documents grouped by field.

        Args:
            field: Field to group by
            match: Optional match filter

        Returns:
            Dict of {field_value: count}
        """
        results = self.group_by(field, match)
        return {r['_id']: r['count'] for r in results}

    def distinct(self, field: str, query: Dict = None) -> List:
        """Get distinct values for field.

        Args:
            field: Field name
            query: Optional filter

        Returns:
            List of distinct values
        """
        query = query or {}
        if self._soft_delete and 'is_deleted' not in query:
            query['is_deleted'] = {'$ne': True}
        return self.collection.distinct(field, query)

    # =========================================================================
    # INDEX Operations
    # =========================================================================

    def ensure_indexes(self):
        """Create indexes defined in schema."""
        indexes = self._schema_loader.get_indexes(self.collection_name)

        for index_name, index_config in indexes.items():
            try:
                fields = index_config.get('fields', [])
                if not fields:
                    continue

                # Build index keys
                keys = [(f, ASCENDING) for f in fields]

                # Build options
                options = {'name': index_name}
                if index_config.get('unique'):
                    options['unique'] = True
                if index_config.get('sparse'):
                    options['sparse'] = True
                if 'ttl' in index_config:
                    options['expireAfterSeconds'] = index_config['ttl']

                self.collection.create_index(keys, **options)
                logger.debug(f"Created index {index_name} on {self.collection_name}")

            except Exception as e:
                if 'already exists' not in str(e).lower():
                    logger.warning(f"Failed to create index {index_name}: {e}")

    def get_indexes(self) -> List[Dict]:
        """Get current indexes on collection.

        Returns:
            List of index info
        """
        return list(self.collection.list_indexes())


# Module-level repository cache
_repositories: Dict[str, DynamicRepository] = {}


def get_repository(collection_name: str, db_name: str = None, transactional: bool = False) -> Optional[DynamicRepository]:
    """Get or create a repository for a collection.

    Args:
        collection_name: Name of the collection
        db_name: Database name (optional, uses schema lookup if not specified)
        transactional: If True, creates a transactional repository

    Returns:
        DynamicRepository instance or None if collection not found
    """
    cache_key = f"{db_name or 'default'}:{collection_name}"

    if cache_key in _repositories:
        return _repositories[cache_key]

    try:
        # Try to get db_name from schema if not provided
        if not db_name:
            schema_loader = get_schema()
            found_db_name, _ = schema_loader.get_collection_with_db(collection_name)
            if found_db_name:
                db_name = found_db_name
            else:
                db_name = 'user_db'  # Default fallback

        repo = DynamicRepository(db_name, collection_name, transactional=transactional)
        _repositories[cache_key] = repo
        return repo
    except Exception as e:
        logger.warning(f"Failed to create repository for {collection_name}: {e}")
        return None

