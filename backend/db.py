from __future__ import annotations

import os
from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from backend.config import settings


class Base(DeclarativeBase):
    pass


DATABASE_URL = settings.get_database_url()

# Managed MySQL providers (e.g. Aiven) require TLS. Set DB_SSL_CA to the path of the
# provider's CA certificate to enable it; local/dev connections are unaffected.
_connect_args: dict = {}
_ssl_ca = os.getenv("DB_SSL_CA")
if _ssl_ca and DATABASE_URL.startswith("mysql"):
    _connect_args["ssl"] = {"ca": _ssl_ca}

engine = create_engine(DATABASE_URL, pool_pre_ping=True, future=True, connect_args=_connect_args)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine, future=True)


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
