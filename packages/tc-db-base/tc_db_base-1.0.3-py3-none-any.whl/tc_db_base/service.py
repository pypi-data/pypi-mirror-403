"""Database Service - Main service class."""

import logging
from typing import Dict, Any, Optional, List

from tc_db_base.client import DatabaseClient, get_db_client
from tc_db_base.schema import SchemaLoader, get_schema
from tc_db_base.repository import DynamicRepository

logger = logging.getLogger(__name__)


class DatabaseService:
    """Main database service with schema-driven repository management."""

    _instance: Optional['DatabaseService'] = None
    _repositories: Dict[str, DynamicRepository] = {}

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return

        self._client = get_db_client()
        self._schema = get_schema()
        self._initialized = True

        logger.info("DatabaseService initialized")

    def connect(self) -> bool:
        """Connect to database.

        Returns:
            True if connected
        """
        return self._client.connect()

    @property
    def is_connected(self) -> bool:
        """Check if connected."""
        return self._client.is_connected

    # =========================================================================
    # Repository Access
    # =========================================================================

    def get_repository(self, collection_name: str) -> Optional[DynamicRepository]:
        """Get repository for a collection.

        Auto-creates repository based on schema.

        Args:
            collection_name: Collection name

        Returns:
            DynamicRepository or None
        """
        # Check cache
        if collection_name in DatabaseService._repositories:
            return DatabaseService._repositories[collection_name]

        # Find collection in schema
        db_name, schema = self._schema.get_collection_with_db(collection_name)
        if not db_name:
            logger.warning(f"Collection '{collection_name}' not found in schema")
            return None

        # Create repository
        repo = DynamicRepository(db_name, collection_name)
        DatabaseService._repositories[collection_name] = repo

        return repo

    def __getattr__(self, name: str) -> Optional[DynamicRepository]:
        """Allow accessing repositories as attributes.

        Example:
            db.users.find_by_email('test@example.com')
        """
        if name.startswith('_'):
            raise AttributeError(name)

        # Check if it's a collection name
        if self._schema.get_collection(name):
            return self.get_repository(name)

        raise AttributeError(f"'{type(self).__name__}' has no attribute '{name}'")

    # =========================================================================
    # Database Access
    # =========================================================================

    def get_database(self, db_name: str):
        """Get database by name.

        Args:
            db_name: Database name

        Returns:
            MongoDB database object
        """
        return self._client.get_database(db_name)

    def get_collection(self, db_name: str, collection_name: str):
        """Get raw MongoDB collection.

        Args:
            db_name: Database name
            collection_name: Collection name

        Returns:
            MongoDB collection
        """
        return self._client.get_collection(db_name, collection_name)

    # =========================================================================
    # Schema Access
    # =========================================================================

    def get_collection_names(self, db_name: str = None) -> List[str]:
        """Get all collection names.

        Args:
            db_name: Optional database filter

        Returns:
            List of collection names
        """
        return self._schema.get_collection_names(db_name)

    def get_databases(self) -> List[str]:
        """Get all database names.

        Returns:
            List of database names
        """
        return list(self._schema.databases.keys())

    # =========================================================================
    # Index Management
    # =========================================================================

    def ensure_all_indexes(self):
        """Create all indexes defined in schema."""
        logger.info("Creating indexes for all collections...")

        for db_name, coll_name, schema in self._schema.get_all_collections():
            try:
                repo = self.get_repository(coll_name)
                if repo:
                    repo.ensure_indexes()
                    logger.debug(f"Indexes ensured for {coll_name}")
            except Exception as e:
                logger.warning(f"Failed to create indexes for {coll_name}: {e}")

        logger.info("Index creation complete")

    # =========================================================================
    # Health & Stats
    # =========================================================================

    def health_check(self) -> Dict[str, Any]:
        """Perform health check.

        Returns:
            Health status dict
        """
        health = self._client.health_check()
        health['collections'] = len(self._schema.get_all_collections())
        health['repositories_cached'] = len(DatabaseService._repositories)
        return health

    def get_stats(self) -> Dict[str, Any]:
        """Get database statistics.

        Returns:
            Statistics dict
        """
        stats = {
            'connected': self.is_connected,
            'databases': {},
            'collections': {},
        }

        for db_name in self.get_databases():
            db = self.get_database(db_name)
            if db:
                try:
                    stats['databases'][db_name] = {
                        'collections': len(db.list_collection_names())
                    }
                except Exception:
                    stats['databases'][db_name] = {'status': 'error'}

        return stats

    # =========================================================================
    # Lifecycle
    # =========================================================================

    def disconnect(self):
        """Disconnect from database."""
        self._client.disconnect()
        DatabaseService._repositories.clear()
        logger.info("DatabaseService disconnected")

    def clear_cache(self):
        """Clear repository cache."""
        DatabaseService._repositories.clear()


# Module-level singletons and convenience functions
_db_service: Optional[DatabaseService] = None


def get_db() -> DatabaseService:
    """Get DatabaseService singleton.

    Returns:
        DatabaseService instance
    """
    global _db_service
    if _db_service is None:
        _db_service = DatabaseService()
    return _db_service


def init_db() -> DatabaseService:
    """Initialize and connect DatabaseService.

    Returns:
        Connected DatabaseService
    """
    db = get_db()
    if not db.is_connected:
        db.connect()
    return db


def get_repository(collection_name: str) -> Optional[DynamicRepository]:
    """Get repository for a collection.

    Convenience function.

    Args:
        collection_name: Collection name

    Returns:
        DynamicRepository or None
    """
    return get_db().get_repository(collection_name)

