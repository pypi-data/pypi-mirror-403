from typing import Optional

from sqlalchemy import Column, Integer, ForeignKey
from sqlmodel import SQLModel, Field, Relationship


class PDFPart(SQLModel, table=True):
    __tablename__ = "pdf_parts"

    id: Optional[int] = Field(default=None, primary_key=True)
    file_id: int = Field(
        sa_column=Column(
            Integer,
            ForeignKey("files.id", ondelete="CASCADE"),
            nullable=False,
            index=True
        )
    )
    file: Optional["File"] = Relationship(back_populates='pdf_parts')
    path: str = Field(max_length=600, nullable=False)
    gemini_file_id: str = Field(max_length=40, nullable=True)
    start_page: int = Field(nullable=True)
    end_page: int = Field(nullable=True)
    title: str = Field(nullable=True)
    section_no: int = Field(nullable=True)
