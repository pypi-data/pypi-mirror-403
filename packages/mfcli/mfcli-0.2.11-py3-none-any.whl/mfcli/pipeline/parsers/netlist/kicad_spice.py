"""
KiCad SPICE Netlist Parser

Parses KiCad-generated SPICE netlist files (.cir) and extracts:
- Reference designators (ref_des)
- Part numbers
- Pin connections (inferred from node positions)

SPICE Format:
    RefDes Node1 Node2 ... PartNumber
    Example: R14 Net-_J3-Pad1_ Net-_LED2-A-Pad6_ CRCW0402330RJNED

Pin Mapping:
    - 2-terminal components (R, C): pin1=node1, pin2=node2
    - 3-terminal components (Q, transistors): pin1=node1, pin2=node2, pin3=node3
    - Multi-terminal: numbered sequentially
"""

from pathlib import Path
from typing import Dict

from mfcli.models.netlist import Component, NetlistSchema, Pin


# ============================================================================
# KiCad SPICE Parser
# ============================================================================

class KiCadSpiceParser:
    """Parser for KiCad SPICE netlist files."""

    def __init__(self, spice_content: str):
        self.content = spice_content
        self.lines = [line.strip() for line in spice_content.strip().split('\n')]
        self.components: Dict[str, Component] = {}

    def parse(self) -> NetlistSchema:
        """Parse SPICE content and return validated schema."""
        for line in self.lines:
            # Skip empty lines
            if not line:
                continue

            # Skip SPICE directives (start with .)
            if line.startswith('.'):
                continue

            # Parse component line
            self._parse_component_line(line)

        # Convert to list and return
        components_list = list(self.components.values())
        return NetlistSchema(components=components_list)

    def _parse_component_line(self, line: str):
        """
        Parse a component line from SPICE netlist.
        Format: RefDes Node1 Node2 ... NodeN PartNumber
        """
        tokens = line.split()

        if len(tokens) < 2:
            return  # Invalid line

        ref_des = tokens[0]

        # Last token is part number, middle tokens are nodes
        if len(tokens) == 2:
            # Special case: component with no connections (placeholder)
            # Example: LED2 __LED2
            part_number = tokens[1]
            nodes = []
        else:
            part_number = tokens[-1]
            nodes = tokens[1:-1]

        # Skip placeholder components (nodes starting with __)
        if nodes and all(node.startswith('__') for node in nodes):
            return

        # Create component
        component = Component(
            ref_des=ref_des,
            part_number=part_number,
            pins=[]
        )

        # Map nodes to pins
        # Pin numbers are inferred from node position (1, 2, 3, ...)
        for pin_num, node_name in enumerate(nodes, start=1):
            # Skip placeholder nodes
            if node_name.startswith('__'):
                continue

            pin = Pin(
                pin=str(pin_num),
                net=node_name
            )
            component.pins.append(pin)

        # Only add component if it has pins (skip placeholders)
        if component.pins:
            self.components[ref_des] = component


# ============================================================================
# Main Function
# ============================================================================

def parse_kicad_spice_file(filepath: Path) -> NetlistSchema:
    """
    Parse a KiCad SPICE netlist file and return validated netlist schema.
    
    Args:
        filepath: Path to KiCad SPICE netlist file (.cir)
        
    Returns:
        NetlistSchema with components and pins
        
    Raises:
        FileNotFoundError: If file doesn't exist
        ValidationError: If parsed data doesn't match schema
    """
    if not filepath.exists():
        raise FileNotFoundError(f"KiCad SPICE netlist file not found: {filepath}")

    # Read file content
    with open(filepath, 'r', encoding='utf-8', errors='replace') as f:
        content = f.read()

    # Parse
    parser = KiCadSpiceParser(content)
    schema = parser.parse()

    return schema
