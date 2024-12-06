import os
from dotenv import load_dotenv
import logging

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

try:
    # Load local environment variables
    load_dotenv('.env.development')
    logger.info("Loaded environment variables")

    # Import after loading environment variables
    from app import create_app, db
    from app.models import User, Post, Category  # Import your models

    logger.info("Imported required modules")

    app = create_app()
    logger.info("Created app instance")

    def setup_local():
        try:
            with app.app_context():
                logger.info("Creating database tables...")
                # Create all database tables
                db.create_all()
                logger.info("Database tables created successfully")
                
                # Check if admin user exists
                admin = User.query.filter_by(username='admin').first()
                if not admin:
                    # Create admin user
                    admin = User(
                        username='admin',
                        email='admin@localhost',
                        is_admin=True
                    )
                    admin.set_password('admin')
                    db.session.add(admin)
                    db.session.commit()
                    logger.info("Admin user created successfully!")
                else:
                    logger.info("Admin user already exists!")

        except Exception as e:
            logger.error(f"Error in setup_local: {str(e)}")
            raise

except Exception as e:
    logger.error(f"Error during setup: {str(e)}")
    raise

if __name__ == '__main__':
    setup_local()
