from datetime import datetime
from typing import Optional, List

from sqlalchemy import func, UniqueConstraint, Column, DateTime
from sqlmodel import SQLModel, Field, Relationship

from mfcli.models.pipeline_run import PipelineRun


class File(SQLModel, table=True):
    __tablename__ = "files"

    __table_args__ = (
        UniqueConstraint("md5", "pipeline_run_id", name="uq_file_md5_pipeline_run"),
    )

    id: Optional[int] = Field(default=None, primary_key=True)
    pipeline_run_id: int = Field(
        foreign_key="pipeline_runs.id",
        index=True,
        nullable=False,
        ondelete="CASCADE"
    )
    pipeline_run: Optional["PipelineRun"] = Relationship()
    pdf_parts: List["PDFPart"] = Relationship(back_populates='file', cascade_delete=True)

    name: str = Field(max_length=255, nullable=False, index=True)
    type: int = Field(nullable=False, index=True)
    sub_type: Optional[int] = Field(default=None, index=True)
    mime_type: str = Field(max_length=255, nullable=False)
    md5: str = Field(max_length=32, nullable=False, index=True)
    ext: str = Field(max_length=10, min_length=2, index=True, nullable=True)
    path: str = Field(max_length=600, nullable=True)
    gemini_file_id: str = Field(max_length=40, nullable=True)
    is_datasheet: int = Field(default=0, nullable=False, index=True)

    # Database-managed timestamps
    created_at: datetime = Field(
        sa_column=Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    )
    updated_at: datetime = Field(
        sa_column=Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    )
