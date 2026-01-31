import re
from collections import defaultdict
from typing import Dict, Any


def parse(file_path: str) -> Dict[str, Any]:
    """
    Parse an EDIF file and extract a relational JSON representation:
    component-pin-net mapping, deduplicated net names, annotated with voltage domains and pull-up/pull-down info.
    """
    with open(file_path, "r") as f:
        edif_text = f.read()

    # --- Step 1: Extract NETLIST_TEXT ---
    match = re.search(r'\(property NETLIST_TEXT \(string "(.*?)"\)\)', edif_text, re.DOTALL)
    if not match:
        raise ValueError("No NETLIST_TEXT property found in EDIF")

    netlist_text = match.group(1)
    netlist_text = netlist_text.replace('\\n', '\n').strip()

    # --- Step 2: Parse SPICE-style lines ---
    component_pattern = re.compile(
        r'^(?P<name>\w+)\s+(?P<n1>\S+)\s+(?P<n2>\S+)\s+(?P<rest>.*)$', re.MULTILINE
    )

    components = []
    nets = defaultdict(lambda: {"name": None, "connected_pins": []})

    for match in component_pattern.finditer(netlist_text):
        name = match.group("name")
        n1, n2 = match.group("n1"), match.group("n2")
        rest = match.group("rest")

        # Deduce type from prefix (SPICE convention)
        type_prefix = name[0].lower()
        type_map = {
            "r": "resistor",
            "c": "capacitor",
            "l": "inductor",
            "v": "voltage_source",
            "i": "current_source",
            "e": "op_amp",
            "d": "diode",
            "j": "jumper",
            "led": "led",
            "s": "switch",
            "y": "crystal",
            "sh": "shunt",
            "rt": "thermistor",
            "tp": "transistor",
        }
        comp_type = type_map.get(type_prefix, "unknown")

        pins = [n1, n2]
        components.append({
            "name": name,
            "type": comp_type,
            "pins": pins,
            "params": rest,
        })

        # Connect pins to nets
        for pin in pins:
            nets[pin]["name"] = pin
            nets[pin]["connected_pins"].append({"component": name, "pin": pin})

    # --- Step 3: Deduplicate net names ---
    unique_nets = list(nets.values())

    # --- Step 4: Annotate nets ---
    for net in unique_nets:
        name = net["name"].lower()
        if name in ("vcc", "vdd", "vin"):
            net["voltage_domain"] = "high"
        elif name in ("gnd", "vss", "0"):
            net["voltage_domain"] = "ground"
        else:
            net["voltage_domain"] = "signal"

        # Simple pull heuristic
        if "pullup" in name:
            net["pull"] = "pull-up"
        elif "pulldown" in name:
            net["pull"] = "pull-down"
        else:
            net["pull"] = None

    # --- Step 5: Return structured output ---
    return {
        "components": components,
        "nets": unique_nets
    }
