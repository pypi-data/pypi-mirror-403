"""Pytest configuration for tc_db_base tests."""

import pytest
import sys
from pathlib import Path

# Add tc_db_base to path
sys.path.insert(0, str(Path(__file__).parent.parent))


@pytest.fixture(autouse=True)
def reset_schema_loader():
    """Reset SchemaLoader singleton before each test."""
    from tc_db_base.schema import SchemaLoader

    # Store original state
    original_instance = SchemaLoader._instance
    original_loaded = SchemaLoader._loaded
    original_databases = SchemaLoader._databases.copy() if SchemaLoader._databases else {}
    original_settings = SchemaLoader._settings.copy() if SchemaLoader._settings else {}

    yield

    # Restore (optional - comment out if you want fresh state per test)
    # SchemaLoader._instance = original_instance
    # SchemaLoader._loaded = original_loaded
    # SchemaLoader._databases = original_databases
    # SchemaLoader._settings = original_settings


@pytest.fixture
def sample_user_data():
    """Sample user data for testing."""
    return {
        'user_key': 'usr_test123',
        'account_key': 'acc_test456',
        'email': 'test@example.com',
        'password': 'hashed_password_here',
        'name': 'Test User',
        'status': 'active',
    }


@pytest.fixture
def sample_pond_data():
    """Sample pond data for testing."""
    return {
        'pond_id': 'pond_test123',
        'account_key': 'acc_test456',
        'name': 'Test Pond',
        'area_sqm': 1000,
        'status': 'active',
    }

