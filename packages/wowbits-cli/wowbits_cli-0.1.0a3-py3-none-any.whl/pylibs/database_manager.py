from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.exc import SQLAlchemyError
from contextlib import contextmanager
from db.schema import Base
import os

class DatabaseManager:
    """
    Database manager for Supabase PostgreSQL database operations.
    Provides connection management and session handling.
    """
    
    def __init__(self):
        """
        Initialize the database manager.
        """
        # Initialize database
        self._initialize_database()
    
    def _initialize_database(self):
        """Initialize Supabase PostgreSQL database connection and create tables."""
        try:
            # Create PostgreSQL database URL
            # Load environment variables from WOWBITS_ROOT_DIR/.env
            from pylibs.env_loader import load_env_variables
            
            load_env_variables()
            database_url = os.getenv('WOWBITS_DB_CONNECTION_STRING')
            print(f"Database URL: {database_url}")
            # Create engine with PostgreSQL-specific configurations
            self.engine = create_engine(
                database_url,
                pool_size=10,  # Connection pool size
                max_overflow=20,  # Maximum overflow connections
                pool_pre_ping=True,  # Verify connections before use
                echo=False  # Set to True for SQL query logging
            )
            
            # Create all tables based on the schema
            Base.metadata.create_all(bind=self.engine)
            
            # Create session factory
            self.SessionLocal = sessionmaker(
                autocommit=False, 
                autoflush=False, 
                bind=self.engine
            )
            
            print(f"Database initialized successfully")
            
        except SQLAlchemyError as e:
            print(f"Database URL: {database_url}")
            print(f"Error initializing database: {e}")
            raise
    
    def get_session(self) -> Session:
        """
        Get a new database session.
        
        Returns:
            Session: SQLAlchemy session object
        """
        
        if self.SessionLocal is None:
            raise RuntimeError("Database not initialized. Call _initialize_database() first.")
        return self.SessionLocal()
    
    @contextmanager
    def get_session_context(self):
        """
        Context manager for database sessions.
        Automatically handles session cleanup.
        
        Usage:
            with db_manager.get_session_context() as session:
                # Use session here
                pass
        """
        session = self.get_session()
        try:
            yield session
            session.commit()
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()
    
    def create_tables(self):
        """Create all tables defined in the schema."""
        try:
            Base.metadata.create_all(bind=self.engine)
            print("All tables created successfully")
        except SQLAlchemyError as e:
            print(f"Error creating tables: {e}")
            raise
    
    def drop_tables(self):
        """Drop all tables. Use with caution!"""
        try:
            Base.metadata.drop_all(bind=self.engine)
            print("All tables dropped successfully")
        except SQLAlchemyError as e:
            print(f"Error dropping tables: {e}")
            raise
    
    def reset_database(self):
        """Reset the database by dropping and recreating all tables."""
        try:
            self.drop_tables()
            self.create_tables()
            print("Database reset successfully")
        except SQLAlchemyError as e:
            print(f"Error resetting database: {e}")
            raise
    
    def close(self):
        """Close database connections."""
        if self.engine:
            self.engine.dispose()
            print("Database connections closed")


# Global database manager instance
_db_manager = None

def get_db_manager() -> DatabaseManager:
    """
    Get or create a global database manager instance.
    
    Returns:
        DatabaseManager: Database manager instance
    """
    global _db_manager
    if _db_manager is None:
        _db_manager = DatabaseManager()
    return _db_manager

def get_session() -> Session:
    """
    Get a database session using the global database manager.
    
    Returns:
        Session: SQLAlchemy session object
    """
    db_manager = get_db_manager()
    return db_manager.get_session()

@contextmanager
def get_session_context():
    """
    Context manager for database sessions using the global database manager.
    
    Usage:
        with get_session_context() as session:
            # Use session here
            pass
    """
    db_manager = get_db_manager()
    with db_manager.get_session_context() as session:
        yield session


# Example usage and testing
if __name__ == "__main__":
    # Test database initialization
    try:
        # Initialize database manager
        db_manager = DatabaseManager()
        
        # Test session creation
        with db_manager.get_session_context() as session:
            print("Database session created successfully")
            
            # You can add test queries here
            from db.schema import Agent
            agents = session.query(Agent).all()
            print(f"Found {len(agents)} agents")
        
        # Clean up
        db_manager.close()
        print("Database test completed successfully")
            
    except Exception as e:
        print(f"Error during testing: {e}") 