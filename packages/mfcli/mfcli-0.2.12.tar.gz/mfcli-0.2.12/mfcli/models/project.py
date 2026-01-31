from datetime import datetime
from typing import Optional, List

from sqlalchemy import Column, DateTime, func
from sqlmodel import SQLModel, Field, Relationship

project_name_regex = r"^[A-Za-z0-9_-]+$"


class Project(SQLModel, table=True):
    __tablename__ = "projects"

    id: Optional[int] = Field(default=None, primary_key=True)
    runs: List["PipelineRun"] = Relationship(back_populates='project', cascade_delete=True)
    name: str = Field(
        nullable=False,
        unique=True,
        index=True,
        min_length=3,
        max_length=45,
        regex=project_name_regex
    )
    index_id: str = Field(index=True, unique=True)
    repo_dir: str = Field(index=True, unique=True)
    created_at: datetime = Field(
        sa_column=Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    )
