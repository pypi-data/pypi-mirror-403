#!/usr/bin/env python3
"""
Protel/Altium Designer Netlist Parser

Parses Protel/Altium Designer netlist files and extracts:
- Reference designators (ref_des)
- Part numbers/footprints
- Pin connections (pin number + net name)

Format example:
{COMPONENT PROTEL.PCB
  {DETAIL
    {SUBCOMP
      {I <footprint>.PRT <ref_des>
        {CN
        <pin> <net>
        ...
        }
      }
    }
  }
}
"""

from pathlib import Path
from typing import Dict

from mfcli.models.netlist import Component, NetlistSchema, Pin


class ProtelParser:
    """Parser for Protel/Altium Designer netlist files."""

    def __init__(self, protel_content: str):
        self.content = protel_content
        self.lines = [line.strip() for line in protel_content.strip().split('\n')]
        self.components: Dict[str, Component] = {}

    def parse(self) -> NetlistSchema:
        """Parse Protel content and return validated schema."""
        # Validate header
        if not self._validate_header():
            raise ValueError("Not a valid Protel/Altium netlist file (missing {COMPONENT PROTEL.PCB header)")

        # Parse components
        self._parse_components()

        # Validate and return
        components_list = list(self.components.values())
        return NetlistSchema(components=components_list)

    def _validate_header(self) -> bool:
        """Check if file has Protel/Altium header."""
        return len(self.lines) > 0 and '{COMPONENT PROTEL.PCB' in self.lines[0]

    def _parse_components(self):
        """Parse components from the netlist."""
        i = 0
        while i < len(self.lines):
            line = self.lines[i]
            
            # Look for component definition: {I <footprint>.PRT <ref_des>
            if line.startswith('{I ') and '.PRT ' in line:
                # Extract footprint and ref_des
                parts = line.split()
                if len(parts) >= 3:
                    footprint = parts[1]  # e.g., "0603.PRT"
                    ref_des = parts[2]    # e.g., "C1"
                    
                    # Remove .PRT extension from footprint
                    if footprint.endswith('.PRT'):
                        footprint = footprint[:-4]
                    
                    # Create component
                    self.components[ref_des] = Component(
                        ref_des=ref_des,
                        part_number=footprint,
                        pins=[]
                    )
                    
                    # Parse pins for this component
                    i = self._parse_pins(i + 1, ref_des)
                    continue
            
            i += 1

    def _parse_pins(self, start_idx: int, ref_des: str) -> int:
        """
        Parse pins for a component starting from the {CN block.
        Returns the index after parsing all pins.
        """
        i = start_idx
        in_cn_block = False
        
        while i < len(self.lines):
            line = self.lines[i]
            
            # Check if we're entering the {CN block
            if line == '{CN':
                in_cn_block = True
                i += 1
                continue
            
            # Check if we're exiting the {CN block or component block
            if line == '}':
                if in_cn_block:
                    in_cn_block = False
                    return i + 1  # Exit after {CN block closes
                else:
                    return i + 1  # Exit after component block closes
            
            # Parse pin connections within {CN block
            if in_cn_block and line:
                # Format: <pin_number> <net_name>
                # Example: "1 3V3" or "2 GND"
                parts = line.split(None, 1)
                if len(parts) >= 1:
                    pin_number = parts[0]
                    net_name = parts[1] if len(parts) > 1 else ""
                    
                    # Skip lines that don't start with a number (metadata)
                    if not pin_number or not pin_number[0].isdigit():
                        i += 1
                        continue
                    
                    # Add pin to component
                    if ref_des in self.components and net_name:
                        pin = Pin(pin=pin_number, net=net_name)
                        
                        # Avoid duplicates
                        existing_pins = self.components[ref_des].pins
                        if not any(p.pin == pin.pin and p.net == pin.net for p in existing_pins):
                            self.components[ref_des].pins.append(pin)
            
            i += 1
        
        return i


def parse_protel_file(filepath: Path) -> NetlistSchema:
    """
    Parse a Protel/Altium Designer netlist file and return validated netlist schema.
    
    Args:
        filepath: Path to Protel/Altium netlist file
        
    Returns:
        NetlistSchema with components and pins
        
    Raises:
        FileNotFoundError: If file doesn't exist
        ValidationError: If parsed data doesn't match schema
        ValueError: If file is not a valid Protel/Altium netlist
    """
    if not filepath.exists():
        raise FileNotFoundError(f"Protel/Altium netlist file not found: {filepath}")

    # Read file content
    with open(filepath, 'r', encoding='utf-8', errors='replace') as f:
        content = f.read()

    # Parse
    parser = ProtelParser(content)
    schema = parser.parse()

    return schema
