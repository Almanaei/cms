from flask.cli import FlaskGroup
from app import create_app, db
from app.models import User, Role, Settings
from werkzeug.security import check_password_hash

app = create_app()

def verify_setup():
    with app.app_context():
        print("Verifying system setup...")
        
        # Check admin role
        print("\nChecking admin role...")
        admin_role = Role.query.filter_by(name='admin').first()
        if admin_role:
            print(f"✓ Admin role exists")
            print(f"  • Name: {admin_role.name}")
            print(f"  • Description: {admin_role.description}")
            print(f"  • Permissions: {hex(admin_role.permissions)}")
        else:
            print("✗ Admin role not found!")
        
        # Check admin user
        print("\nChecking admin user...")
        admin_user = User.query.filter_by(username='admin').first()
        if admin_user:
            print(f"✓ Admin user exists")
            print(f"  • Username: {admin_user.username}")
            print(f"  • Email: {admin_user.email}")
            print(f"  • Is Admin: {admin_user.is_admin}")
            print(f"  • Is Active: {admin_user.is_active}")
            print(f"  • Email Confirmed: {admin_user.email_confirmed}")
            
            # Verify password works
            test_password = 'admin123'
            if check_password_hash(admin_user.password_hash, test_password):
                print(f"✓ Password verification successful")
            else:
                print(f"✗ Password verification failed!")
        else:
            print("✗ Admin user not found!")
        
        # Check settings
        print("\nChecking system settings...")
        settings = Settings.query.all()
        if settings:
            print(f"✓ Found {len(settings)} system settings:")
            for setting in settings:
                print(f"  • {setting.key}: {setting.value} ({setting.type})")
        else:
            print("✗ No settings found!")

if __name__ == '__main__':
    try:
        verify_setup()
    except Exception as e:
        print(f"Error: {e}")
