from typing import List

from pydantic import BaseModel, Field


class MCUData(BaseModel):
    """Complete MCU cheat sheet for firmware boot essentials."""
    mcu_name: str = Field(..., description="MCU part number")
    mcu_family: str = Field("", description="MCU family or series")
    architecture: str = Field("", description="CPU architecture (e.g., ARM Cortex-M4, RISC-V, AVR)")
    core_frequency_max: str = Field("", description="Maximum core frequency")


class MemoryRegion(BaseModel):
    """Represents a memory region in the MCU."""
    name: str = Field(..., description="Memory region name (e.g., FLASH, RAM, ROM)")
    start_address: str = Field(..., description="Start address in hex (e.g., 0x08000000)")
    size: str = Field(..., description="Size in bytes or with unit (e.g., 128KB, 0x20000)")
    type: str = Field(..., description="Type: flash, ram, rom, peripheral, reserved")
    description: str = Field("", description="Additional details about this region")


class MemoryMap(BaseModel):
    memory_map: List[MemoryRegion] = Field(default_factory=list, description="Memory regions for linker script")


class ClockConfiguration(BaseModel):
    """Represents clock configuration details."""
    clock_source: str = Field(..., description="Clock source (e.g., HSI, HSE, PLL, Internal RC)")
    frequency_range: str = Field("", description="Frequency range or typical frequency")
    configuration_steps: List[str] = Field(default_factory=list, description="Steps to configure this clock")
    registers: List[str] = Field(default_factory=list, description="Key registers to configure")
    notes: str = Field("", description="Important notes about clock configuration")


class ClockConfig(BaseModel):
    clock_config: ClockConfiguration = Field(..., description="Represents clock configuration details.")


class InterruptVector(BaseModel):
    """Represents an interrupt vector entry."""
    vector_number: int = Field(..., description="Interrupt vector number or position")
    name: str = Field(..., description="Interrupt name")
    address: str = Field("", description="Vector table address in hex")
    priority: str = Field("", description="Default or configurable priority")
    description: str = Field("", description="What triggers this interrupt")


class InterruptVectors(BaseModel):
    interrupt_vectors: List[InterruptVector] = Field(..., description="Represents interrupt vector entities.")


class StartupRequirements(BaseModel):
    """Represents startup and boot requirements."""
    boot_mode: str = Field("", description="Boot mode or boot source selection")
    startup_code_location: str = Field("", description="Where startup code should be placed")
    vector_table_offset: str = Field("", description="Vector table offset register (VTOR)")
    stack_pointer_init: str = Field("", description="How to initialize stack pointer")
    minimum_init_sequence: List[str] = Field(default_factory=list, description="Minimum steps to boot")
    watchdog_handling: str = Field("", description="How to handle watchdog timer at startup")


class StartupRequirementsModel(BaseModel):
    startup_requirements: StartupRequirements = Field(..., description="Represents startup and boot requirements.")


class PeripheralInfo(BaseModel):
    """Represents a peripheral module."""
    name: str = Field(..., description="Peripheral name (e.g., GPIO, UART0, Timer1)")
    base_address: str = Field("", description="Base address in hex")
    clock_enable: str = Field("", description="How to enable clock for this peripheral")
    initialization_steps: List[str] = Field(default_factory=list, description="Basic init steps")
    key_registers: List[str] = Field(default_factory=list, description="Important registers")


class EssentialPeripherals(BaseModel):
    essential_peripherals: List[PeripheralInfo] = Field(..., description="Represents essential peripherals")


class MCULinkerScriptInfo(BaseModel):
    linker_script_notes: str = Field("", description="Notes for creating linker script")


class MCUHelloWorldSteps(BaseModel):
    hello_world_steps: List[str] = Field(default_factory=list, description="Steps to create a hello world app")


class MCUDebuggingInterface(BaseModel):
    debugging_interface: str = Field("", description="Debug interface (JTAG, SWD, etc.)")


class MCUProgrammingInterface(BaseModel):
    programming_interface: str = Field("", description="Programming interface and method")


class MCUDatasheetReferences(BaseModel):
    datasheet_references: List[str] = Field(default_factory=list, description="Key datasheet sections/pages")
