import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.db import Base, get_db, init_db, make_engine
from app.core.security import create_access_token
from app.main import app
from app.models import Role, User


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


@pytest.fixture
def client(engine):
    """API client wired to the test database instead of dfip.db."""
    testing_session = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)

    def override_get_db():
        session = testing_session()
        try:
            yield session
        finally:
            session.close()

    app.dependency_overrides[get_db] = override_get_db
    yield TestClient(app)
    app.dependency_overrides.pop(get_db, None)


@pytest.fixture
def auth_headers(db):
    """auth_headers(Role.PLANNER) -> Authorization header for a user with that role."""

    def make(role: Role) -> dict:
        email = f"{role.value}@test.local"
        user = db.scalar(select(User).where(User.email == email))
        if user is None:
            user = User(name=f"Test {role.value}", email=email, password_hash="not-used", role=role)
            db.add(user)
            db.commit()
        token = create_access_token(subject=str(user.id), role=role.value)
        return {"Authorization": f"Bearer {token}"}

    return make
