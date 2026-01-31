from typing import Dict, List, Any

from pydantic import BaseModel, Field


class DebugInterface(BaseModel):
    """Debug interface configuration from schematic."""
    interface_type: str = Field(..., description="Debug interface type: JTAG, SWD, ICSP, etc.")
    pin_count: int = Field(0, description="Number of pins in debug connector")
    pin_mapping: Dict[str, str] = Field(default_factory=dict,
                                        description="Pin number to signal mapping (e.g., {'1': 'VCC', '2': 'SWDIO'})")
    connector_type: str = Field("", description="Physical connector type (e.g., 10-pin Cortex, 20-pin JTAG)")
    voltage_level: str = Field("", description="Target voltage level (3.3V, 5V, etc.)")


class DebugTool(BaseModel):
    """Recommended debug tool/probe."""
    name: str = Field(..., description="Tool name (e.g., J-Link, ST-Link, CMSIS-DAP)")
    model: str = Field("", description="Specific model recommendation")
    purchase_links: List[str] = Field(default_factory=list, description="Where to buy")
    compatibility_notes: str = Field("", description="Why this tool is recommended")
    alternative_tools: List[str] = Field(default_factory=list, description="Alternative compatible tools")


class DriverInfo(BaseModel):
    """Driver installation information."""
    windows: Dict[str, Any] = Field(default_factory=dict,
                                    description="Windows driver info: download_url, installation_steps")
    linux: Dict[str, Any] = Field(default_factory=dict,
                                  description="Linux driver info: package_name, installation_steps")
    macos: Dict[str, Any] = Field(default_factory=dict, description="macOS driver info (optional)")


class VSCodeLaunchConfig(BaseModel):
    """VS Code launch.json configuration."""
    configuration_name: str = Field(..., description="Name for this configuration")
    configuration_type: str = Field(..., description="Debugger type: cortex-debug, cppdbg, etc.")
    launch_json: Dict[str, Any] = Field(default_factory=dict, description="Complete launch.json configuration")
    extensions_required: List[str] = Field(default_factory=list, description="Required VS Code extensions")
    setup_notes: str = Field("", description="Additional setup notes")


class GDBServerConfig(BaseModel):
    """GDB server configuration."""
    server_name: str = Field(..., description="GDB server name (e.g., JLinkGDBServer, OpenOCD)")
    command_line: str = Field("", description="Command to start GDB server")
    config_file: str = Field("", description="Configuration file content or path")
    port: int = Field(3333, description="GDB server port")


class DSTargetMCU(BaseModel):
    target_mcu: str = Field(..., description="Target MCU from schematic")


class DSAdditionalTools(BaseModel):
    additional_tools: List[str] = Field(default_factory=list, description="Additional helpful tools")


class DSTroubleshootingGuide(BaseModel):
    troubleshooting: List[str] = Field(default_factory=list, description="Common issues and solutions")


class DSQuickStartGuide(BaseModel):
    quick_start_guide: List[str] = Field(default_factory=list, description="Step-by-step quick start")
