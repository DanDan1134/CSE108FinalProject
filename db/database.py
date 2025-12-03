"""
Database connection and session management.
"""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from db.models import Base
import os

# Database file path (relative to project root, stored in db folder)
DATABASE_URL = os.getenv('DATABASE_URL', 'sqlite:///db/wordle_battle.db')

# Create engine
engine = create_engine(DATABASE_URL, echo=False)

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    """Get database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def init_database():
    """Initialize database tables."""
    Base.metadata.create_all(engine)

