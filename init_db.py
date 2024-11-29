from app import create_app, db
from app.models import User, Category

def init_db():
    app = create_app()
    with app.app_context():
        # Create all tables
        db.create_all()

        # Check if admin user exists
        admin = User.query.filter_by(username='admin').first()
        if not admin:
            admin = User(
                username='admin',
                email='admin@example.com',
                is_admin=True
            )
            admin.set_password('admin')  # Change this password in production!
            db.session.add(admin)

        # Add some default categories
        default_categories = ['General', 'Technology', 'News', 'Tutorial']
        for cat_name in default_categories:
            if not Category.query.filter_by(name=cat_name).first():
                category = Category(name=cat_name)
                db.session.add(category)

        db.session.commit()
        print("Database initialized successfully!")

if __name__ == '__main__':
    init_db()
