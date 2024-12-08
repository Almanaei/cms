from flask import Flask
from app import create_app
import os
import shutil

app = create_app()

# List of expected migration files (same as in check_migration.py)
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
        
        # Create backup directory
        backup_dir = os.path.join(os.path.dirname(__file__), 'migrations', 'backup')
        if not os.path.exists(backup_dir):
            os.makedirs(backup_dir)
            print(f"Created backup directory: {backup_dir}")
        
        # Check each file in migrations directory
        for filename in os.listdir(migrations_dir):
            if filename.endswith('.py') and not filename.startswith('__'):
                filepath = os.path.join(migrations_dir, filename)
                if filename not in EXPECTED_MIGRATIONS:
                    print(f"Moving unexpected migration {filename} to backup...")
                    backup_path = os.path.join(backup_dir, filename)
                    shutil.move(filepath, backup_path)
                    print(f"✓ Moved {filename} to backup")
                else:
                    print(f"✓ Keeping expected migration: {filename}")
        
        print("\nMigration cleanup complete!")
        print("You can find backed up migrations in the migrations/backup directory")
