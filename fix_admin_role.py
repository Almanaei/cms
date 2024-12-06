from app import create_app, db
from app.models import User, Role
from flask import current_app

def fix_admin_role():
    app = create_app()
    with app.app_context():
        print("Fixing admin user role...")
        
        # First, ensure roles exist
        Role.insert_roles()
        
        # Get admin role
        admin_role = Role.query.filter_by(name='Admin').first()
        if not admin_role:
            print("Error: Admin role not found!")
            return
            
        # Find admin user and update role
        admin_user = User.query.filter_by(username='admin').first()
        if not admin_user:
            print("Error: Admin user not found!")
            return
            
        # Update role
        old_role = admin_user.role.name if admin_user.role else "No role"
        admin_user.role = admin_role
        db.session.commit()
        
        print(f"\nUpdated admin user role:")
        print(f"Username: {admin_user.username}")
        print(f"Old role: {old_role}")
        print(f"New role: {admin_user.role.name}")
        print("\nPermissions:")
        for perm in admin_user.role.get_permissions_list():
            print(f"- {perm}")
            
        print("\nRole update complete.")

if __name__ == '__main__':
    fix_admin_role()
