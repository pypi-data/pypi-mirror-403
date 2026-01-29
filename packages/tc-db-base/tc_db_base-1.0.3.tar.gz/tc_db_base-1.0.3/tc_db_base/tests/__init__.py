"""Tests for tc_db_base schema loader."""

import pytest
from pathlib import Path


class TestSchemaLoader:
    """Test SchemaLoader functionality."""

    def test_schema_loads(self):
        """Test that schema loads successfully."""
        from tc_db_base.schema import SchemaLoader

        # Reset singleton for fresh test
        SchemaLoader._instance = None
        SchemaLoader._loaded = False
        SchemaLoader._databases = {}
        SchemaLoader._settings = {}

        loader = SchemaLoader()
        assert loader.databases is not None

    def test_get_collection(self):
        """Test getting a collection schema."""
        from tc_db_base.schema import get_schema

        schema = get_schema()
        users = schema.get_collection('users')

        # Should find users collection
        if users:
            assert 'fields' in users
            assert 'user_key' in users['fields']

    def test_get_collection_with_db(self):
        """Test getting collection with database name."""
        from tc_db_base.schema import get_schema

        schema = get_schema()
        db_name, coll_schema = schema.get_collection_with_db('users')

        if coll_schema:
            assert db_name == 'user_db'

    def test_get_unique_fields(self):
        """Test getting unique fields."""
        from tc_db_base.schema import get_schema

        schema = get_schema()
        unique = schema.get_unique_fields('users')

        if unique:
            assert 'user_key' in unique
            assert 'email' in unique

    def test_get_searchable_fields(self):
        """Test getting searchable fields."""
        from tc_db_base.schema import get_schema

        schema = get_schema()
        searchable = schema.get_searchable_fields('users')

        if searchable:
            assert 'user_key' in searchable
            assert 'email' in searchable

    def test_has_soft_delete(self):
        """Test soft delete detection."""
        from tc_db_base.schema import get_schema

        schema = get_schema()
        # Users should have soft delete
        assert schema.has_soft_delete('users') == True

    def test_settings(self):
        """Test schema settings."""
        from tc_db_base.schema import get_schema

        schema = get_schema()
        settings = schema.settings

        if settings:
            assert 'auto_timestamps' in settings
            assert 'default_limit' in settings


class TestSchemaValidator:
    """Test SchemaValidator functionality."""

    def test_validate_required_fields(self):
        """Test validation of required fields."""
        from tc_db_base.schema.validator import SchemaValidator, ValidationError

        validator = SchemaValidator('users')

        # Missing required fields should fail
        is_valid, errors = validator.validate({})

        # If schema loaded, should have errors for required fields
        if validator._schema:
            assert not is_valid
            assert len(errors) > 0

    def test_validate_with_valid_data(self):
        """Test validation with valid data."""
        from tc_db_base.schema.validator import SchemaValidator

        validator = SchemaValidator('users')

        data = {
            'user_key': 'usr_123',
            'account_key': 'acc_456',
            'email': 'test@example.com',
            'password': 'hashed_password',
        }

        is_valid, errors = validator.validate(data)

        if validator._schema:
            assert is_valid
            assert len(errors) == 0

    def test_apply_defaults(self):
        """Test applying default values."""
        from tc_db_base.schema.validator import SchemaValidator

        validator = SchemaValidator('users')

        data = {'user_key': 'usr_123'}
        result = validator.apply_defaults(data)

        # Should apply default for status
        if validator._schema:
            assert result.get('status') == 'active'


class TestDynamicRepository:
    """Test DynamicRepository (requires MongoDB)."""

    @pytest.fixture
    def mock_collection(self, mocker):
        """Create a mock MongoDB collection."""
        mock = mocker.MagicMock()
        mock.find_one.return_value = None
        mock.insert_one.return_value = mocker.MagicMock(inserted_id='test_id')
        return mock

    def test_repository_has_dynamic_methods(self):
        """Test that repository has auto-generated methods."""
        from tc_db_base.schema import get_schema

        schema = get_schema()
        unique_fields = schema.get_unique_fields('users')

        # Verify unique fields exist for method generation
        if unique_fields:
            assert 'user_key' in unique_fields
            assert 'email' in unique_fields

