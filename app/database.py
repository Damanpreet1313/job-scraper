from contextlib import contextmanager
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

from app.config import DATABASE_URL

# PostgreSQL connection pooling: use QueuePool with sensible defaults
# SQLite doesn't support pooling params; ignore for sqlite
if DATABASE_URL.startswith("postgresql"):
    engine = create_engine(
        DATABASE_URL,
        pool_size=5,
        max_overflow=10,
        pool_pre_ping=True,  # validates connections before use
        pool_recycle=3600,   # recycle after 1 hour
    )
else:
    connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}
    engine = create_engine(DATABASE_URL, connect_args=connect_args)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def init_db():
    from app import models  # noqa: F401 (ensures models are registered)
    Base.metadata.create_all(bind=engine)
    _ensure_columns()


def _ensure_columns():
    """create_all() only creates tables that don't exist yet — it never
    alters an existing table. Since jobs.db is committed to the repo and
    persists across runs, any new column added to models.py needs to be
    added here too, or it'll silently be missing on the already-existing
    table."""
    from sqlalchemy import inspect, text

    inspector = inspect(engine)
    if "jobs" not in inspector.get_table_names():
        return

    existing_cols = {col["name"] for col in inspector.get_columns("jobs")}
    needed_cols = {
        "match_reason": "TEXT",
        "posted_date_parsed": "DATETIME",
        "cross_source_hash": "VARCHAR(64)",
    }

    with engine.connect() as conn:
        for col_name, col_type in needed_cols.items():
            if col_name not in existing_cols:
                conn.execute(text(f"ALTER TABLE jobs ADD COLUMN {col_name} {col_type}"))
        conn.commit()


@contextmanager
def get_db():
    """Database session context manager for use in application code."""
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def get_db_dependency():
    """FastAPI dependency that yields a session (for route handlers)."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
