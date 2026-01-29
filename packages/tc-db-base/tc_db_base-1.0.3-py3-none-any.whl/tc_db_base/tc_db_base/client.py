"""Database Client - MongoDB connection management."""

import os
import logging
from typing import Optional, Dict, Any

from pymongo import MongoClient
from pymongo.errors import ConnectionFailure, ConfigurationError

logger = logging.getLogger(__name__)


class DatabaseClient:
    """MongoDB client with connection management."""

    _instance: Optional['DatabaseClient'] = None
    _client: Optional[MongoClient] = None
    _connected: bool = False

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if DatabaseClient._connected:
            return

    @classmethod
    def get_mongo_uri(cls) -> str:
        """Get MongoDB URI from config or environment."""
        try:
            from task_circuit_base import get_value
            return get_value('database.mongo_uri', default='mongodb://localhost:27017', env_var='MONGO_URI')
        except ImportError:
            return os.getenv('MONGO_URI', 'mongodb://localhost:27017')

    @classmethod
    def get_client_options(cls) -> Dict[str, Any]:
        """Get MongoDB client options."""
        try:
            from task_circuit_base import get_value
            return {
                'serverSelectionTimeoutMS': get_value('database.connection.server_selection_timeout_ms', default=10000),
                'connectTimeoutMS': get_value('database.connection.timeout_ms', default=10000),
                'socketTimeoutMS': get_value('database.connection.socket_timeout_ms', default=30000),
                'maxPoolSize': get_value('database.connection.max_pool_size', default=100),
                'minPoolSize': get_value('database.connection.min_pool_size', default=10),
                'retryWrites': get_value('database.connection.retry_writes', default=True),
                'retryReads': get_value('database.connection.retry_reads', default=True),
            }
        except ImportError:
            return {
                'serverSelectionTimeoutMS': 10000,
                'connectTimeoutMS': 10000,
                'socketTimeoutMS': 30000,
                'maxPoolSize': 100,
                'retryWrites': True,
                'retryReads': True,
            }

    def connect(self, uri: str = None, max_retries: int = 3) -> bool:
        """Connect to MongoDB.

        Args:
            uri: MongoDB connection URI
            max_retries: Number of connection attempts

        Returns:
            True if connected successfully
        """
        if DatabaseClient._connected and DatabaseClient._client:
            return True

        uri = uri or self.get_mongo_uri()
        options = self.get_client_options()

        for attempt in range(max_retries):
            try:
                DatabaseClient._client = MongoClient(uri, **options)
                DatabaseClient._client.admin.command('ping')
                DatabaseClient._connected = True
                logger.info("MongoDB connected successfully")
                return True

            except (ConnectionFailure, ConfigurationError) as e:
                logger.warning(f"MongoDB connection attempt {attempt + 1}/{max_retries} failed: {e}")
                if attempt == max_retries - 1:
                    logger.error(f"Failed to connect to MongoDB after {max_retries} attempts")
                    DatabaseClient._connected = False
                    return False

            except Exception as e:
                logger.error(f"Unexpected error connecting to MongoDB: {e}")
                DatabaseClient._connected = False
                return False

        return False

    @property
    def client(self) -> Optional[MongoClient]:
        """Get MongoDB client."""
        if not DatabaseClient._client:
            self.connect()
        return DatabaseClient._client

    @property
    def is_connected(self) -> bool:
        """Check if connected."""
        return DatabaseClient._connected and DatabaseClient._client is not None

    def get_database(self, db_name: str):
        """Get database by name.

        Args:
            db_name: Database name

        Returns:
            MongoDB database object
        """
        if self.client:
            return self.client[db_name]
        return None

    def get_collection(self, db_name: str, collection_name: str):
        """Get collection.

        Args:
            db_name: Database name
            collection_name: Collection name

        Returns:
            MongoDB collection object
        """
        db = self.get_database(db_name)
        if db is not None:
            return db[collection_name]
        return None

    def health_check(self) -> Dict[str, Any]:
        """Perform health check.

        Returns:
            Health status dict
        """
        if not self.client:
            return {'status': 'disconnected', 'error': 'No client'}

        try:
            self.client.admin.command('ping')
            server_info = self.client.server_info()
            return {
                'status': 'healthy',
                'version': server_info.get('version', 'unknown'),
            }
        except Exception as e:
            return {'status': 'unhealthy', 'error': str(e)}

    def disconnect(self):
        """Close connection."""
        if DatabaseClient._client:
            try:
                DatabaseClient._client.close()
                logger.info("MongoDB connection closed")
            except Exception as e:
                logger.error(f"Error closing connection: {e}")
            finally:
                DatabaseClient._client = None
                DatabaseClient._connected = False


# Module-level singleton
_db_client: Optional[DatabaseClient] = None


def get_db_client() -> DatabaseClient:
    """Get DatabaseClient singleton.

    Returns:
        DatabaseClient instance
    """
    global _db_client
    if _db_client is None:
        _db_client = DatabaseClient()
    return _db_client

