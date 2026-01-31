"""
KiCad Schematic File Detector

This module detects KiCad schematic files (.kicad_sch) based on their content.
KiCad schematics use S-expression format and start with (kicad_sch ...).
"""


def is_kicad_schematic(text: str) -> bool:
    """
    Detect if a file is a KiCad schematic based on its content.
    
    KiCad schematics (.kicad_sch) are S-expression files that start with:
    (kicad_sch (version X) (generator ...) ...)
    
    Args:
        text: The content of the file (first few lines are sufficient)
        
    Returns:
        True if the file is a KiCad schematic, False otherwise
    """
    if not text:
        return False
    
    # Remove leading whitespace
    stripped = text.lstrip()
    
    # Check if it starts with the KiCad schematic header
    # KiCad schematics start with (kicad_sch
    if stripped.startswith("(kicad_sch"):
        return True
    
    return False
