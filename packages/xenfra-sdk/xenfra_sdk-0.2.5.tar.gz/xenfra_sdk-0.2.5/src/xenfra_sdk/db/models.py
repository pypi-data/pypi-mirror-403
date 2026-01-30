# src/xenfra/db/models.py

from typing import Optional

from sqlmodel import Field, SQLModel

# --- Project Model for CLI state ---


class Project(SQLModel, table=True):
    """
    Project model storing deployment state in the SDK's local database.
    """

    __tablename__ = "projects"

    id: Optional[int] = Field(default=None, primary_key=True)
    droplet_id: int = Field(unique=True, index=True)
    name: str
    ip_address: str
    status: str
    region: str
    size: str
    # user_id is a reference to User.id in the SSO service database
    # No foreign key constraint since databases are separate in microservices architecture
    user_id: int = Field(index=True)  # Index for query performance
