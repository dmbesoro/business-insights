import pytest

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.config import settings
from app.db.base import Base
import app.models  # Register models


@pytest.fixture
def db_session():
    test_database_url = settings.DATABASE_URL.replace(
        "/business_insights",
        "/business_insights_test",
    )

    engine = create_engine(
        test_database_url,
        pool_pre_ping=True,
    )

    TestingSessionLocal = sessionmaker(
        bind=engine,
        autoflush=False,
        autocommit=False,
    )

    Base.metadata.create_all(bind=engine)

    db = TestingSessionLocal()

    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)
        engine.dispose()