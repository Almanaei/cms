from app import create_app, db
from app.models import User, Role
from flask import current_app

def check_and_fix_roles():
    app = create_app()
    with app.app_context():
        print("Checking roles and permissions...")
        
        # First, ensure roles exist
        Role.insert_roles()
        
        # Get admin role
        admin_role = Role.query.filter_by(name='Admin').first()
        if not admin_role:
            print("Error: Admin role not found!")
            return
            
        # Check admin permissions
        print("\nAdmin Role Permissions:")
        permissions = admin_role.get_permissions_list()
        print("\n".join(f"- {perm}" for perm in permissions))
        
        # Check users and their roles
        print("\nChecking users and their roles:")
        users = User.query.all()
        for user in users:
            print(f"\nUser: {user.username}")
            print(f"Role: {user.role.name if user.role else 'No role'}")
            if user.role:
                print("Permissions:")
                for perm in user.role.get_permissions_list():
                    print(f"- {perm}")
                    
        print("\nDone checking roles and permissions.")

if __name__ == '__main__':
    check_and_fix_roles()
