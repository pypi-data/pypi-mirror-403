"""Query Builder - Fluent API for building complex MongoDB queries."""

from typing import Any, Callable, Dict, List, Optional, Union, TYPE_CHECKING
from copy import deepcopy

if TYPE_CHECKING:
    from tc_db_base.repository import DynamicRepository


class QueryBuilder:
    """Fluent query builder for complex MongoDB queries.

    Usage:
        results = (repo.query()
            .where('status', 'active')
            .where_in('role', ['admin', 'manager'])
            .where_gt('age', 18)
            .where_between('created_at', start_date, end_date)
            .or_where('is_vip', True)
            .order_by('created_at', 'desc')
            .skip(10)
            .limit(20)
            .select(['name', 'email', 'status'])
            .get())

        # Get single
        user = repo.query().where('email', 'test@example.com').first()

        # Check existence
        exists = repo.query().where('email', 'test@example.com').exists()

        # Count
        count = repo.query().where('status', 'active').count()

        # Update
        repo.query().where('status', 'pending').update({'status': 'active'})

        # Delete
        repo.query().where('status', 'inactive').delete()
    """

    def __init__(self, repository: 'DynamicRepository'):
        """Initialize query builder.

        Args:
            repository: Repository instance
        """
        self._repository = repository
        self._conditions: List[Dict] = []
        self._or_conditions: List[Dict] = []
        self._sort: List[tuple] = []
        self._skip_count: int = 0
        self._limit_count: int = 100
        self._projection: Optional[Dict] = None
        self._distinct_field: Optional[str] = None

    # =========================================================================
    # WHERE Conditions
    # =========================================================================

    def where(self, field: str, value: Any = None, operator: str = 'eq') -> 'QueryBuilder':
        """Add where condition.

        Args:
            field: Field name
            value: Field value
            operator: Comparison operator (eq, ne, gt, gte, lt, lte, in, nin, regex, exists)

        Returns:
            Self for chaining
        """
        condition = self._build_condition(field, value, operator)
        self._conditions.append(condition)
        return self

    def where_eq(self, field: str, value: Any) -> 'QueryBuilder':
        """Where field equals value."""
        return self.where(field, value, 'eq')

    def where_ne(self, field: str, value: Any) -> 'QueryBuilder':
        """Where field not equals value."""
        return self.where(field, value, 'ne')

    def where_gt(self, field: str, value: Any) -> 'QueryBuilder':
        """Where field greater than value."""
        return self.where(field, value, 'gt')

    def where_gte(self, field: str, value: Any) -> 'QueryBuilder':
        """Where field greater than or equal to value."""
        return self.where(field, value, 'gte')

    def where_lt(self, field: str, value: Any) -> 'QueryBuilder':
        """Where field less than value."""
        return self.where(field, value, 'lt')

    def where_lte(self, field: str, value: Any) -> 'QueryBuilder':
        """Where field less than or equal to value."""
        return self.where(field, value, 'lte')

    def where_in(self, field: str, values: List[Any]) -> 'QueryBuilder':
        """Where field value is in list."""
        return self.where(field, values, 'in')

    def where_not_in(self, field: str, values: List[Any]) -> 'QueryBuilder':
        """Where field value is not in list."""
        return self.where(field, values, 'nin')

    def where_like(self, field: str, pattern: str, case_insensitive: bool = True) -> 'QueryBuilder':
        """Where field matches pattern (SQL LIKE style).

        Args:
            field: Field name
            pattern: Pattern with % wildcards (e.g., '%john%', 'john%', '%smith')
            case_insensitive: Case insensitive matching

        Returns:
            Self for chaining
        """
        # Convert SQL LIKE to regex
        regex_pattern = pattern.replace('%', '.*').replace('_', '.')
        if not pattern.startswith('%'):
            regex_pattern = '^' + regex_pattern
        if not pattern.endswith('%'):
            regex_pattern = regex_pattern + '$'

        options = 'i' if case_insensitive else ''
        self._conditions.append({field: {'$regex': regex_pattern, '$options': options}})
        return self

    def where_regex(self, field: str, pattern: str, options: str = 'i') -> 'QueryBuilder':
        """Where field matches regex pattern.

        Args:
            field: Field name
            pattern: Regex pattern
            options: Regex options (i=case insensitive, m=multiline, etc.)

        Returns:
            Self for chaining
        """
        self._conditions.append({field: {'$regex': pattern, '$options': options}})
        return self

    def where_between(self, field: str, start: Any, end: Any) -> 'QueryBuilder':
        """Where field is between start and end (inclusive).

        Args:
            field: Field name
            start: Start value
            end: End value

        Returns:
            Self for chaining
        """
        self._conditions.append({field: {'$gte': start, '$lte': end}})
        return self

    def where_null(self, field: str) -> 'QueryBuilder':
        """Where field is null or doesn't exist."""
        self._conditions.append({'$or': [{field: None}, {field: {'$exists': False}}]})
        return self

    def where_not_null(self, field: str) -> 'QueryBuilder':
        """Where field is not null and exists."""
        self._conditions.append({field: {'$ne': None, '$exists': True}})
        return self

    def where_exists(self, field: str, exists: bool = True) -> 'QueryBuilder':
        """Where field exists or not."""
        self._conditions.append({field: {'$exists': exists}})
        return self

    def where_size(self, field: str, size: int) -> 'QueryBuilder':
        """Where array field has specific size."""
        self._conditions.append({field: {'$size': size}})
        return self

    def where_elem_match(self, field: str, conditions: Dict) -> 'QueryBuilder':
        """Where array element matches conditions."""
        self._conditions.append({field: {'$elemMatch': conditions}})
        return self

    def where_all(self, field: str, values: List[Any]) -> 'QueryBuilder':
        """Where array field contains all values."""
        self._conditions.append({field: {'$all': values}})
        return self

    def where_type(self, field: str, bson_type: Union[str, int]) -> 'QueryBuilder':
        """Where field is of specific BSON type."""
        self._conditions.append({field: {'$type': bson_type}})
        return self

    def where_mod(self, field: str, divisor: int, remainder: int) -> 'QueryBuilder':
        """Where field mod divisor equals remainder."""
        self._conditions.append({field: {'$mod': [divisor, remainder]}})
        return self

    # =========================================================================
    # OR Conditions
    # =========================================================================

    def or_where(self, field: str, value: Any = None, operator: str = 'eq') -> 'QueryBuilder':
        """Add OR condition.

        Args:
            field: Field name
            value: Field value
            operator: Comparison operator

        Returns:
            Self for chaining
        """
        condition = self._build_condition(field, value, operator)
        self._or_conditions.append(condition)
        return self

    def or_where_in(self, field: str, values: List[Any]) -> 'QueryBuilder':
        """OR where field value is in list."""
        return self.or_where(field, values, 'in')

    def or_where_like(self, field: str, pattern: str) -> 'QueryBuilder':
        """OR where field matches pattern."""
        regex_pattern = pattern.replace('%', '.*').replace('_', '.')
        if not pattern.startswith('%'):
            regex_pattern = '^' + regex_pattern
        if not pattern.endswith('%'):
            regex_pattern = regex_pattern + '$'
        self._or_conditions.append({field: {'$regex': regex_pattern, '$options': 'i'}})
        return self

    # =========================================================================
    # Nested Conditions
    # =========================================================================

    def where_and(self, callback) -> 'QueryBuilder':
        """Add nested AND conditions.

        Args:
            callback: Function that receives a new QueryBuilder

        Usage:
            .where_and(lambda q: q.where('a', 1).where('b', 2))
        """
        nested = QueryBuilder(self._repository)
        callback(nested)
        if nested._conditions:
            self._conditions.append({'$and': nested._conditions})
        return self

    def where_or(self, callback) -> 'QueryBuilder':
        """Add nested OR conditions.

        Args:
            callback: Function that receives a new QueryBuilder

        Usage:
            .where_or(lambda q: q.where('a', 1).where('b', 2))
        """
        nested = QueryBuilder(self._repository)
        callback(nested)
        if nested._conditions:
            self._conditions.append({'$or': nested._conditions})
        return self

    # =========================================================================
    # Sorting & Pagination
    # =========================================================================

    def order_by(self, field: str, direction: str = 'asc') -> 'QueryBuilder':
        """Add sort order.

        Args:
            field: Field to sort by
            direction: 'asc' or 'desc'

        Returns:
            Self for chaining
        """
        from pymongo import ASCENDING, DESCENDING
        sort_dir = DESCENDING if direction.lower() == 'desc' else ASCENDING
        self._sort.append((field, sort_dir))
        return self

    def order_by_desc(self, field: str) -> 'QueryBuilder':
        """Sort by field descending."""
        return self.order_by(field, 'desc')

    def order_by_asc(self, field: str) -> 'QueryBuilder':
        """Sort by field ascending."""
        return self.order_by(field, 'asc')

    def latest(self, field: str = 'created_at') -> 'QueryBuilder':
        """Sort by field descending (latest first)."""
        return self.order_by(field, 'desc')

    def oldest(self, field: str = 'created_at') -> 'QueryBuilder':
        """Sort by field ascending (oldest first)."""
        return self.order_by(field, 'asc')

    def skip(self, count: int) -> 'QueryBuilder':
        """Skip documents.

        Args:
            count: Number to skip

        Returns:
            Self for chaining
        """
        self._skip_count = count
        return self

    def limit(self, count: int) -> 'QueryBuilder':
        """Limit results.

        Args:
            count: Maximum results

        Returns:
            Self for chaining
        """
        self._limit_count = count
        return self

    def take(self, count: int) -> 'QueryBuilder':
        """Alias for limit()."""
        return self.limit(count)

    def page(self, page_number: int, per_page: int = 20) -> 'QueryBuilder':
        """Set pagination.

        Args:
            page_number: Page number (1-based)
            per_page: Items per page

        Returns:
            Self for chaining
        """
        self._skip_count = (max(1, page_number) - 1) * per_page
        self._limit_count = per_page
        return self

    # =========================================================================
    # Projection (Select)
    # =========================================================================

    def select(self, fields: List[str]) -> 'QueryBuilder':
        """Select specific fields to return.

        Args:
            fields: List of field names

        Returns:
            Self for chaining
        """
        self._projection = {field: 1 for field in fields}
        return self

    def exclude(self, fields: List[str]) -> 'QueryBuilder':
        """Exclude specific fields from results.

        Args:
            fields: List of field names to exclude

        Returns:
            Self for chaining
        """
        self._projection = {field: 0 for field in fields}
        return self

    # =========================================================================
    # Execution Methods
    # =========================================================================

    def get(self) -> List[Dict]:
        """Execute query and return results.

        Returns:
            List of documents
        """
        query = self._build_query()
        return self._repository.find_many(
            query=query,
            skip=self._skip_count,
            limit=self._limit_count,
            sort=self._sort if self._sort else None
        )

    def all(self) -> List[Dict]:
        """Alias for get()."""
        return self.get()

    def first(self) -> Optional[Dict]:
        """Get first matching document.

        Returns:
            Document or None
        """
        query = self._build_query()
        cursor = self._repository.collection.find(query)
        if self._sort:
            cursor = cursor.sort(self._sort)
        cursor = cursor.limit(1)
        try:
            doc = next(cursor)
            return self._repository._validator.sanitize(doc)
        except StopIteration:
            return None

    def first_or_fail(self) -> Dict:
        """Get first matching document or raise exception.

        Returns:
            Document

        Raises:
            ValueError: If no document found
        """
        result = self.first()
        if result is None:
            raise ValueError(f"No document found matching query")
        return result

    def last(self) -> Optional[Dict]:
        """Get last matching document (by _id).

        Returns:
            Document or None
        """
        from pymongo import DESCENDING
        query = self._build_query()
        doc = self._repository.collection.find_one(
            query,
            sort=[('_id', DESCENDING)]
        )
        if doc:
            return self._repository._validator.sanitize(doc)
        return None

    def count(self) -> int:
        """Count matching documents.

        Returns:
            Document count
        """
        query = self._build_query()
        return self._repository.collection.count_documents(query)

    def exists(self) -> bool:
        """Check if any document matches.

        Returns:
            True if exists
        """
        query = self._build_query()
        return self._repository.collection.find_one(query, {'_id': 1}) is not None

    def distinct(self, field: str) -> List[Any]:
        """Get distinct values for field.

        Args:
            field: Field name

        Returns:
            List of distinct values
        """
        query = self._build_query()
        return self._repository.collection.distinct(field, query)

    def pluck(self, field: str) -> List[Any]:
        """Get list of values for a specific field.

        Args:
            field: Field name

        Returns:
            List of field values
        """
        results = self.select([field]).get()
        return [doc.get(field) for doc in results if field in doc]

    def chunk(self, size: int):
        """Process results in chunks (generator).

        Args:
            size: Chunk size

        Yields:
            Lists of documents
        """
        offset = 0
        while True:
            self._skip_count = offset
            self._limit_count = size
            results = self.get()
            if not results:
                break
            yield results
            offset += size

    # =========================================================================
    # Modification Methods
    # =========================================================================

    def update(self, data: Dict[str, Any]) -> int:
        """Update matching documents.

        Args:
            data: Fields to update

        Returns:
            Modified count
        """
        query = self._build_query()
        return self._repository.update_many(query, data)

    def delete(self) -> int:
        """Delete matching documents.

        Returns:
            Deleted count
        """
        query = self._build_query()
        return self._repository.delete_many(query)

    def increment(self, field: str, amount: int = 1) -> int:
        """Increment field value.

        Args:
            field: Field to increment
            amount: Amount to increment

        Returns:
            Modified count
        """
        query = self._build_query()
        result = self._repository.collection.update_many(
            query,
            {'$inc': {field: amount}}
        )
        return result.modified_count

    def decrement(self, field: str, amount: int = 1) -> int:
        """Decrement field value.

        Args:
            field: Field to decrement
            amount: Amount to decrement

        Returns:
            Modified count
        """
        return self.increment(field, -amount)

    def push(self, field: str, value: Any) -> int:
        """Push value to array field.

        Args:
            field: Array field
            value: Value to push

        Returns:
            Modified count
        """
        query = self._build_query()
        result = self._repository.collection.update_many(
            query,
            {'$push': {field: value}}
        )
        return result.modified_count

    def pull(self, field: str, value: Any) -> int:
        """Pull value from array field.

        Args:
            field: Array field
            value: Value to pull

        Returns:
            Modified count
        """
        query = self._build_query()
        result = self._repository.collection.update_many(
            query,
            {'$pull': {field: value}}
        )
        return result.modified_count

    def add_to_set(self, field: str, value: Any) -> int:
        """Add value to array if not exists.

        Args:
            field: Array field
            value: Value to add

        Returns:
            Modified count
        """
        query = self._build_query()
        result = self._repository.collection.update_many(
            query,
            {'$addToSet': {field: value}}
        )
        return result.modified_count

    # =========================================================================
    # Aggregation Shortcuts
    # =========================================================================

    def sum(self, field: str) -> float:
        """Sum field values.

        Args:
            field: Field to sum

        Returns:
            Sum value
        """
        query = self._build_query()
        pipeline = [
            {'$match': query},
            {'$group': {'_id': None, 'total': {'$sum': f'${field}'}}}
        ]
        results = list(self._repository.collection.aggregate(pipeline))
        return results[0]['total'] if results else 0

    def avg(self, field: str) -> float:
        """Average field values.

        Args:
            field: Field to average

        Returns:
            Average value
        """
        query = self._build_query()
        pipeline = [
            {'$match': query},
            {'$group': {'_id': None, 'average': {'$avg': f'${field}'}}}
        ]
        results = list(self._repository.collection.aggregate(pipeline))
        return results[0]['average'] if results else 0

    def min(self, field: str) -> Any:
        """Get minimum value.

        Args:
            field: Field name

        Returns:
            Minimum value
        """
        query = self._build_query()
        pipeline = [
            {'$match': query},
            {'$group': {'_id': None, 'min_val': {'$min': f'${field}'}}}
        ]
        results = list(self._repository.collection.aggregate(pipeline))
        return results[0]['min_val'] if results else None

    def max(self, field: str) -> Any:
        """Get maximum value.

        Args:
            field: Field name

        Returns:
            Maximum value
        """
        query = self._build_query()
        pipeline = [
            {'$match': query},
            {'$group': {'_id': None, 'max_val': {'$max': f'${field}'}}}
        ]
        results = list(self._repository.collection.aggregate(pipeline))
        return results[0]['max_val'] if results else None

    def group_by(self, field: str) -> List[Dict]:
        """Group by field and count.

        Args:
            field: Field to group by

        Returns:
            List of {_id: value, count: n}
        """
        query = self._build_query()
        pipeline = [
            {'$match': query},
            {'$group': {'_id': f'${field}', 'count': {'$sum': 1}}},
            {'$sort': {'count': -1}}
        ]
        return list(self._repository.collection.aggregate(pipeline))

    # =========================================================================
    # Query Building Helpers
    # =========================================================================

    def _build_condition(self, field: str, value: Any, operator: str) -> Dict:
        """Build a single condition."""
        operators = {
            'eq': lambda f, v: {f: v},
            'ne': lambda f, v: {f: {'$ne': v}},
            'gt': lambda f, v: {f: {'$gt': v}},
            'gte': lambda f, v: {f: {'$gte': v}},
            'lt': lambda f, v: {f: {'$lt': v}},
            'lte': lambda f, v: {f: {'$lte': v}},
            'in': lambda f, v: {f: {'$in': v}},
            'nin': lambda f, v: {f: {'$nin': v}},
            'regex': lambda f, v: {f: {'$regex': v, '$options': 'i'}},
            'exists': lambda f, v: {f: {'$exists': v}},
        }

        builder = operators.get(operator, operators['eq'])
        return builder(field, value)

    def _build_query(self) -> Dict:
        """Build final MongoDB query."""
        query = {}

        # Combine AND conditions
        if self._conditions:
            if len(self._conditions) == 1:
                query = deepcopy(self._conditions[0])
            else:
                query['$and'] = deepcopy(self._conditions)

        # Add OR conditions
        if self._or_conditions:
            if query:
                # Combine existing query with OR conditions
                query = {
                    '$and': [
                        query,
                        {'$or': deepcopy(self._or_conditions)}
                    ]
                }
            else:
                query['$or'] = deepcopy(self._or_conditions)

        # Add soft delete filter
        if self._repository._soft_delete:
            if '$and' in query:
                query['$and'].append({'is_deleted': {'$ne': True}})
            elif query:
                query = {'$and': [query, {'is_deleted': {'$ne': True}}]}
            else:
                query['is_deleted'] = {'$ne': True}

        return query

    def to_query(self) -> Dict:
        """Get the built query (for debugging).

        Returns:
            MongoDB query dict
        """
        return self._build_query()

    def explain(self) -> Dict:
        """Get query execution plan.

        Returns:
            Query explain output
        """
        query = self._build_query()
        return self._repository.collection.find(query).explain()

    def __repr__(self) -> str:
        """String representation."""
        return f"QueryBuilder(conditions={len(self._conditions)}, or={len(self._or_conditions)})"
