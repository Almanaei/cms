import psycopg2
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv('.env.development')

# Get database URI from environment
db_uri = os.getenv('SQLALCHEMY_DATABASE_URI')
print(f"Attempting to connect with URI: {db_uri}")

try:
    # Parse the URI to get connection parameters
    db_uri = db_uri.replace('postgresql://', '')
    user_pass, host_db = db_uri.split('@')
    user, password = user_pass.split(':')
    host, db = host_db.split('/')

    # Try to connect
    conn = psycopg2.connect(
        dbname=db,
        user=user,
        password=password,
        host=host
    )
    print("Successfully connected to PostgreSQL!")
    conn.close()
except Exception as e:
    print(f"Error: {str(e)}")
