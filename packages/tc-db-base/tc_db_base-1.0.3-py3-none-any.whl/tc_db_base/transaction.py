"""Transaction Manager - MongoDB multi-document transaction support."""

import logging
from typing import Any, Callable, Optional, List, Dict
from contextlib import contextmanager
from functools import wraps

from pymongo.client_session import ClientSession
from pymongo.errors import PyMongoError

logger = logging.getLogger(__name__)


class TransactionError(Exception):
    """Transaction-related error."""

    def __init__(self, message: str, cause: Exception = None):
        self.message = message
        self.cause = cause
        super().__init__(message)


class TransactionContext:
    """Context object for tracking transaction state.

    Passed to operations within a transaction to provide session access.
    """

    def __init__(self, session: ClientSession):
        self.session = session
        self._committed = False
        self._rolled_back = False
        self._operations: List[str] = []

    @property
    def is_active(self) -> bool:
        """Check if transaction is still active."""
        return not self._committed and not self._rolled_back

    def add_operation(self, operation: str):
        """Track an operation for debugging."""
        self._operations.append(operation)

    @property
    def operations(self) -> List[str]:
        """Get list of operations performed."""
        return self._operations.copy()


class TransactionManager:
    """Manages MongoDB transactions.

    Provides context manager and decorator patterns for transactions.

    Usage:
        # Context manager
        with transaction() as txn:
            users.create({'name': 'John'}, session=txn.session)
            accounts.create({'user_id': user_id}, session=txn.session)

        # Decorator
        @transactional
        def create_user_with_account(name, txn=None):
            user_id = users.create({'name': name}, session=txn.session)
            accounts.create({'user_id': user_id}, session=txn.session)
            return user_id

        # Manual control
        txn = TransactionManager()
        txn.begin()
        try:
            # operations...
            txn.commit()
        except:
            txn.rollback()
    """

    def __init__(self, client=None):
        """Initialize transaction manager.

        Args:
            client: MongoDB client (uses default if not provided)
        """
        self._client = client
        self._session: Optional[ClientSession] = None
        self._context: Optional[TransactionContext] = None

    @property
    def client(self):
        """Get MongoDB client."""
        if self._client is None:
            from tc_db_base.client import get_db_client
            db_client = get_db_client()
            self._client = db_client.client
        return self._client

    @property
    def session(self) -> Optional[ClientSession]:
        """Get current session."""
        return self._session

    @property
    def context(self) -> Optional[TransactionContext]:
        """Get current transaction context."""
        return self._context

    @property
    def is_active(self) -> bool:
        """Check if transaction is active."""
        return self._session is not None and self._context is not None and self._context.is_active

    def begin(self) -> TransactionContext:
        """Begin a new transaction.

        Returns:
            TransactionContext for the transaction

        Raises:
            TransactionError: If transaction already active or client unavailable
        """
        if self._session is not None:
            raise TransactionError("Transaction already in progress")

        if not self.client:
            raise TransactionError("MongoDB client not available")

        try:
            self._session = self.client.start_session()
            self._session.start_transaction()
            self._context = TransactionContext(self._session)
            logger.debug("Transaction started")
            return self._context

        except PyMongoError as e:
            logger.error(f"Failed to start transaction: {e}")
            raise TransactionError("Failed to start transaction", cause=e)

    def commit(self):
        """Commit the current transaction.

        Raises:
            TransactionError: If no active transaction
        """
        if not self._session or not self._context:
            raise TransactionError("No active transaction to commit")

        try:
            self._session.commit_transaction()
            self._context._committed = True
            logger.debug(f"Transaction committed ({len(self._context.operations)} operations)")

        except PyMongoError as e:
            logger.error(f"Failed to commit transaction: {e}")
            raise TransactionError("Failed to commit transaction", cause=e)

        finally:
            self._cleanup()

    def rollback(self):
        """Rollback the current transaction.

        Raises:
            TransactionError: If no active transaction
        """
        if not self._session or not self._context:
            raise TransactionError("No active transaction to rollback")

        try:
            self._session.abort_transaction()
            self._context._rolled_back = True
            logger.debug(f"Transaction rolled back ({len(self._context.operations)} operations)")

        except PyMongoError as e:
            logger.error(f"Failed to rollback transaction: {e}")
            raise TransactionError("Failed to rollback transaction", cause=e)

        finally:
            self._cleanup()

    def _cleanup(self):
        """Clean up session resources."""
        if self._session:
            try:
                self._session.end_session()
            except Exception:
                pass
            self._session = None
        self._context = None

    @contextmanager
    def transaction(self):
        """Context manager for transactions.

        Usage:
            with txn_manager.transaction() as txn:
                users.create({...}, session=txn.session)
                orders.create({...}, session=txn.session)

        Yields:
            TransactionContext
        """
        context = self.begin()
        try:
            yield context
            self.commit()
        except Exception as e:
            self.rollback()
            raise

    def __enter__(self) -> TransactionContext:
        """Enter context manager."""
        return self.begin()

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Exit context manager."""
        if exc_type is not None:
            self.rollback()
            return False
        self.commit()
        return False


# Thread-local storage for current transaction
import threading
_current_transaction = threading.local()


def get_current_transaction() -> Optional[TransactionContext]:
    """Get the current active transaction context (if any).

    Returns:
        TransactionContext or None
    """
    return getattr(_current_transaction, 'context', None)


def set_current_transaction(context: Optional[TransactionContext]):
    """Set the current transaction context.

    Args:
        context: TransactionContext or None
    """
    _current_transaction.context = context


@contextmanager
def transaction(client=None):
    """Context manager for database transactions.

    Usage:
        from tc_db_base import transaction

        with transaction() as txn:
            users.create({'name': 'John'}, session=txn.session)
            accounts.create({'user_id': user_id}, session=txn.session)
            # Auto-commits on success, auto-rollback on exception

    Args:
        client: Optional MongoDB client

    Yields:
        TransactionContext
    """
    manager = TransactionManager(client)
    context = manager.begin()

    # Set as current transaction
    previous = get_current_transaction()
    set_current_transaction(context)

    try:
        yield context
        manager.commit()
    except Exception:
        manager.rollback()
        raise
    finally:
        set_current_transaction(previous)


def transactional(func: Callable = None, *, on_error: str = 'rollback'):
    """Decorator to run a function within a transaction.

    Usage:
        @transactional
        def create_user_with_account(name, txn=None):
            user_id = users.create({'name': name}, session=txn.session)
            accounts.create({'user_id': user_id}, session=txn.session)
            return user_id

        # Call normally - transaction is automatic
        user_id = create_user_with_account('John')

        # Or pass existing transaction
        with transaction() as txn:
            create_user_with_account('John', txn=txn)
            create_user_with_account('Jane', txn=txn)

    Args:
        func: Function to wrap
        on_error: 'rollback' (default) or 'raise'

    Returns:
        Wrapped function
    """
    def decorator(fn: Callable) -> Callable:
        @wraps(fn)
        def wrapper(*args, **kwargs):
            # Check if transaction context already provided
            if 'txn' in kwargs and kwargs['txn'] is not None:
                return fn(*args, **kwargs)

            # Check for current active transaction
            current = get_current_transaction()
            if current is not None:
                kwargs['txn'] = current
                return fn(*args, **kwargs)

            # Create new transaction
            with transaction() as txn:
                kwargs['txn'] = txn
                return fn(*args, **kwargs)

        return wrapper

    if func is not None:
        return decorator(func)
    return decorator


class UnitOfWork:
    """Unit of Work pattern for grouping operations.

    Tracks changes and commits them atomically.

    Usage:
        uow = UnitOfWork()

        uow.register_new('users', {'name': 'John', 'email': 'john@example.com'})
        uow.register_new('accounts', {'user_id': 'u123', 'balance': 0})
        uow.register_update('users', {'_id': user_id}, {'status': 'active'})
        uow.register_delete('sessions', {'user_id': user_id})

        uow.commit()  # All operations in single transaction
    """

    def __init__(self):
        self._new: List[Dict] = []
        self._updated: List[Dict] = []
        self._deleted: List[Dict] = []
        self._committed = False

    def register_new(self, collection: str, document: Dict):
        """Register a new document to insert.

        Args:
            collection: Collection name
            document: Document to insert
        """
        self._new.append({
            'collection': collection,
            'document': document
        })

    def register_update(self, collection: str, query: Dict, update: Dict):
        """Register a document update.

        Args:
            collection: Collection name
            query: Query to find document
            update: Update data
        """
        self._updated.append({
            'collection': collection,
            'query': query,
            'update': update
        })

    def register_delete(self, collection: str, query: Dict):
        """Register a document deletion.

        Args:
            collection: Collection name
            query: Query to find document(s)
        """
        self._deleted.append({
            'collection': collection,
            'query': query
        })

    def commit(self) -> Dict[str, Any]:
        """Commit all registered operations in a transaction.

        Returns:
            Results dict with inserted_ids, modified_count, deleted_count
        """
        if self._committed:
            raise TransactionError("UnitOfWork already committed")

        from tc_db_base import get_repository

        results = {
            'inserted_ids': [],
            'modified_count': 0,
            'deleted_count': 0
        }

        with transaction() as txn:
            # Inserts
            for op in self._new:
                repo = get_repository(op['collection'])
                if repo:
                    doc_id = repo.create(op['document'], session=txn.session)
                    results['inserted_ids'].append(doc_id)
                    txn.add_operation(f"INSERT {op['collection']}")

            # Updates
            for op in self._updated:
                repo = get_repository(op['collection'])
                if repo:
                    count = repo.update_one(op['query'], op['update'], session=txn.session)
                    results['modified_count'] += count
                    txn.add_operation(f"UPDATE {op['collection']}")

            # Deletes
            for op in self._deleted:
                repo = get_repository(op['collection'])
                if repo:
                    count = repo.delete_one(op['query'], session=txn.session)
                    results['deleted_count'] += count
                    txn.add_operation(f"DELETE {op['collection']}")

        self._committed = True
        return results

    def rollback(self):
        """Clear all pending operations without committing."""
        self._new.clear()
        self._updated.clear()
        self._deleted.clear()

    @property
    def pending_operations(self) -> int:
        """Get count of pending operations."""
        return len(self._new) + len(self._updated) + len(self._deleted)

    def __repr__(self) -> str:
        return f"UnitOfWork(new={len(self._new)}, updated={len(self._updated)}, deleted={len(self._deleted)})"
