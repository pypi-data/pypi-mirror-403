"""Schema Loader - Load and parse database schema from JSON files."""

import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


class SchemaLoader:
    """Load and manage database schema from JSON files.

    Schema files are loaded from (in priority order):
    1. SCHEMA_PATH environment variable
    2. {cwd}/resources/schema/
    3. Parent directories /resources/schema/ (up to 5 levels)
    4. Package default tc_db_base/schema (if exists)

    Your service should provide schema files at:
        your_service/
        └── resources/
            └── schema/
                ├── dbs.json           # Main config with settings
                └── dbs/               # Individual database schemas
                    ├── user_db.json
                    └── ...
    """

    _instance: Optional['SchemaLoader'] = None
    _schema: Dict[str, Any] = {}
    _databases: Dict[str, Any] = {}
    _settings: Dict[str, Any] = {}
    _loaded: bool = False

    def __new__(cls, schema_path: str = None):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self, schema_path: str = None):
        if SchemaLoader._loaded and schema_path is None:
            return
        self._load_schema(schema_path)

    def _find_schema_directories(self) -> List[Path]:
        """Find all possible schema directories.

        Search order:
        1. SCHEMA_PATH environment variable
        2. {cwd}/resources/schema
        3. Parent directories /resources/schema (up to 5 levels)
        4. Package default tc_db_base/schema

        Returns:
            List of existing schema directories
        """
        import os
        candidates = []

        # 1. SCHEMA_PATH environment variable
        schema_env = os.getenv('SCHEMA_PATH')
        if schema_env:
            candidates.append(Path(schema_env))

        # 2. Current working directory /resources/schema
        cwd = Path.cwd()
        candidates.append(cwd / 'resources' / 'schema')

        # 3. Parent directories (up to 5 levels)
        current = cwd
        for _ in range(5):
            candidates.append(current / 'resources' / 'schema')
            if current.parent == current:
                break
            current = current.parent

        # 4. Package default (tc_db_base/schema)
        candidates.append(Path(__file__).parent)

        # Return existing directories (unique, preserving order)
        seen = set()
        result = []
        for path in candidates:
            try:
                resolved = path.resolve()
                if str(resolved) not in seen and resolved.exists() and resolved.is_dir():
                    seen.add(str(resolved))
                    result.append(resolved)
            except Exception:
                continue

        return result

    def _load_schema(self, schema_path: str = None):
        """Load schema from JSON files.

        Searches for schema in multiple locations and merges them.
        Later sources override earlier ones.
        """
        SchemaLoader._databases = {}
        SchemaLoader._settings = {}

        # Get schema directories to search
        if schema_path:
            schema_dirs = [Path(schema_path)]
        else:
            schema_dirs = self._find_schema_directories()

        logger.debug(f"Searching for schema in: {[str(d) for d in schema_dirs]}")

        # Load from each directory (later overrides earlier)
        for schema_dir in reversed(schema_dirs):  # Reverse so later dirs override
            self._load_from_directory(schema_dir)

        SchemaLoader._loaded = True
        total_collections = sum(len(colls) for colls in SchemaLoader._databases.values())
        logger.info(f"Schema loaded: {len(SchemaLoader._databases)} databases, {total_collections} collections")

    def _load_from_directory(self, schema_dir: Path):
        """Load schema from a single directory."""
        # Load main config (dbs.json)
        main_config_path = schema_dir / 'dbs.json'
        if main_config_path.exists():
            try:
                with open(main_config_path, 'r') as f:
                    main_config = json.load(f)
                # Merge settings
                SchemaLoader._settings.update(main_config.get('settings', {}))

                # Check for embedded dbs (backward compat)
                if 'dbs' in main_config:
                    for db_name, collections in main_config['dbs'].items():
                        if db_name not in SchemaLoader._databases:
                            SchemaLoader._databases[db_name] = {}
                        SchemaLoader._databases[db_name].update(collections)

            except Exception as e:
                logger.warning(f"Failed to load main config from {main_config_path}: {e}")

        # Load individual database schemas from /dbs folder
        dbs_folder = schema_dir / 'dbs'
        if dbs_folder.exists() and dbs_folder.is_dir():
            for db_file in dbs_folder.glob('*.json'):
                try:
                    with open(db_file, 'r') as f:
                        db_schema = json.load(f)
                    db_name = db_schema.get('db_name', db_file.stem)
                    collections = db_schema.get('collections', {})

                    # Merge collections
                    if db_name not in SchemaLoader._databases:
                        SchemaLoader._databases[db_name] = {}
                    SchemaLoader._databases[db_name].update(collections)

                    logger.debug(f"Loaded schema for {db_name} from {db_file}")
                except Exception as e:
                    logger.warning(f"Failed to load {db_file}: {e}")

    @property
    def schema(self) -> Dict[str, Any]:
        """Get full schema (for backward compatibility)."""
        return {
            'dbs': SchemaLoader._databases,
            'settings': SchemaLoader._settings
        }

    @property
    def databases(self) -> Dict[str, Any]:
        """Get all databases config."""
        return SchemaLoader._databases

    @property
    def settings(self) -> Dict[str, Any]:
        """Get schema settings."""
        return SchemaLoader._settings

    def get_database(self, db_name: str) -> Optional[Dict[str, Any]]:
        """Get database schema by name."""
        return self.databases.get(db_name)

    def get_collection(self, collection_name: str) -> Optional[Dict[str, Any]]:
        """Get collection schema by name (searches all databases)."""
        for db_name, db_config in self.databases.items():
            if collection_name in db_config:
                return db_config[collection_name]
        return None

    def get_collection_with_db(self, collection_name: str) -> Tuple[Optional[str], Optional[Dict]]:
        """Get collection schema with database name."""
        for db_name, db_config in self.databases.items():
            if collection_name in db_config:
                return db_name, db_config[collection_name]
        return None, None

    def get_all_collections(self) -> List[Tuple[str, str, Dict]]:
        """Get all collections with their database names."""
        result = []
        for db_name, db_config in self.databases.items():
            for coll_name, coll_schema in db_config.items():
                result.append((db_name, coll_name, coll_schema))
        return result

    def get_collection_names(self, db_name: str = None) -> List[str]:
        """Get all collection names."""
        if db_name:
            db = self.databases.get(db_name, {})
            return list(db.keys())
        names = []
        for db_config in self.databases.values():
            names.extend(db_config.keys())
        return names

    def get_database_names(self) -> List[str]:
        """Get all database names."""
        return list(self.databases.keys())

    def get_fields(self, collection_name: str) -> Dict[str, Any]:
        """Get field definitions for a collection."""
        schema = self.get_collection(collection_name)
        if schema:
            return schema.get('fields', {})
        return {}

    def get_required_fields(self, collection_name: str) -> List[str]:
        """Get required field names for a collection."""
        fields = self.get_fields(collection_name)
        return [name for name, config in fields.items() if config.get('required', False)]

    def get_unique_fields(self, collection_name: str) -> List[str]:
        """Get unique field names for a collection."""
        schema = self.get_collection(collection_name)
        if schema:
            return schema.get('unique_fields', [])
        return []

    def get_searchable_fields(self, collection_name: str) -> List[str]:
        """Get searchable field names for a collection."""
        schema = self.get_collection(collection_name)
        if schema:
            return schema.get('searchable_fields', [])
        return []

    def get_indexes(self, collection_name: str) -> Dict[str, Any]:
        """Get index definitions for a collection."""
        schema = self.get_collection(collection_name)
        if schema:
            return schema.get('indexes', {})
        return {}

    def has_soft_delete(self, collection_name: str) -> bool:
        """Check if collection uses soft delete."""
        schema = self.get_collection(collection_name)
        if schema:
            return schema.get('soft_delete', False)
        return False

    def has_timestamps(self, collection_name: str) -> bool:
        """Check if collection uses timestamps."""
        schema = self.get_collection(collection_name)
        if schema:
            return schema.get('timestamps', self.settings.get('auto_timestamps', True))
        return True

    def get_field_default(self, collection_name: str, field_name: str) -> Any:
        """Get default value for a field."""
        fields = self.get_fields(collection_name)
        field = fields.get(field_name, {})
        return field.get('default')

    def get_field_type(self, collection_name: str, field_name: str) -> Optional[str]:
        """Get field type."""
        fields = self.get_fields(collection_name)
        field = fields.get(field_name, {})
        return field.get('type')

    def get_enum_values(self, collection_name: str, field_name: str) -> Optional[List]:
        """Get enum values for a field."""
        fields = self.get_fields(collection_name)
        field = fields.get(field_name, {})
        return field.get('enum')

    def reload(self, schema_path: str = None):
        """Reload schema from files."""
        SchemaLoader._loaded = False
        SchemaLoader._databases = {}
        SchemaLoader._settings = {}
        self._load_schema(schema_path)


# Module-level singleton
_schema_loader: Optional[SchemaLoader] = None


def get_schema(schema_path: str = None) -> SchemaLoader:
    """Get SchemaLoader singleton."""
    global _schema_loader
    if _schema_loader is None:
        _schema_loader = SchemaLoader(schema_path)
    return _schema_loader

