from typing import List, Optional

from pydantic import BaseModel, Field
from sqlmodel import SQLModel, Field as DBField, Relationship

from mfcli.models.pipeline_run import PipelineRun


# DB Models

class FunctionalBlock(SQLModel, table=True):
    __tablename__ = 'functional_blocks'
    id: Optional[int] = DBField(default=None, primary_key=True)
    pipeline_run_id: int = DBField(
        foreign_key="pipeline_runs.id",
        index=True,
        nullable=False,
        ondelete="CASCADE"
    )
    pipeline_run: Optional["PipelineRun"] = Relationship()
    name: str = DBField(max_length=255, nullable=False, index=True)
    description: str = DBField(nullable=False)
    components: List["FunctionalBlockComponent"] = Relationship(back_populates='functional_block', cascade_delete=True)


class FunctionalBlockComponent(SQLModel, table=True):
    __tablename__ = 'functional_block_components'
    id: Optional[int] = DBField(default=None, primary_key=True)
    functional_block_id: int = DBField(
        foreign_key="functional_blocks.id",
        index=True,
        nullable=False,
        ondelete="CASCADE"
    )
    functional_block: Optional["FunctionalBlock"] = Relationship(back_populates='components')
    ref: str = DBField(max_length=45, nullable=False)


class FunctionalBlocks(BaseModel):
    functional_blocks: list[str] = Field(..., description="Names of functional blocks")


# Pydantic models

class PinInfo(BaseModel):
    """Represents pin configuration information."""
    pin_number: str = Field(..., description="Pin number or identifier")
    pin_name: str = Field(..., description="Pin name or signal name")
    direction: str = Field("", description="Pin direction: input, output, bidirectional, power, ground")
    pull_config: str = Field("", description="Pull-up/pull-down configuration: pull-up, pull-down, none, external")
    voltage_level: str = Field("", description="Voltage level (e.g., 3.3V, 5V, 1.8V)")
    function: str = Field("", description="Pin function description")
    connected_to: str = Field("", description="What this pin connects to")
    alternate_functions: List[str] = Field(default_factory=list, description="Alternative pin functions")


class ConnectorInfo(BaseModel):
    """Represents connector information."""
    connector_ref: str = Field(..., description="Connector reference designator (e.g., J1, P2)")
    connector_type: str = Field("", description="Connector type (e.g., USB-C, JST-XH, header)")
    pin_count: int = Field(0, description="Number of pins in connector")
    pins: List[PinInfo] = Field(default_factory=list, description="Pin information for connector")
    description: str = Field("", description="Connector description and purpose")


class FunctionalBlockMeta(BaseModel):
    name: str = Field(..., description="Name of the functional block (e.g., 'Power Supply', 'USB Interface')")
    description: str = Field(..., description="Detailed description of what this block does")
    components: List[str] = Field(default_factory=list, description="Reference designators of components in this block")


class FBPins(BaseModel):
    pins: List[PinInfo] = Field(default_factory=list, description="Pin information for this functional block")


class FBConnectors(BaseModel):
    connectors: List[ConnectorInfo] = Field(default_factory=list, description="Connectors associated with this block")


class FBVoltageRails(BaseModel):
    voltage_rails: List[str] = Field(default_factory=list,
                                     description="Voltage rails used by this block (e.g., 3.3V, 5V)")


class FBInitializationNotes(BaseModel):
    initialization_notes: str = Field("", description="Notes on how to initialize/configure this block in firmware")


class FBDependencies(BaseModel):
    dependencies: List[str] = Field(default_factory=list, description="Other functional blocks this depends on")


class FBFirmwareRequirements(BaseModel):
    firmware_requirements: str = Field("", description="Key firmware requirements for this block")
