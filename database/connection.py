"""
Database connection and session management.
"""

from sqlalchemy import create_engine, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from contextlib import contextmanager
from typing import Generator

from core.config import config

# Database engine and session setup
engine = create_engine(
    config.DATABASE_URL,
    pool_pre_ping=True,  # Verify connections before use
    pool_recycle=300,    # Recycle connections every 5 minutes
    echo=False           # Set to True for SQL debugging
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

@contextmanager
def get_db_session() -> Generator[Session, None, None]:
    """
    Context manager for database sessions with automatic cleanup.
    
    Usage:
        with get_db_session() as session:
            # Use session here
            pass
    """
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()

def init_database():
    """Initialize database tables."""
    try:
        Base.metadata.create_all(bind=engine)
        return True
    except Exception as e:
        print(f"Database initialization failed: {e}")
        return False

def test_connection() -> bool:
    """Test database connectivity."""
    try:
        with get_db_session() as session:
            session.execute(text("SELECT 1"))
        return True
    except Exception as e:
        print(f"Database connection test failed: {e}")
        return False 