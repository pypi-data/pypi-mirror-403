"""
Protel/Altium Designer Netlist Detector

Helper function to detect if a file is a Protel/Altium Designer netlist.
"""


def is_protel_netlist(content: str) -> bool:
    """
    Detect if content is from a Protel/Altium Designer netlist file.
    
    Args:
        content: File content to check
        
    Returns:
        True if content appears to be a Protel/Altium netlist
    """
    lines = content.strip().split('\n')
    
    if not lines:
        return False
    
    # Check for Protel/Altium header in first few lines
    for line in lines[:5]:
        line = line.strip()
        if '{COMPONENT PROTEL.PCB' in line:
            return True
    
    return False
