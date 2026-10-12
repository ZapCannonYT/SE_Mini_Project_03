import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.db import Base, get_db, make_engine
from app.core.security import create_access_token, hash_password
from app.main import app
from app.models.user import Role, User


@pytest.fixture
def engine():
    """Fresh in-memory SQLite database for each test."""
    eng = make_engine("sqlite://", poolclass=StaticPool)

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
    Seed the default admin user required by auth tests.
    """
    TestingSessionLocal = sessionmaker(
        bind=engine,
        autoflush=False,
        expire_on_commit=False,
    )

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


@pytest.fixture
def client():
    """FastAPI test client."""
    return TestClient(app)


@pytest.fixture
def auth_headers(db):
    """auth_headers(Role.PLANNER) -> Authorization header for a user with that role."""

    def make(role: Role) -> dict:
        email = f"{role.value}@test.local"

        user = db.scalar(
            select(User).where(User.email == email)
        )

        if user is None:
            user = User(
                name=f"Test {role.value}",
                email=email,
                password_hash="not-used",
                role=role,
            )

            db.add(user)
            db.commit()
            db.refresh(user)

        token = create_access_token(
            subject=str(user.id),
            role=role.value,
        )

        return {
            "Authorization": f"Bearer {token}"
        }

    return make