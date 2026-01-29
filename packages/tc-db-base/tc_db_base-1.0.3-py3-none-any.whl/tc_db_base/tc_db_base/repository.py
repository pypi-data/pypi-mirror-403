"""Dynamic Repository - Auto-generated repository with schema-driven methods."""

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional, Callable
from functools import partial

from bson import ObjectId
from pymongo import ASCENDING, DESCENDING

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
    """

    def __init__(self, db_name: str, collection_name: str):
        """Initialize repository.

        Args:
            db_name: Database name
            collection_name: Collection name
        """
        self.db_name = db_name
        self.collection_name = collection_name

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
    # CREATE Operations
    # =========================================================================

    def create(self, data: Dict[str, Any], validate: bool = True) -> str:
        """Create a new document.

        Args:
            data: Document data
            validate: Validate against schema

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

        result = self.collection.insert_one(doc)
        return str(result.inserted_id)

    def create_many(self, documents: List[Dict[str, Any]], validate: bool = True) -> List[str]:
        """Create multiple documents.

        Args:
            documents: List of documents
            validate: Validate against schema

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

        result = self.collection.insert_many(prepared_docs)
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
        validate: bool = True
    ) -> int:
        """Update single document.

        Args:
            query: Query filter
            data: Fields to update
            upsert: Create if not exists
            validate: Validate against schema

        Returns:
            Modified count
        """
        if validate:
            self._validator.validate_or_raise(data, partial=True)

        # Apply auto fields (updated_at)
        update_data = self._validator.apply_auto_fields(data, is_update=True)

        result = self.collection.update_one(query, {'$set': update_data}, upsert=upsert)
        return result.modified_count

    def update_many(
        self,
        query: Dict[str, Any],
        data: Dict[str, Any],
        validate: bool = True
    ) -> int:
        """Update multiple documents.

        Args:
            query: Query filter
            data: Fields to update
            validate: Validate against schema

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

    def delete_one(self, query: Dict[str, Any]) -> int:
        """Delete single document (soft delete if enabled).

        Args:
            query: Query filter

        Returns:
            Deleted/modified count
        """
        if self._soft_delete:
            return self.update_one(query, {'is_deleted': True}, validate=False)
        result = self.collection.delete_one(query)
        return result.deleted_count

    def delete_many(self, query: Dict[str, Any]) -> int:
        """Delete multiple documents (soft delete if enabled).

        Args:
            query: Query filter

        Returns:
            Deleted/modified count
        """
        if self._soft_delete:
            return self.update_many(query, {'is_deleted': True}, validate=False)
        result = self.collection.delete_many(query)
        return result.deleted_count

    def delete_by_id(self, id: str) -> bool:
        """Delete document by ID.

        Args:
            id: Document ID

        Returns:
            True if deleted
        """
        try:
            return self.delete_one({'_id': ObjectId(id)}) > 0
        except Exception:
            return False

    def hard_delete(self, query: Dict[str, Any]) -> int:
        """Permanently delete documents (bypass soft delete).

        Args:
            query: Query filter

        Returns:
            Deleted count
        """
        result = self.collection.delete_many(query)
        return result.deleted_count

    def restore(self, query: Dict[str, Any]) -> int:
        """Restore soft-deleted documents.

        Args:
            query: Query filter

        Returns:
            Restored count
        """
        if not self._soft_delete:
            return 0
        return self.collection.update_many(
            {**query, 'is_deleted': True},
            {'$set': {'is_deleted': False, 'updated_at': datetime.utcnow()}}
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

