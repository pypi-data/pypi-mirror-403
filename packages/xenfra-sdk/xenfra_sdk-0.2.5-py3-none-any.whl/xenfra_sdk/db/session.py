# src/xenfra/db/session.py

import os
from pathlib import Path

from sqlmodel import Session, SQLModel, create_engine

# Get the app directory for the current user
# Use ~/.xenfra for cross-platform simplicity and to avoid 'click' dependency in SDK
app_dir = Path.home() / ".xenfra"
app_dir.mkdir(parents=True, exist_ok=True)
db_path = app_dir / "xenfra.db"

# For now, we will use a simple SQLite database for ease of setup.
# In production, this should be a PostgreSQL database URL from environment variables.
DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite:///{db_path}")

# Only echo SQL in development (set SQL_ECHO=1 to enable)
SQL_ECHO = os.getenv("SQL_ECHO", "0") == "1"

engine = create_engine(DATABASE_URL, echo=SQL_ECHO)


def create_db_and_tables():
    SQLModel.metadata.create_all(engine)


def get_session():
    with Session(engine) as session:
        yield session
