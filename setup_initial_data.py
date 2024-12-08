from flask.cli import FlaskGroup
from app import create_app, db
from app.models import User, Role, Settings
from datetime import datetime
import bcrypt

app = create_app()

def setup_initial_data():
    with app.app_context():
        print("Setting up initial data...")
        
        # Create admin role
        print("\nCreating roles...")
        admin_role = Role.query.filter_by(name='admin').first()
        if not admin_role:
            admin_role = Role(
                name='admin',
                description='Administrator role with full permissions',
                permissions=0xFFFFFFFF,  # All permissions
                created_at=datetime.utcnow()
            )
            db.session.add(admin_role)
            print("✓ Admin role created")
        
        # Create default admin user
        print("\nCreating admin user...")
        admin_user = User.query.filter_by(username='admin').first()
        if not admin_user:
            # Generate salt and hash password
            salt = bcrypt.gensalt()
            password_hash = bcrypt.hashpw('admin123'.encode('utf-8'), salt)
            
            admin_user = User(
                username='admin',
                email='admin@example.com',
                password_hash=password_hash.decode('utf-8'),
                is_admin=True,
                is_active=True,
                email_confirmed=True,
                created_at=datetime.utcnow(),
                role_id=admin_role.id
            )
            db.session.add(admin_user)
            print("✓ Admin user created with default password: admin123")
            print("  ⚠ Please change this password immediately after first login!")
        
        # Create default settings
        print("\nCreating default settings...")
        default_settings = {
            'site_name': ('Site Name', 'string', 'My CMS'),
            'site_description': ('Site Description', 'string', 'A powerful content management system'),
            'posts_per_page': ('Posts Per Page', 'integer', '10'),
            'allow_comments': ('Allow Comments', 'boolean', 'true'),
            'allow_registration': ('Allow Registration', 'boolean', 'true'),
            'maintenance_mode': ('Maintenance Mode', 'boolean', 'false'),
            'theme': ('Theme', 'string', 'default'),
            'analytics_enabled': ('Analytics Enabled', 'boolean', 'true'),
            'backup_enabled': ('Backup Enabled', 'boolean', 'true'),
            'backup_frequency': ('Backup Frequency', 'string', 'daily'),
        }
        
        for key, (description, type_, value) in default_settings.items():
            setting = Settings.query.filter_by(key=key).first()
            if not setting:
                setting = Settings(
                    key=key,
                    value=value,
                    type=type_,
                    description=description
                )
                db.session.add(setting)
                print(f"✓ Added setting: {key}")
        
        # Commit all changes
        try:
            db.session.commit()
            print("\n✓ Initial data setup completed successfully!")
        except Exception as e:
            db.session.rollback()
            print(f"\n✗ Error during setup: {e}")
            raise

if __name__ == '__main__':
    try:
        setup_initial_data()
    except Exception as e:
        print(f"Error: {e}")
