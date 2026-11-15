from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.core.config import settings


class Base(DeclarativeBase):
    pass


connect_args = (
    {"check_same_thread": False}
    if settings.database_url.startswith("sqlite")
    else {}
)
pool_options = (
    {"poolclass": StaticPool}
    if settings.database_url in {"sqlite://", "sqlite:///:memory:"}
    else {}
)

engine = create_engine(
    settings.database_url, connect_args=connect_args, **pool_options
)
SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


def get_db() -> Generator[Session, None, None]:
    with SessionLocal() as session:
        yield session
