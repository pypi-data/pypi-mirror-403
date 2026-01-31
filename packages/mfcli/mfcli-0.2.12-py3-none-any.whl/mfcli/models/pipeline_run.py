from datetime import datetime
from typing import Optional

from sqlalchemy import Integer, func, Text, Column, DateTime, ForeignKey
from sqlmodel import SQLModel, Field, Relationship

from mfcli.constants.pipeline_run_status import PIPELINE_STATUS_IN_PROGRESS
from mfcli.models.project import Project


class PipelineRun(SQLModel, table=True):
    __tablename__ = "pipeline_runs"

    id: Optional[int] = Field(default=None, primary_key=True)
    project_id: int = Field(
        sa_column=Column(
            Integer,
            ForeignKey("projects.id", ondelete="CASCADE"),
            nullable=True,
            index=True
        )
    )
    project: Optional["Project"] = Relationship(back_populates='runs')
    status: int = Field(
        sa_column=Column(Integer, nullable=False, server_default=str(PIPELINE_STATUS_IN_PROGRESS))
    )
    errors: Optional[str] = Field(default=None, sa_column=Column(Text, nullable=True))

    created_at: datetime = Field(
        sa_column=Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    )
    updated_at: datetime = Field(
        sa_column=Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    )
