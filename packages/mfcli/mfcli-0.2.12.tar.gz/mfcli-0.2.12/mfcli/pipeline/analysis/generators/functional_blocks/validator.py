from typing import List, Dict, Tuple
from difflib import SequenceMatcher

from mfcli.models.functional_blocks import FunctionalBlockMeta
from mfcli.models.netlist import NetlistComponent, Netlist
from mfcli.utils.logger import get_logger
from mfcli.utils.orm import Session

logger = get_logger(__name__)


def validate_functional_blocks_against_netlist(
        db: Session,
        pipeline_run_id: int,
        functional_blocks: List[FunctionalBlockMeta]
) -> Dict:
    """
    Validate functional block components against netlist.
    Returns corrected blocks and validation report.
    """

    # Get all valid component ref_des from netlist
    valid_components = (
        db.query(NetlistComponent.ref_des)
        .join(NetlistComponent.netlist)
        .filter(Netlist.pipeline_run_id == pipeline_run_id)
        .all()
    )
    valid_refs = {comp.ref_des for comp in valid_components}

    report = {
        "total_components": 0,
        "valid_components": 0,
        "invalid_components": [],
        "corrected_components": [],
        "blocks_validated": 0
    }

    for block in functional_blocks:
        corrected_components = []

        for component_ref in block.components:
            report["total_components"] += 1

            if component_ref in valid_refs:
                # Valid component
                report["valid_components"] += 1
                corrected_components.append(component_ref)
            else:
                # Invalid - try fuzzy matching
                best_match = find_best_match(component_ref, valid_refs)

                if best_match and similarity_ratio(component_ref, best_match) > 0.8:
                    # High confidence match - autocorrect
                    logger.warning(f"Auto-correcting '{component_ref}' -> '{best_match}'")
                    corrected_components.append(best_match)
                    report["corrected_components"].append({
                        "original": component_ref,
                        "corrected": best_match,
                        "block": block.name
                    })
                else:
                    # No good match - log and skip
                    logger.error(f"Invalid component '{component_ref}' in block '{block.name}'")
                    report["invalid_components"].append({
                        "ref": component_ref,
                        "block": block.name,
                        "suggestion": best_match if best_match else None
                    })

        block.components = corrected_components

        report["blocks_validated"] += 1

    return report


def find_best_match(ref: str, valid_refs: set) -> str:
    """Find nearest matching reference designator."""
    best_match = None
    best_ratio = 0

    for valid_ref in valid_refs:
        ratio = SequenceMatcher(None, ref.upper(), valid_ref.upper()).ratio()
        if ratio > best_ratio:
            best_ratio = ratio
            best_match = valid_ref

    return best_match if best_ratio > 0.6 else None


def similarity_ratio(str1: str, str2: str) -> float:
    """Calculate similarity between two strings."""
    return SequenceMatcher(None, str1.upper(), str2.upper()).ratio()
