import pytest
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.db import Base, get_db, make_engine
from app.core.security import hash_password
from app.main import app
from app.models.user import Role, User


@pytest.fixture
def engine():
    """Fresh in-memory SQLite database for each test."""
    eng = make_engine("sqlite://", poolclass=StaticPool)

    # Create all tables
    import app.models  # noqa: F401
    Base.metadata.create_all(bind=eng)

    yield eng

    Base.metadata.drop_all(bind=eng)
    eng.dispose()


@pytest.fixture
def db(engine):
    """Database session connected to the test database."""
    TestingSessionLocal = sessionmaker(
        bind=engine,
        autoflush=False,
        expire_on_commit=False,
    )

    session = TestingSessionLocal()

    yield session

    session.close()


@pytest.fixture(autouse=True)
def override_database(engine):
    """
    Make FastAPI use the fresh test database automatically.
    Also seed the default admin user required by auth tests.
    """
    TestingSessionLocal = sessionmaker(
        bind=engine,
        autoflush=False,
        expire_on_commit=False,
    )

    # Seed test admin
    with TestingSessionLocal() as session:
        admin = User(
            name="Admin",
            email="admin@dfip.local",
            password_hash=hash_password("Admin@123"),
            role=Role.ADMIN,
            is_active=True,
        )

        session.add(admin)
        session.commit()

    def override_get_db():
        session = TestingSessionLocal()
        try:
            yield session
        finally:
            session.close()

    app.dependency_overrides[get_db] = override_get_db

    yield

    app.dependency_overrides.clear()