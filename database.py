from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import logging

logger = logging.getLogger(__name__)

# SQLite database configuration
SQLALCHEMY_DATABASE_URL = "sqlite:///./address_book.db"

# Create database engine with SQLite-specific configuration
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False}  # Allows multiple threads to access the DB
)
logger.info(f"Database engine created: {SQLALCHEMY_DATABASE_URL}")

# Session factory for creating new database sessions
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for all ORM models
Base = declarative_base()

def get_db():
    """
    Database session dependency for FastAPI.
    
    This is used as a dependency in route handlers to provide a database session.
    The session is automatically closed after the request is complete, even if an
    error occurs during request processing.
    
    Yields:
        A SQLAlchemy Session object for database operations
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()