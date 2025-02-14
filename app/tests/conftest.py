import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.core.database import Base, TEST_DATABASE_URL

# Use a separate engine for the test database
test_engine = create_engine(TEST_DATABASE_URL)
TestSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)

@pytest.fixture(scope="session")
def setup_test_db():
    """Create and drop the test database."""
    Base.metadata.create_all(bind=test_engine)  # Create test tables
    yield
    Base.metadata.drop_all(bind=test_engine)  # Drop test tables after tests finish

@pytest.fixture(scope="function")
def test_db_session(setup_test_db):
    """Create a fresh test DB session for each test function."""
    db = TestSessionLocal()
    try:
        yield db
    finally:
        db.rollback()
        db.close()
