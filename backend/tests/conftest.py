import pytest
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.db import Base, init_db, make_engine


@pytest.fixture
def engine():
    """Fresh in-memory SQLite database for each test."""
    eng = make_engine("sqlite://", poolclass=StaticPool)
    init_db(bind=eng)
    yield eng
    Base.metadata.drop_all(bind=eng)
    eng.dispose()


@pytest.fixture
def db(engine):
    session = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)()
    yield session
    session.close()
