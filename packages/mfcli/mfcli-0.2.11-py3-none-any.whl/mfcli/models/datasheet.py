from typing import Optional

from sqlmodel import SQLModel, Field


class Datasheet(SQLModel, table=True):
    __tablename__ = "datasheets"
    id: Optional[int] = Field(default=None, primary_key=True)
    part_number: str = Field(index=True, nullable=False, max_length=100, unique=False)
    datasheet: str = Field(index=True, nullable=False, max_length=500, unique=False)
