import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from subarashii.db import Base

TEST_DATABASE_URL = "sqlite:///:memory:"


@pytest.fixture(scope="function")
def session():
    engine = create_engine(TEST_DATABASE_URL, echo=False, future=True)

    Base.metadata.create_all(bind=engine)

    TestingSessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)

    session = TestingSessionLocal()

    try:
        yield session
    finally:
        session.close()
