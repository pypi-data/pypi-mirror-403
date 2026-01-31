"""
KiCad Legacy Netlist Parser

Parses KiCad legacy netlist files (.net) in S-expression format.
Extracts:
- Reference designators (ref_des)
- Part numbers (from value or PARTNUMBER property)
- Pin connections from nets section

Format:
    (export (version "E")
      (components
        (comp (ref "C1")
          (value "PART_NUMBER")
          (property (name "PARTNUMBER") (value "..."))))
      (nets
        (net (code "1") (name "GND")
          (node (ref "C1") (pin "1")))))
"""

from collections import defaultdict
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from mfcli.models.netlist import Component, NetlistSchema, Pin


# ============================================================================
# S-Expression Parser
# ============================================================================

class SExpression:
    """Represents a parsed S-expression."""

    def __init__(self, value: Optional[str] = None, children: Optional[List['SExpression']] = None):
        self.value = value  # String value for atoms, None for lists
        self.children = children or []  # Child expressions for lists

    def is_list(self) -> bool:
        """Check if this is a list (not an atom)."""
        return self.value is None

    def find(self, key: str) -> Optional['SExpression']:
        """Find first child with matching value."""
        for child in self.children:
            if child.is_list() and child.children and child.children[0].value == key:
                return child
        return None

    def find_all(self, key: str) -> List['SExpression']:
        """Find all children with matching value."""
        results = []
        for child in self.children:
            if child.is_list() and child.children and child.children[0].value == key:
                results.append(child)
        return results

    def get_value(self, index: int = 0) -> Optional[str]:
        """Get value at index from children."""
        if index < len(self.children):
            return self.children[index].value
        return None

    @staticmethod
    def parse(text: str) -> List['SExpression']:
        """Parse S-expression text into tree structure."""
        tokens = SExpression._tokenize(text)
        expressions, _ = SExpression._parse_tokens(tokens, 0)
        return expressions

    @staticmethod
    def _tokenize(text: str) -> List[str]:
        """Tokenize S-expression text."""
        tokens = []
        i = 0
        while i < len(text):
            char = text[i]

            # Skip whitespace
            if char.isspace():
                i += 1
                continue

            # Handle parentheses
            if char in '()':
                tokens.append(char)
                i += 1
                continue

            # Handle quoted strings
            if char == '"':
                j = i + 1
                while j < len(text) and text[j] != '"':
                    if text[j] == '\\':
                        j += 2  # Skip escaped character
                    else:
                        j += 1
                tokens.append(text[i:j + 1])  # Include quotes
                i = j + 1
                continue

            # Handle atoms (unquoted strings)
            j = i
            while j < len(text) and not text[j].isspace() and text[j] not in '()':
                j += 1
            tokens.append(text[i:j])
            i = j

        return tokens

    @staticmethod
    def _parse_tokens(tokens: List[str], pos: int) -> Tuple[List['SExpression'], int]:
        """Parse tokens into S-expressions, returns (expressions, next_pos)."""
        expressions = []

        while pos < len(tokens):
            token = tokens[pos]

            if token == '(':
                # Start of list
                children, pos = SExpression._parse_tokens(tokens, pos + 1)
                expressions.append(SExpression(children=children))

            elif token == ')':
                # End of list
                return expressions, pos + 1

            else:
                # Atom - remove quotes if present
                value = token.strip('"')
                expressions.append(SExpression(value=value))
                pos += 1

        return expressions, pos


# ============================================================================
# KiCad Legacy Netlist Parser
# ============================================================================

class KiCadLegacyNetParser:
    """Parser for KiCad legacy netlist files."""

    def __init__(self, content: str):
        self.content = content
        self.root: Optional[SExpression] = None
        self.components_map: Dict[str, str] = {}  # ref_des -> part_number
        self.nets_map: Dict[str, List[Tuple[str, str]]] = defaultdict(list)  # net_name -> [(ref_des, pin), ...]

    def parse(self) -> NetlistSchema:
        """Parse content and return validated schema."""
        # Parse S-expressions
        self.root = SExpression.parse(self.content)

        if not self.root:
            raise ValueError("Failed to parse S-expression")

        # Find export section
        export = None
        for expr in self.root:
            if expr.is_list() and expr.get_value(0) == "export":
                export = expr
                break

        if not export:
            raise ValueError("No (export ...) section found")

        # Extract components and nets
        self._extract_components(export)
        self._extract_nets(export)

        # Build schema
        return self._build_schema()

    def _extract_components(self, export: SExpression):
        """Extract components from (components ...) section."""
        components_section = export.find("components")
        if not components_section:
            return

        # Find all (comp ...) entries
        for comp in components_section.find_all("comp"):
            ref_des = self._get_component_ref(comp)
            part_number = self._get_component_part_number(comp)

            if ref_des and part_number:
                self.components_map[ref_des] = part_number

    def _get_component_ref(self, comp: SExpression) -> Optional[str]:
        """Extract reference designator from (comp ...) section."""
        ref_expr = comp.find("ref")
        if ref_expr and len(ref_expr.children) > 1:
            return ref_expr.children[1].value
        return None

    def _get_component_part_number(self, comp: SExpression) -> Optional[str]:
        """
        Extract part number from (comp ...) section.
        Try (value ...) first, then (property (name "PARTNUMBER") ...).
        """
        # Try (value ...) - most common
        value_expr = comp.find("value")
        if value_expr and len(value_expr.children) > 1:
            part_number = value_expr.children[1].value
            if part_number:
                return part_number

        # Try (property (name "PARTNUMBER") (value "..."))
        for prop in comp.find_all("property"):
            name_expr = prop.find("name")
            if name_expr and len(name_expr.children) > 1:
                if name_expr.children[1].value == "PARTNUMBER":
                    value_expr = prop.find("value")
                    if value_expr and len(value_expr.children) > 1:
                        return value_expr.children[1].value

        return None

    def _extract_nets(self, export: SExpression):
        """Extract nets from (nets ...) section."""
        nets_section = export.find("nets")
        if not nets_section:
            return

        # Find all (net ...) entries
        for net in nets_section.find_all("net"):
            net_name = self._get_net_name(net)
            if not net_name:
                continue

            # Find all (node ...) entries
            for node in net.find_all("node"):
                ref_des, pin = self._get_node_info(node)
                if ref_des and pin:
                    self.nets_map[net_name].append((ref_des, pin))

    def _get_net_name(self, net: SExpression) -> Optional[str]:
        """Extract net name from (net ...) section."""
        name_expr = net.find("name")
        if name_expr and len(name_expr.children) > 1:
            return name_expr.children[1].value
        return None

    def _get_node_info(self, node: SExpression) -> Tuple[Optional[str], Optional[str]]:
        """Extract ref_des and pin from (node ...) section."""
        ref_des = None
        pin = None

        ref_expr = node.find("ref")
        if ref_expr and len(ref_expr.children) > 1:
            ref_des = ref_expr.children[1].value

        pin_expr = node.find("pin")
        if pin_expr and len(pin_expr.children) > 1:
            pin = pin_expr.children[1].value

        return ref_des, pin

    def _build_schema(self) -> NetlistSchema:
        """Build NetlistSchema from extracted data."""
        # Build pin list per component
        component_pins: Dict[str, List[Pin]] = defaultdict(list)

        for net_name, nodes in self.nets_map.items():
            for ref_des, pin_number in nodes:
                # Only add pins for known components
                if ref_des in self.components_map:
                    pin = Pin(
                        pin=pin_number,
                        net=net_name
                    )
                    component_pins[ref_des].append(pin)

        # Build components list
        components = []
        for ref_des, part_number in self.components_map.items():
            component = Component(
                ref_des=ref_des,
                part_number=part_number,
                pins=component_pins[ref_des]
            )
            components.append(component)

        return NetlistSchema(components=components)


# ============================================================================
# Main Function
# ============================================================================

def is_kicad_legacy_netlist(text: str) -> bool:
    stripped = text.lstrip()
    if not stripped.startswith("(export"):
        return False

    # MUST contain these blocks
    keywords = ["(design", "(components", "(nets"]
    return all(k in text for k in keywords)


def parse_kicad_legacy_net_file(filepath: Path) -> NetlistSchema:
    """
    Parse a KiCad legacy netlist file and return validated netlist schema.
    
    Args:
        filepath: Path to KiCad legacy netlist file (.net)
        
    Returns:
        NetlistSchema with components and pins
        
    Raises:
        FileNotFoundError: If file doesn't exist
        ValidationError: If parsed data doesn't match schema
    """
    if not filepath.exists():
        raise FileNotFoundError(f"KiCad legacy netlist file not found: {filepath}")

    # Read file content
    with open(filepath, 'r', encoding='utf-8', errors='replace') as f:
        content = f.read()

    # Parse
    parser = KiCadLegacyNetParser(content)
    schema = parser.parse()

    return schema
