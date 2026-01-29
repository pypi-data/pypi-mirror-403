"""Example usage of tc-db-base package."""

from tc_db_base import init_db, get_repository, get_schema

# =============================================================================
# Setup: Copy examples/schema/ to your project's resources/schema/
# =============================================================================
#
# your_project/
# ├── resources/
# │   └── schema/
# │       ├── dbs.json
# │       └── dbs/
# │           └── app_db.json
# └── app.py
#
# =============================================================================


def main():
    # Initialize database connection
    db = init_db()

    # Check loaded schema
    schema = get_schema()
    print(f"Loaded databases: {schema.get_database_names()}")
    print(f"Loaded collections: {schema.get_collection_names()}")

    # Get auto-generated repository for 'users' collection
    users = get_repository('users')

    if users is None:
        print("Error: 'users' collection not found in schema.")
        print("Make sure your schema files are in resources/schema/")
        return

    # ==========================================================================
    # CREATE - Insert a new user
    # ==========================================================================
    user_data = {
        'user_id': 'usr_001',
        'email': 'john@example.com',
        'password': 'hashed_password_here',  # Always hash passwords!
        'name': 'John Doe',
        'role': 'user',
        'tags': ['developer', 'python'],
    }

    try:
        user_id = users.create(user_data)
        print(f"Created user with ID: {user_id}")
    except Exception as e:
        print(f"Create error (might already exist): {e}")

    # ==========================================================================
    # READ - Auto-generated finders based on schema
    # ==========================================================================

    # find_by_{unique_field} - returns single document
    user = users.find_by_user_id('usr_001')
    print(f"Found by user_id: {user}")

    user = users.find_by_email('john@example.com')
    print(f"Found by email: {user}")

    # find_by_{searchable_field} - returns list
    active_users = users.find_by_status('active')
    print(f"Active users count: {len(active_users)}")

    admins = users.find_by_role('admin')
    print(f"Admin users count: {len(admins)}")

    # ==========================================================================
    # SEARCH - Search across multiple fields
    # ==========================================================================
    results = users.search('john', limit=10)
    print(f"Search results for 'john': {len(results)}")

    # ==========================================================================
    # UPDATE - Update a user
    # ==========================================================================
    users.update_by_id(user_id, {'name': 'John Smith'})
    print("User updated")

    # ==========================================================================
    # AGGREGATION - Count by field
    # ==========================================================================
    role_counts = users.count_by('role')
    print(f"Users by role: {role_counts}")

    status_counts = users.count_by('status')
    print(f"Users by status: {status_counts}")

    # ==========================================================================
    # DELETE - Soft delete (if enabled in schema)
    # ==========================================================================
    # users.delete_by_id(user_id)  # Soft deletes - sets is_deleted=True
    # users.hard_delete({'user_id': 'usr_001'})  # Permanent delete


if __name__ == '__main__':
    main()

