from flask import Flask
from flask_migrate import Migrate
from app import create_app, db
import os

app = create_app()
migrate = Migrate(app, db)

# List of expected migration files (in order)
EXPECTED_MIGRATIONS = [
    '1d7d196fd4d8_add_settings_model.py',
    '5b4109bd61e2_add_backup_model.py',
    '7713f24f6704_add_useractivitylog_and_reportdraft_.py',
    'afc23bbb572e_update_pageview_model_with_path_and_.py',
    'c567b3bea632_add_backup_schedule_model.py',
    'da6d3a183b9a_add_missing_columns_and_relationships.py',
    'f622ce7cb309_update_pageview_model_relationships.py',
    '202312080047_add_database_backup_final.py',
    '202312082143_merge_heads.py',
    '202312082146_stamp_existing_tables.py'
]

if __name__ == '__main__':
    with app.app_context():
        # Get the migrations directory
        migrations_dir = os.path.join(os.path.dirname(__file__), 'migrations', 'versions')
        
        print("\nCurrent Database State:")
        print("----------------------")
        
        # List all migration files
        print("Current migrations in directory:")
        actual_migrations = []
        for filename in sorted(os.listdir(migrations_dir)):
            if filename.endswith('.py') and not filename.startswith('__'):
                actual_migrations.append(filename)
                status = "✓" if filename in EXPECTED_MIGRATIONS else "⚠️ (unexpected)"
                print(f"{status} {filename}")
        
        # Check for missing expected migrations
        print("\nMissing expected migrations:")
        missing = False
        for expected in EXPECTED_MIGRATIONS:
            if expected not in actual_migrations:
                print(f"❌ {expected}")
                missing = True
        if not missing:
            print("None - all expected migrations are present")
        
        # Get current revision from database
        from flask_migrate import current
        current_rev = current()
        
        print(f"\nCurrent database revision: {current_rev}")
        if current_rev:
            print("Database is initialized with migrations")
            # Check if current revision is expected
            current_file = next((f for f in actual_migrations if current_rev in f), None)
            if current_file in EXPECTED_MIGRATIONS:
                print("Current revision is an expected migration")
            else:
                print("⚠️ Warning: Current revision is not in the expected migrations list")
        else:
            print("Database might be empty or not initialized")
