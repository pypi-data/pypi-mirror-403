from pydantic import BaseModel, Field
from typing import Optional, List


class VectorizeCheatSheetsConfig(BaseModel):
    vectorize_errata: bool = Field(default=False)
    vectorize_mcu: bool = Field(default=False)
    vectorize_debug_setup: bool = Field(default=False)
    vectorize_functional_blocks: bool = Field(default=False)


class MCUConfiguration(BaseModel):
    """Configuration for microcontrollers in the project"""
    primary_mcu: Optional[str] = Field(
        default=None, 
        description="Primary microcontroller part number (e.g., MSPM0L1306, STM32F407)"
    )
    additional_mcus: List[str] = Field(
        default_factory=list, 
        description="Additional microcontrollers in the design"
    )


class ProjectConfig(BaseModel):
    name: str
    mcu_config: Optional[MCUConfiguration] = Field(
        default=None,
        description="Microcontroller configuration for the project"
    )
    vectorize_hw_files: bool = Field(default=True)
    vectorize_datasheets: bool = Field(default=True)
    vectorize_cheat_sheets_config: VectorizeCheatSheetsConfig = Field(default_factory=VectorizeCheatSheetsConfig)
