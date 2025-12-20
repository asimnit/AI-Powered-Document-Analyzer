"""
Database Configuration

Sets up SQLAlchemy engine and session management.
- Engine: Connects to PostgreSQL
- SessionLocal: Creates database sessions
- Base: Base class for all database models
"""

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

from app.core.config import settings

# Create database engine
# echo=True shows SQL queries in console (useful for learning/debugging)
engine = create_engine(
    settings.DATABASE_URL,
    echo=settings.DEBUG,
    pool_pre_ping=True,  # Check connection health before using
)

# Create SessionLocal class
# Each instance is a database session
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for all models
# All database models will inherit from this
Base = declarative_base()


def get_db():
    """
    Dependency for FastAPI routes
    
    Yields a database session and ensures it's closed after use.
    Usage in routes:
        @app.get("/items")
        def get_items(db: Session = Depends(get_db)):
            ...
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
