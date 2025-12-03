"""
Initialize the database and create all tables.
"""
from db.database import init_database, DATABASE_URL

if __name__ == '__main__':
    print("Creating database tables...")
    init_database()
    print(f"Database initialized successfully at: {DATABASE_URL}")

