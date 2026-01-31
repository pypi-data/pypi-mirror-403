from typing import List, Literal

from pydantic import BaseModel, Field


class ErrataIDs(BaseModel):
    ids: list[str]


class ErrataTopLevelSummary(BaseModel):
    errata_document: str = Field(..., description="Errata document name (e.g., Silicon Errata Rev 1.2 - March 2024)")
    mcu_name: str = Field(..., description="MCU name (e.g., MSPM0L1306)")
    recommendations: list[str] = Field(default_factory=list, description="Top-level firmware recommendations")


class ErrataItem(BaseModel):
    """Individual errata issue."""
    errata_id: str = Field(..., description="Errata ID/number (e.g., 'I2C_01', 'ADV0123')")
    title: str = Field(..., description="Brief title of the issue")
    affected_modules: List[str] = Field(default_factory=list, description="Affected peripherals/modules")
    severity: Literal['Critical', 'Major', 'Minor']
    description: str = Field(..., description="What the issue is")
    conditions: str = Field("", description="When/how the issue occurs")
    firmware_workaround: str = Field("", description="Firmware workaround or mitigation")
    impact: str = Field("", description="Impact on firmware operation")
    affected_revisions: List[str] = Field(default_factory=list, description="Silicon revisions affected")
