from functools import lru_cache

from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, Session as dbSession

from mfcli.models.base import Base
from mfcli.models.bom import BOM

from mfcli.utils.config import get_config
from mfcli.utils.directory_manager import app_dirs

config = get_config()


@lru_cache
def get_db_url() -> str:
    return f"sqlite:///{app_dirs.app_data_dir / "multifactor.db"}"


engine = create_engine(
    get_db_url(),
    pool_pre_ping=True,
    pool_recycle=1800,
    pool_size=10,
    max_overflow=20,
    pool_timeout=30
)


@event.listens_for(engine, "connect")
def enable_sqlite_fk(dbapi_conn, conn_record):
    cursor = dbapi_conn.cursor()
    cursor.execute("PRAGMA foreign_keys=ON;")
    cursor.close()


Session = sessionmaker(bind=engine)
session = dbSession(engine)


def create_orm():
    engine.connect()
    Base.metadata.create_all(engine)
