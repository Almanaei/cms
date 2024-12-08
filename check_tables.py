from flask.cli import FlaskGroup
from app import create_app, db

app = create_app()

def check_tables():
    with app.app_context():
        # Get all table names
        inspector = db.inspect(db.engine)
        tables = inspector.get_table_names()
        
        print("\nDatabase Tables:")
        print("----------------")
        for table in tables:
            print(f"- {table}")
            # Get columns for each table
            columns = inspector.get_columns(table)
            for col in columns:
                print(f"  • {col['name']} ({col['type']})")
            print()

if __name__ == '__main__':
    try:
        check_tables()
    except Exception as e:
        print(f"Error: {e}")
