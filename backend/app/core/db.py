from collections.abc import Iterator

from sqlalchemy import create_engine, event
from sqlalchemy.engine import Engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.core.config import settings


class Base(DeclarativeBase):
    """Base class for all SQLAlchemy models."""


def make_engine(url: str, **kwargs) -> Engine:
    if url.startswith("sqlite"):
        kwargs.setdefault("connect_args", {"check_same_thread": False})
    return create_engine(url, **kwargs)


@event.listens_for(Engine, "connect")
def _enable_sqlite_foreign_keys(dbapi_connection, _record) -> None:
    # SQLite ignores foreign keys unless this is switched on for each connection.
    if dbapi_connection.__class__.__module__.startswith("sqlite3"):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()


engine = make_engine(settings.database_url)

SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    expire_on_commit=False,
)


def get_db() -> Iterator[Session]:
    """FastAPI dependency: one session per request."""
    db = SessionLocal()

    try:
        yield db
    finally:
        db.close()


def init_db(bind: Engine = engine) -> None:
    """Create tables and seed the default admin user."""

    # Import models only after Base has been fully created.
    import app.models  # noqa: F401

    from app.core.security import hash_password
    from app.models.user import Role, User

    Base.metadata.create_all(bind=bind)

    with Session(bind) as db:
        admin = (
            db.query(User)
            .filter(User.email == settings.admin_email)
            .first()
        )

        if admin is None:
            admin = User(
                name="Admin",
                email=settings.admin_email,
                password_hash=hash_password(settings.admin_password),
                role=Role.ADMIN,
                is_active=True,
            )

            db.add(admin)
            db.commit()