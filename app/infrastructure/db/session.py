from collections.abc import Iterator

from sqlalchemy import Engine, create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.settings import Settings


def build_engine(database_url: str) -> Engine:
    return create_engine(database_url, future=True)


def build_session_factory(database_url: str) -> sessionmaker[Session]:
    return sessionmaker(bind=build_engine(database_url), expire_on_commit=False)


def get_session() -> Iterator[Session]:
    settings = Settings()
    session_factory = build_session_factory(settings.database_url)
    with session_factory() as session:
        yield session
