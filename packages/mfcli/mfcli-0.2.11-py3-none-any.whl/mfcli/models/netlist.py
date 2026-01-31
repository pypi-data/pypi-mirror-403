from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel
from sqlalchemy import Column, TIMESTAMP, func
from sqlmodel import Field, Relationship, SQLModel

from mfcli.models.bom import BOM
from mfcli.models.pipeline_run import PipelineRun


class Pin(BaseModel):
    """Represents a single pin connection."""
    pin: str = Field(..., description="Pin number or name")
    net: str = Field(..., description="Net name this pin connects to")


class Component(BaseModel):
    """Represents a component with its pins and connections."""
    ref_des: str = Field(..., description="Reference designator (C1, R5, U2, etc.)")
    part_number: str = Field(..., description="Part number or footprint")
    pins: List[Pin] = Field(default_factory=list, description="List of pin connections")


class NetlistSchema(BaseModel):
    """Top-level schema for parsed netlist."""
    components: List[Component] = Field(default_factory=list, description="List of components")


class Netlist(SQLModel, table=True):
    __tablename__ = "netlists"
    id: Optional[int] = Field(default=None, primary_key=True)
    pipeline_run_id: int = Field(foreign_key='pipeline_runs.id', index=True, nullable=False, ondelete="CASCADE")
    pipeline_run: Optional["PipelineRun"] = Relationship()
    components: List["NetlistComponent"] = Relationship(back_populates='netlist', cascade_delete=True)
    created_at: datetime = Field(
        sa_column=Column(TIMESTAMP(timezone=True), server_default=func.now(), nullable=False)
    )


class NetlistComponent(SQLModel, table=True):
    __tablename__ = "netlist_components"
    id: Optional[int] = Field(default=None, primary_key=True)
    netlist_id: int = Field(foreign_key='netlists.id', index=True, nullable=False, ondelete="CASCADE")
    netlist: Optional["Netlist"] = Relationship(back_populates='components')
    pins: List["NetlistPin"] = Relationship(back_populates='netlist_component', cascade_delete=True)
    ref_des: str = Field(..., max_length=100, nullable=False)
    part_number: str = Field(max_length=255, nullable=False, index=True)
    bom_entry_id: Optional[int] = Field(foreign_key='bom.id', index=True, ondelete='CASCADE')
    bom_entry: Optional["BOM"] = Relationship()


class NetlistPin(SQLModel, table=True):
    __tablename__ = "netlist_pins"
    id: Optional[int] = Field(default=None, primary_key=True)
    netlist_component_id: int = Field(foreign_key='netlist_components.id', index=True, nullable=False, ondelete="CASCADE")
    netlist_component: NetlistComponent = Relationship()
    pin: str = Field(..., max_length=100, nullable=False)
    net: str = Field(..., max_length=100, nullable=False)
