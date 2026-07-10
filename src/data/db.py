"""SQLAlchemy engine singleton for the MySQL backend."""
from __future__ import annotations

from sqlalchemy import Engine, create_engine

from config.settings import database_url

_engine: Engine | None = None


def get_engine() -> Engine:
    global _engine
    if _engine is None:
        # pre_ping: the dashboard sits idle between requests, so stale pooled
        # connections would otherwise surface as random "server has gone away".
        _engine = create_engine(database_url(), pool_pre_ping=True, pool_recycle=3600)
    return _engine
