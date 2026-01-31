#!/usr/bin/env python3
"""
PADS Netlist Parser

Parses PADS netlist files (Mentor Graphics) and extracts:
- Reference designators (ref_des)
- Part numbers/footprints
- Pin connections (pin number + net name)

Usage:
    python pads_parser.py <netlist.txt> [--output <output.json>]

Example:
    python pads_parser.py design.asc --output parsed.json
"""

from pathlib import Path
from typing import Dict

from mfcli.models.netlist import Component, NetlistSchema, Pin


# ============================================================================
# PADS Parser
# ============================================================================

class PADSParser:
    """Parser for PADS netlist files."""

    def __init__(self, pads_content: str):
        self.content = pads_content
        self.lines = [line.strip() for line in pads_content.strip().split('\n')]
        self.components: Dict[str, Component] = {}

    def parse(self) -> NetlistSchema:
        """Parse PADS content and return validated schema."""
        # Step 1: Validate header
        if not self._validate_header():
            raise ValueError("Not a valid PADS netlist file (missing *PADS-PCB* header)")

        # Step 2: Find section boundaries
        part_start, part_end = self._find_section('*PART*')
        net_start, net_end = self._find_section('*NET*')

        # Step 3: Parse components
        if part_start is not None and part_end is not None:
            self._parse_parts(part_start, part_end)

        # Step 4: Parse nets and add pins to components
        if net_start is not None and net_end is not None:
            self._parse_nets(net_start, net_end)

        # Step 5: Validate and return
        components_list = list(self.components.values())
        return NetlistSchema(components=components_list)

    def _validate_header(self) -> bool:
        """Check if file has PADS header."""
        return len(self.lines) > 0 and self.lines[0].startswith('*PADS-PCB*')

    def _find_section(self, section_name: str) -> tuple:
        """Find start and end indices of a section."""
        try:
            start_idx = self.lines.index(section_name) + 1

            # Find end of section (next TOP-LEVEL section marker or *END*)
            # Top-level markers: *PART*, *NET*, *END* (not *SIGNAL*)
            top_level_markers = ['*PART*', '*NET*', '*END*']
            end_idx = len(self.lines)
            for i in range(start_idx, len(self.lines)):
                if self.lines[i] in top_level_markers and self.lines[i] != section_name:
                    end_idx = i
                    break

            return start_idx, end_idx
        except ValueError:
            return None, None

    def _parse_parts(self, start_idx: int, end_idx: int):
        """Parse the *PART* section to extract components."""
        for i in range(start_idx, end_idx):
            line = self.lines[i]

            # Skip empty lines and section markers
            if not line or line.startswith('*'):
                continue

            # Split line into ref_des and part_number
            parts = line.split(None, 1)  # Split on first whitespace
            if len(parts) >= 1:
                ref_des = parts[0]
                part_number = parts[1] if len(parts) > 1 else ""

                # Create component
                self.components[ref_des] = Component(
                    ref_des=ref_des,
                    part_number=part_number,
                    pins=[]
                )

    def _parse_nets(self, start_idx: int, end_idx: int):
        """Parse the *NET* section to extract pin connections."""
        current_net = None

        for i in range(start_idx, end_idx):
            line = self.lines[i]

            # Skip empty lines
            if not line:
                continue

            # Check for signal/net definition
            if line.startswith('*SIGNAL*'):
                # Extract net name (everything after *SIGNAL*)
                parts = line.split(None, 1)
                if len(parts) > 1:
                    current_net = parts[1]
                continue

            # Skip other section markers
            if line.startswith('*'):
                current_net = None
                continue

            # Parse pin references if we have a current net
            if current_net:
                self._parse_pin_references(line, current_net)

    def _parse_pin_references(self, line: str, net_name: str):
        """Parse pin references from a line and add to components."""
        # Split line into individual pin references
        pin_refs = line.split()

        for pin_ref in pin_refs:
            # Skip empty strings
            if not pin_ref:
                continue

            # Pin format: RefDes.PinNumber (e.g., C1.2, R14.1)
            if '.' in pin_ref:
                parts = pin_ref.split('.', 1)
                ref_des = parts[0]
                pin_number = parts[1]

                # Add pin to component if component exists
                if ref_des in self.components:
                    pin = Pin(pin=pin_number, net=net_name)

                    # Avoid duplicates
                    existing_pins = self.components[ref_des].pins
                    if not any(p.pin == pin.pin and p.net == pin.net for p in existing_pins):
                        self.components[ref_des].pins.append(pin)


# ============================================================================
# Main Functions
# ============================================================================

def parse_pads_file(filepath: Path) -> NetlistSchema:
    """
    Parse a PADS netlist file and return validated netlist schema.
    
    Args:
        filepath: Path to PADS netlist file
        
    Returns:
        NetlistSchema with components and pins
        
    Raises:
        FileNotFoundError: If file doesn't exist
        ValidationError: If parsed data doesn't match schema
        ValueError: If file is not a valid PADS netlist
    """
    if not filepath.exists():
        raise FileNotFoundError(f"PADS netlist file not found: {filepath}")

    # Read file content
    with open(filepath, 'r', encoding='utf-8', errors='replace') as f:
        content = f.read()

    # Parse
    parser = PADSParser(content)
    schema = parser.parse()

    return schema
