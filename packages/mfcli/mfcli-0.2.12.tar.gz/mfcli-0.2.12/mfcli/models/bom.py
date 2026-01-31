from datetime import datetime

from pydantic import BaseModel
from sqlalchemy import Column, func, TIMESTAMP

from mfcli.models.file import File

from sqlmodel import SQLModel, Field, Relationship
from typing import Optional


class BOMSchema(BaseModel):
    # Required core fields
    reference: str = Field(..., description="Reference designators (C1, R3, U2, etc.)")
    value: str = Field(..., description="Electrical value or part name (10kΩ, MSPM0L1306)")
    quantity: int = Field(..., description="Quantity of identical components")
    description: Optional[str] = Field(None, description="General text describing component")

    # Optional fields
    manufacturer: Optional[str] = Field(None, description="Manufacturer name")
    mpn: Optional[str] = Field(None, description="Manufacturer part number")
    lifecycle_status: Optional[str] = Field(None, description="Maturity (Active / NRND / Obsolete)")
    supplier: Optional[str] = Field(None, description="Distributor / supplier")
    supplier_part: Optional[str] = Field(None, description="Supplier SKU or catalog number")
    supplier_unit_price: Optional[float] = Field(None, description="Unit cost")
    supplier_subtotal: Optional[float] = Field(None, description="Quantity × unit cost")
    revision_id: Optional[str] = Field(None, description="Design revision identifier")
    revision_state: Optional[str] = Field(None, description="Engineering state (Released / Draft)")
    revision_status: Optional[str] = Field(None, description="Workflow status (Approved / Pending)")


class BOM(SQLModel, table=True):
    __tablename__ = "bom"

    id: Optional[int] = Field(default=None, primary_key=True)
    file_id: int = Field(
        foreign_key="files.id",
        index=True,
        nullable=False,
        ondelete="CASCADE"
    )

    # Relationship
    file: Optional["File"] = Relationship()

    # Required core fields
    reference: str = Field(max_length=100, nullable=False)
    value: str = Field(max_length=255, nullable=False)
    quantity: int = Field(nullable=False)
    description: Optional[str] = Field(default=None, max_length=600, nullable=True)

    # Optional fields
    manufacturer: Optional[str] = Field(default=None, max_length=255)
    mpn: Optional[str] = Field(default=None, max_length=255)
    lifecycle_status: Optional[str] = Field(default=None, max_length=50)
    supplier: Optional[str] = Field(default=None, max_length=255)
    supplier_part: Optional[str] = Field(default=None, max_length=255)
    supplier_unit_price: Optional[float] = Field(default=None)
    supplier_subtotal: Optional[float] = Field(default=None)
    revision_id: Optional[str] = Field(default=None, max_length=50)
    revision_state: Optional[str] = Field(default=None, max_length=50)
    revision_status: Optional[str] = Field(default=None, max_length=100)
    datasheet: Optional[str] = Field(default=None, nullable=True, max_length=500)

    # Timestamps
    created_at: datetime = Field(
        sa_column=Column(TIMESTAMP(timezone=True), server_default=func.now(), nullable=False)
    )
    updated_at: datetime = Field(
        sa_column=Column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    )
