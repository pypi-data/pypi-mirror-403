"""
Module for identifying microcontrollers from BOM entries and schematics.
"""
import re
from typing import List, Dict, Optional, Tuple
from sqlalchemy.orm import Session

from mfcli.models.bom import BOM
from mfcli.models.file import File
from mfcli.constants.file_types import FileSubtypes
from mfcli.utils.logger import get_logger

logger = get_logger(__name__)


# Common MCU manufacturer prefixes and patterns
# These patterns are designed to match at the START of part numbers to avoid false positives
MCU_PATTERNS = [
    # Texas Instruments - Must not start with common passive prefixes
    r'\bMSP(M0)?[A-Z]?\d+[A-Z]*\d*\w*',  # MSP430, MSPM0L1306, etc.
    r'\bTMS\d+\w*',
    r'\bCC(13|25|26|27|32)\d+\w*',  # CC13xx, CC25xx, CC26xx, CC27xx, CC32xx families
    
    # STMicroelectronics
    r'\bSTM32[A-Z]\d+\w*',
    r'\bSTM8[A-Z]\d+\w*',
    
    # Microchip/Atmel
    r'\bPIC(16|18|24|32)[A-Z]*\d+\w*',  # More specific PIC patterns
    r'\bATMEGA\d+\w*',
    r'\bATTINY\d+\w*',
    r'\bATSAMD?\d+\w*',
    r'\bdsPIC\d+\w*',
    
    # NXP/Freescale
    r'\bLPC\d+\w*',
    r'\bMK[A-Z]?\d+\w*',
    r'\bS32K\d+\w*',
    r'\bi\.?MX\d+\w*',
    r'\bKINETIS\w*',
    
    # Espressif
    r'\bESP32\w*',
    r'\bESP8266\w*',
    
    # Nordic Semiconductor
    r'\bNRF(5|9)\d+\w*',  # NRF5x, NRF9x series
    
    # Renesas
    r'\bRL78\w*',
    r'\bRX[12467]\d+\w*',  # RX100, RX200, RX400, RX600, RX700 series
    r'\bRA[246]\w*',  # RA2, RA4, RA6 series
    
    # Silicon Labs
    r'\bEFM32\w*',
    r'\bEFR32\w*',
    r'\bSi[18]0\d+\w*',  # Si1000, Si8000 series
    
    # Infineon
    r'\bXMC\d+\w*',
    r'\bPSoC[3456]\w*',
    
    # Raspberry Pi
    r'\bRP20\d+\w*',  # RP2040, etc.
    
    # ARM
    r'\bCortex-[A-Z]\d+',
    
    # RISC-V patterns
    r'\bGD32V\w*',
    r'\bFE310\w*',
]

# Common MCU reference designators
MCU_DESIGNATORS = [
    r'^U\d+$',      # U1, U2, etc.
    r'^IC\d+$',     # IC1, IC2, etc.
    r'^MCU\d+$',    # MCU1, MCU2, etc.
    r'^CPU\d+$',    # CPU1, CPU2, etc.
    r'^uC\d+$',     # uC1, uC2, etc.
    r'^MSP\d+$',    # MSP1, MSP2, etc. (common for TI boards)
]

# Part number prefixes that indicate NOT an MCU (passive components)
PASSIVE_PREFIXES = [
    r'^R[A-Z]*\d',   # Resistors: RC0402, RG1005, etc.
    r'^C[A-Z]*\d',   # Capacitors: CL10, C1005, C0603, etc.
    r'^L[A-Z]*\d',   # Inductors: LQH, CBC, etc.
    r'^GRM\d',       # Murata capacitors
    r'^ERA\d',       # Panasonic resistors
    r'^CRCW\d',      # Vishay resistors
    r'^MCT\d',       # Resistor networks
    r'^ERJ-\d',      # Panasonic resistors
]

# Keywords in descriptions that indicate MCU
MCU_KEYWORDS = [
    'microcontroller',
    'mcu',
    'processor',
    'cpu',
    'cortex',
    'arm',
    'risc-v',
    'controller',
]


class DetectedMCU:
    """Represents a detected microcontroller"""
    
    def __init__(
        self,
        part_number: str,
        reference: str,
        description: Optional[str] = None,
        manufacturer: Optional[str] = None,
        confidence_score: float = 0.0,
        source: str = "BOM"
    ):
        self.part_number = part_number.strip()
        self.reference = reference.strip()
        self.description = description or ""
        self.manufacturer = manufacturer or ""
        self.confidence_score = confidence_score
        self.source = source
    
    def __repr__(self):
        return f"DetectedMCU(part={self.part_number}, ref={self.reference}, score={self.confidence_score:.2f})"
    
    def to_dict(self) -> Dict:
        return {
            "part_number": self.part_number,
            "reference": self.reference,
            "description": self.description,
            "manufacturer": self.manufacturer,
            "confidence_score": self.confidence_score,
            "source": self.source
        }


def _is_passive_component(part_number: str) -> bool:
    """Check if part number is a passive component (resistor, capacitor, inductor)"""
    part_upper = part_number.upper().strip()
    
    for pattern in PASSIVE_PREFIXES:
        if re.match(pattern, part_upper):
            return True
    
    return False


def _match_mcu_pattern(part_number: str) -> bool:
    """Check if part number matches known MCU patterns"""
    part_upper = part_number.upper().strip()
    
    # First check if it's a passive component - if so, reject immediately
    if _is_passive_component(part_upper):
        return False
    
    for pattern in MCU_PATTERNS:
        if re.search(pattern, part_upper):
            return True
    
    return False


def _match_mcu_designator(reference: str) -> bool:
    """Check if reference designator indicates an MCU"""
    ref_upper = reference.upper().strip()
    
    for pattern in MCU_DESIGNATORS:
        if re.match(pattern, ref_upper):
            return True
    
    return False


def _has_mcu_keywords(text: str) -> bool:
    """Check if text contains MCU-related keywords"""
    if not text:
        return False
    
    text_lower = text.lower()
    return any(keyword in text_lower for keyword in MCU_KEYWORDS)


def _calculate_confidence_score(
    bom_entry: BOM,
    part_matches: bool,
    ref_matches: bool,
    desc_matches: bool
) -> float:
    """
    Calculate confidence score for MCU detection.
    Score is between 0.0 and 1.0.
    """
    score = 0.0
    
    # Part number match is strongest indicator
    if part_matches:
        score += 0.6
    
    # Reference designator match
    if ref_matches:
        score += 0.2
    
    # Description keyword match
    if desc_matches:
        score += 0.2
    
    # Boost score for reference U1 (typically primary MCU)
    if bom_entry.reference.upper() == 'U1':
        score += 0.1
    
    # Boost score if manufacturer is known MCU vendor
    if bom_entry.manufacturer:
        mfr_lower = bom_entry.manufacturer.lower()
        known_vendors = [
            'texas instruments', 'ti', 'stmicroelectronics', 'st',
            'microchip', 'atmel', 'nxp', 'freescale', 'espressif',
            'nordic', 'renesas', 'silicon labs', 'infineon', 'raspberry'
        ]
        if any(vendor in mfr_lower for vendor in known_vendors):
            score += 0.1
    
    return min(score, 1.0)


def _extract_reference_number(reference: str) -> int:
    """Extract numeric part from reference designator (e.g., U1 -> 1)"""
    match = re.search(r'\d+', reference)
    if match:
        return int(match.group())
    return 999  # Default high number for unparseable references


def _is_passive_reference(reference: str) -> bool:
    """Check if reference designator indicates a passive component"""
    ref_upper = reference.upper().strip()
    
    # Common passive component designators
    passive_refs = [
        r'^R\d+$',      # Resistors: R1, R2, etc.
        r'^C\d+$',      # Capacitors: C1, C2, etc.
        r'^L\d+$',      # Inductors: L1, L2, etc.
        r'^RV\d+$',     # Variable resistors
        r'^RT\d+$',     # Thermistors
        r'^FB\d+$',     # Ferrite beads
    ]
    
    for pattern in passive_refs:
        if re.match(pattern, ref_upper):
            return True
    
    return False


def identify_mcus_from_bom(db: Session, pipeline_run_id: int) -> List[DetectedMCU]:
    """
    Identify microcontrollers from BOM entries.
    
    Args:
        db: Database session
        pipeline_run_id: Pipeline run ID to query BOM entries
    
    Returns:
        List of detected MCUs, sorted by confidence score (highest first)
    """
    logger.info(f"Identifying MCUs from BOM for pipeline run: {pipeline_run_id}")
    
    # Query all BOM entries for this pipeline run
    bom_entries = (
        db.query(BOM)
        .join(File, BOM.file_id == File.id)
        .filter(File.pipeline_run_id == pipeline_run_id)
        .all()
    )
    
    if not bom_entries:
        logger.warning("No BOM entries found for MCU identification")
        return []
    
    detected_mcus = []
    
    for entry in bom_entries:
        # Skip entries without part numbers
        if not entry.value:
            continue
        
        # Skip passive components by reference designator
        if _is_passive_reference(entry.reference):
            continue
        
        # Check various criteria
        part_matches = _match_mcu_pattern(entry.value)
        ref_matches = _match_mcu_designator(entry.reference)
        desc_matches = _has_mcu_keywords(entry.description or "")
        
        # Need at least one match to consider it
        if not (part_matches or (ref_matches and desc_matches)):
            continue
        
        # Calculate confidence score
        confidence = _calculate_confidence_score(
            entry, part_matches, ref_matches, desc_matches
        )
        
        # Only include if confidence is above threshold
        if confidence >= 0.4:
            mcu = DetectedMCU(
                part_number=entry.value,
                reference=entry.reference,
                description=entry.description,
                manufacturer=entry.manufacturer,
                confidence_score=confidence,
                source="BOM"
            )
            detected_mcus.append(mcu)
            logger.debug(f"Detected MCU: {mcu}")
    
    # Sort by confidence score (descending), then by reference number (ascending)
    detected_mcus.sort(
        key=lambda m: (-m.confidence_score, _extract_reference_number(m.reference))
    )
    
    logger.info(f"Found {len(detected_mcus)} potential MCUs")
    return detected_mcus


def _clean_part_number(part_number: str) -> str:
    """
    Clean up part number by removing common suffixes and normalizing.
    
    Args:
        part_number: Raw part number
    
    Returns:
        Cleaned part number
    """
    # Remove common suffixes from datasheets
    suffixes_to_remove = [
        '_DATASHEET', '_DS', '_MANUAL', '_DOC', '_PDF',
        'DATASHEET', 'DS', 'MANUAL', 'DOC', 'PDF'
    ]
    
    cleaned = part_number.upper().strip()
    
    for suffix in suffixes_to_remove:
        if cleaned.endswith(suffix):
            cleaned = cleaned[:-len(suffix)]
            cleaned = cleaned.rstrip('_-')
    
    return cleaned


def _normalize_part_number(part_number: str) -> str:
    """
    Normalize part number for comparison (e.g., ATMEGA328 vs ATMEGA328P).
    Removes trailing variant letters/numbers that might differ.
    
    Args:
        part_number: Part number to normalize
    
    Returns:
        Normalized part number for matching
    """
    # Remove common variant suffixes for matching purposes
    # This helps match ATMEGA328 with ATMEGA328P, STM32F407VG with STM32F407VGT6
    normalized = part_number.upper().strip()
    
    # For matching purposes, we use the base part number
    # but still keep enough to distinguish different MCU families
    return normalized


def identify_mcus_from_datasheets(db: Session, pipeline_run_id: int) -> List[DetectedMCU]:
    """
    Identify microcontrollers from MCU datasheet files.
    
    Args:
        db: Database session
        pipeline_run_id: Pipeline run ID to query files
    
    Returns:
        List of detected MCUs from datasheet filenames
    """
    logger.info(f"Identifying MCUs from datasheets for pipeline run: {pipeline_run_id}")
    
    # Query MCU datasheet files
    mcu_datasheets = (
        db.query(File)
        .filter(File.pipeline_run_id == pipeline_run_id)
        .filter(File.sub_type == FileSubtypes.MCU_DATASHEET)
        .all()
    )
    
    if not mcu_datasheets:
        logger.info("No MCU datasheet files found")
        return []
    
    detected_mcus = []
    
    for file in mcu_datasheets:
        # Try to extract MCU part number from filename
        filename = file.name.upper()
        
        for pattern in MCU_PATTERNS:
            match = re.search(pattern, filename)
            if match:
                raw_part_number = match.group()
                # Clean up the part number
                part_number = _clean_part_number(raw_part_number)
                
                # Skip if cleaning removed everything
                if len(part_number) < 3:
                    continue
                
                mcu = DetectedMCU(
                    part_number=part_number,
                    reference="N/A",
                    description=f"From datasheet: {file.name}",
                    confidence_score=0.7,  # High confidence from datasheet
                    source="Datasheet"
                )
                detected_mcus.append(mcu)
                logger.debug(f"Detected MCU from datasheet: {mcu}")
                break  # Only match first pattern per file
    
    logger.info(f"Found {len(detected_mcus)} MCUs from datasheets")
    return detected_mcus


def _parts_are_similar(part1: str, part2: str) -> bool:
    """
    Check if two part numbers are likely the same MCU with minor variations.
    E.g., ATMEGA328 and ATMEGA328P, STM32F407VG and STM32F407VGT6
    
    Args:
        part1: First part number
        part2: Second part number
    
    Returns:
        True if they're likely the same MCU
    """
    p1 = part1.upper().strip()
    p2 = part2.upper().strip()
    
    # Exact match
    if p1 == p2:
        return True
    
    # One is prefix of the other (e.g., ATMEGA328 vs ATMEGA328P)
    if p1.startswith(p2) or p2.startswith(p1):
        # Make sure the difference is small (just variant suffix)
        diff = abs(len(p1) - len(p2))
        if diff <= 3:  # Allow up to 3 character difference
            return True
    
    # Check if they share the same core part number
    # Extract the numeric + letter core (e.g., STM32F407 from STM32F407VGT6)
    # This is a simple heuristic
    core1 = re.match(r'([A-Z]+\d+[A-Z]?\d*)', p1)
    core2 = re.match(r'([A-Z]+\d+[A-Z]?\d*)', p2)
    
    if core1 and core2:
        if core1.group(1) == core2.group(1):
            return True
    
    return False


def merge_mcu_detections(
    bom_mcus: List[DetectedMCU],
    datasheet_mcus: List[DetectedMCU]
) -> List[DetectedMCU]:
    """
    Merge MCU detections from multiple sources, removing duplicates.
    Uses similarity matching to identify the same MCU with minor part number variations.
    
    Args:
        bom_mcus: MCUs detected from BOM
        datasheet_mcus: MCUs detected from datasheets
    
    Returns:
        Merged list of unique MCUs, sorted by confidence
    """
    # Use part number as key for deduplication
    mcu_map: Dict[str, DetectedMCU] = {}
    
    # Add BOM MCUs first (they have reference designators and are more authoritative)
    for mcu in bom_mcus:
        key = mcu.part_number.upper()
        if key not in mcu_map or mcu.confidence_score > mcu_map[key].confidence_score:
            mcu_map[key] = mcu
    
    # Add datasheet MCUs, checking for similar part numbers
    for ds_mcu in datasheet_mcus:
        ds_key = ds_mcu.part_number.upper()
        
        # Check if this datasheet MCU matches any BOM MCU
        found_match = False
        for bom_key, bom_mcu in mcu_map.items():
            if _parts_are_similar(ds_key, bom_key):
                # Found a match! Boost the BOM MCU's confidence
                bom_mcu.confidence_score = min(bom_mcu.confidence_score + 0.2, 1.0)
                logger.info(f"MCU {bom_key} confirmed by datasheet {ds_key}, boosting confidence to {bom_mcu.confidence_score:.0%}")
                found_match = True
                break
        
        # If no match found, add as separate MCU
        if not found_match:
            # But first check if it's already in the map with exact key
            if ds_key in mcu_map:
                # Boost existing entry
                mcu_map[ds_key].confidence_score = min(mcu_map[ds_key].confidence_score + 0.2, 1.0)
                logger.debug(f"MCU {ds_key} confirmed by datasheet, boosting confidence")
            else:
                # Add as new MCU
                mcu_map[ds_key] = ds_mcu
                logger.debug(f"Added datasheet MCU {ds_key} as separate entry")
    
    # Convert back to list and sort by confidence
    merged = list(mcu_map.values())
    merged.sort(
        key=lambda m: (-m.confidence_score, _extract_reference_number(m.reference))
    )
    
    logger.info(f"Merged to {len(merged)} unique MCUs after deduplication")
    return merged


def suggest_primary_mcu(detected_mcus: List[DetectedMCU]) -> Tuple[Optional[DetectedMCU], str]:
    """
    Suggest which MCU should be the primary one.
    
    Args:
        detected_mcus: List of detected MCUs
    
    Returns:
        Tuple of (suggested_mcu, reasoning)
    """
    if not detected_mcus:
        return None, "No MCUs detected"
    
    # Primary is highest confidence score
    primary = detected_mcus[0]
    
    # Build reasoning
    reasons = []
    
    if primary.confidence_score >= 0.9:
        reasons.append("Very high confidence match")
    elif primary.confidence_score >= 0.7:
        reasons.append("High confidence match")
    
    if primary.reference.upper() == 'U1':
        reasons.append("Located at reference U1 (typically primary)")
    
    if primary.source == "BOM":
        reasons.append("Found in BOM")
    
    reasoning = "; ".join(reasons) if reasons else "Highest confidence score"
    
    return primary, reasoning
