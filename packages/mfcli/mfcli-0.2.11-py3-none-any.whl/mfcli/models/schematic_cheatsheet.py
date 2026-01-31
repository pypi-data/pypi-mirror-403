from typing import List, Dict, Optional

from pydantic import BaseModel, Field


class ClockSource(BaseModel):
    """Clock source information."""
    name: str = Field(..., description="Clock source name (e.g., 'HSE', 'LSE', 'PLL')")
    frequency: str = Field("", description="Clock frequency (e.g., '16MHz', '32.768kHz')")
    source_type: str = Field("", description="Type: crystal, oscillator, RC, external")
    components: List[str] = Field(default_factory=list, description="Associated components (crystals, caps, etc.)")


class MCUSummary(BaseModel):
    """MCU configuration summary."""
    mcu_part: str = Field("", description="MCU part number")
    clock_sources: List[ClockSource] = Field(default_factory=list, description="Clock configuration")
    reset_circuit: str = Field("", description="Reset circuit description (supervisor IC, RC, button, etc.)")
    boot_configuration: str = Field("", description="Boot mode pins and configuration")
    programming_interface: str = Field("", description="Programming interface description (SWD, JTAG, etc.)")
    notes: str = Field("", description="Additional MCU configuration notes")


class PinMapping(BaseModel):
    """Single pin to net mapping."""
    pin_number: str = Field(..., description="MCU pin number or name")
    net_name: str = Field(..., description="Net name from schematic")
    function: str = Field("", description="Pin function/purpose")
    direction: str = Field("", description="Input/Output/Bidirectional")


class PinMap(BaseModel):
    """Pin mappings for meaningful/named nets only."""
    pins: List[PinMapping] = Field(default_factory=list, description="List of pin to net mappings")
    notes: str = Field("", description="Additional notes about pin assignments")


class BusDevice(BaseModel):
    """Device on a communication bus."""
    device_name: str = Field(..., description="Device name or part number")
    ref_des: str = Field(..., description="Reference designator")
    address: str = Field("", description="Bus address (for I2C) or chip select (for SPI)")
    irq_pin: str = Field("", description="Interrupt pin net name")
    reset_pin: str = Field("", description="Reset pin net name")
    enable_pin: str = Field("", description="Enable/chip enable pin net name")
    other_signals: Dict[str, str] = Field(default_factory=dict, description="Other control signals")


class BusDefinition(BaseModel):
    """Communication bus definition."""
    bus_type: str = Field(..., description="Bus type: I2C, SPI, UART, CAN, etc.")
    bus_name: str = Field("", description="Bus instance name (e.g., 'I2C1', 'SPI2')")
    signal_nets: Dict[str, str] = Field(default_factory=dict, description="Signal to net mapping (e.g., {'SCL': 'I2C_SCL', 'SDA': 'I2C_SDA'})")
    devices: List[BusDevice] = Field(default_factory=list, description="Devices connected to this bus")
    notes: str = Field("", description="Additional bus notes")


class BusMap(BaseModel):
    """Map of all communication buses."""
    buses: List[BusDefinition] = Field(default_factory=list, description="List of communication buses")


class Peripheral(BaseModel):
    """External peripheral/component requiring driver."""
    name: str = Field(..., description="Peripheral name/description")
    part_number: str = Field("", description="Part number")
    ref_des: str = Field("", description="Reference designator")
    interface: str = Field("", description="Interface type (I2C, SPI, GPIO, etc.)")
    driver_target: str = Field("", description="Suggested driver or library")
    notes: str = Field("", description="Integration notes")


class PeripheralList(BaseModel):
    """List of peripherals requiring drivers."""
    peripherals: List[Peripheral] = Field(default_factory=list, description="List of peripherals")


class VoltageRail(BaseModel):
    """Power rail information."""
    rail_name: str = Field(..., description="Rail name (e.g., '3V3', 'VBAT', '1V8')")
    voltage: str = Field(..., description="Nominal voltage")
    source: str = Field("", description="Power source (LDO, buck converter, external, etc.)")
    enable_signal: str = Field("", description="Enable signal net name")
    power_good_signal: str = Field("", description="Power good/status signal")
    loads: List[str] = Field(default_factory=list, description="Major loads on this rail")


class PowerSequencing(BaseModel):
    """Power and sequencing information."""
    voltage_rails: List[VoltageRail] = Field(default_factory=list, description="Voltage rails")
    sequencing_requirements: str = Field("", description="Power-up/down sequencing requirements")
    notes: str = Field("", description="Additional power notes")


class ConstraintsGotchas(BaseModel):
    """Design constraints and gotchas."""
    constraints: List[str] = Field(default_factory=list, description="Design constraints")
    gotchas: List[str] = Field(default_factory=list, description="Gotchas, errata references, workarounds")
    recommendations: List[str] = Field(default_factory=list, description="Design recommendations")


class ConnectorPin(BaseModel):
    """Single connector pin."""
    pin_number: str = Field(..., description="Pin number on connector")
    net_name: str = Field(..., description="Net name")
    signal_name: str = Field("", description="Signal name/function")
    direction: str = Field("", description="Signal direction")
    notes: str = Field("", description="Pin notes")


class ConnectorPinout(BaseModel):
    """Connector pinout table."""
    ref_des: str = Field(..., description="Connector reference designator")
    connector_type: str = Field("", description="Connector type/part number")
    description: str = Field("", description="Connector purpose")
    pins: List[ConnectorPin] = Field(default_factory=list, description="Pin definitions")


class ConnectorPinouts(BaseModel):
    """All connector pinouts."""
    connectors: List[ConnectorPinout] = Field(default_factory=list, description="List of connectors")
