"""
Module for interactive MCU configuration with user prompts.
"""
import json
from typing import List, Optional
from pathlib import Path

from mfcli.models.project_metadata import MCUConfiguration
from mfcli.pipeline.analysis.mcu_identifier import DetectedMCU
from mfcli.utils.logger import get_logger
from mfcli.utils.directory_manager import app_dirs

logger = get_logger(__name__)


def display_detected_mcus(detected_mcus: List[DetectedMCU], suggested_primary: Optional[DetectedMCU], reasoning: str):
    """
    Display detected MCUs in a user-friendly format.
    
    Args:
        detected_mcus: List of detected MCUs
        suggested_primary: Suggested primary MCU
        reasoning: Reasoning for the suggestion
    """
    print(f"\n{'='*70}")
    print(f"MICROCONTROLLER IDENTIFICATION")
    print(f"{'='*70}\n")
    
    if not detected_mcus:
        print("No microcontrollers were detected in the BOM or schematics.")
        return
    
    print(f"Found {len(detected_mcus)} microcontroller(s) in your design:\n")
    
    for idx, mcu in enumerate(detected_mcus, 1):
        is_primary = suggested_primary and mcu.part_number == suggested_primary.part_number
        marker = " ⭐ PRIMARY (suggested)" if is_primary else ""
        
        print(f"{idx}. {mcu.part_number}{marker}")
        print(f"   Reference: {mcu.reference}")
        if mcu.manufacturer:
            print(f"   Manufacturer: {mcu.manufacturer}")
        if mcu.description:
            print(f"   Description: {mcu.description}")
        print(f"   Confidence: {mcu.confidence_score:.0%}")
        print(f"   Source: {mcu.source}")
        print()
    
    if suggested_primary:
        print(f"Suggested Primary MCU: {suggested_primary.part_number}")
        print(f"Reasoning: {reasoning}\n")
    
    print(f"{'='*70}\n")


def prompt_mcu_configuration(detected_mcus: List[DetectedMCU]) -> Optional[MCUConfiguration]:
    """
    Interactively prompt user to configure MCUs.
    
    Args:
        detected_mcus: List of detected MCUs
    
    Returns:
        MCUConfiguration object or None if skipped
    """
    from mfcli.pipeline.analysis.mcu_identifier import suggest_primary_mcu
    
    if not detected_mcus:
        print("\nNo microcontrollers detected. You can configure this later using 'mfcli configure-mcu'")
        return None
    
    # Get suggestion
    suggested_primary, reasoning = suggest_primary_mcu(detected_mcus)
    
    # Display detected MCUs
    display_detected_mcus(detected_mcus, suggested_primary, reasoning)
    
    # Prompt user for action
    print("What would you like to do?")
    print("  1. Accept suggested configuration")
    print("  2. Select a different primary MCU")
    print("  3. Add additional MCUs manually")
    print("  4. Skip configuration (can configure later)")
    
    while True:
        choice = input("\nEnter your choice (1-4): ").strip()
        
        if choice == '1':
            # Accept suggested configuration
            return _accept_suggested_configuration(detected_mcus, suggested_primary)
        
        elif choice == '2':
            # Select different primary
            return _select_different_primary(detected_mcus)
        
        elif choice == '3':
            # Add additional MCUs
            return _add_additional_mcus(detected_mcus, suggested_primary)
        
        elif choice == '4':
            # Skip configuration
            print("\n✓ Skipping MCU configuration. You can configure later using 'mfcli configure-mcu'")
            logger.info("User skipped MCU configuration")
            return None
        
        else:
            print("Invalid choice. Please enter 1, 2, 3, or 4.")


def _accept_suggested_configuration(
    detected_mcus: List[DetectedMCU],
    suggested_primary: DetectedMCU
) -> MCUConfiguration:
    """Accept the suggested configuration."""
    additional = [mcu.part_number for mcu in detected_mcus if mcu.part_number != suggested_primary.part_number]
    
    config = MCUConfiguration(
        primary_mcu=suggested_primary.part_number,
        additional_mcus=additional
    )
    
    print(f"\n✓ Configuration accepted:")
    print(f"  Primary MCU: {config.primary_mcu}")
    if config.additional_mcus:
        print(f"  Additional MCUs: {', '.join(config.additional_mcus)}")
    
    logger.info(f"MCU configuration accepted: primary={config.primary_mcu}, additional={config.additional_mcus}")
    return config


def _select_different_primary(detected_mcus: List[DetectedMCU]) -> Optional[MCUConfiguration]:
    """Allow user to select a different primary MCU."""
    print("\nSelect the primary MCU:")
    
    for idx, mcu in enumerate(detected_mcus, 1):
        print(f"  {idx}. {mcu.part_number} ({mcu.reference})")
    
    while True:
        try:
            choice = input(f"\nEnter number (1-{len(detected_mcus)}) or 'c' to cancel: ").strip()
            
            if choice.lower() == 'c':
                print("Cancelled. Returning to main menu...")
                return prompt_mcu_configuration(detected_mcus)
            
            idx = int(choice) - 1
            if 0 <= idx < len(detected_mcus):
                primary = detected_mcus[idx]
                additional = [mcu.part_number for mcu in detected_mcus if mcu.part_number != primary.part_number]
                
                config = MCUConfiguration(
                    primary_mcu=primary.part_number,
                    additional_mcus=additional
                )
                
                print(f"\n✓ Configuration set:")
                print(f"  Primary MCU: {config.primary_mcu}")
                if config.additional_mcus:
                    print(f"  Additional MCUs: {', '.join(config.additional_mcus)}")
                
                logger.info(f"User selected primary MCU: {config.primary_mcu}")
                return config
            else:
                print(f"Invalid number. Please enter 1-{len(detected_mcus)}")
        
        except ValueError:
            print("Invalid input. Please enter a number or 'c' to cancel.")


def _add_additional_mcus(
    detected_mcus: List[DetectedMCU],
    suggested_primary: DetectedMCU
) -> Optional[MCUConfiguration]:
    """Allow user to add additional MCUs manually."""
    # Start with suggested configuration
    primary = suggested_primary.part_number
    additional = [mcu.part_number for mcu in detected_mcus if mcu.part_number != suggested_primary.part_number]
    
    print(f"\nCurrent configuration:")
    print(f"  Primary MCU: {primary}")
    if additional:
        print(f"  Additional MCUs: {', '.join(additional)}")
    else:
        print(f"  Additional MCUs: None")
    
    print("\nEnter additional MCU part numbers (one per line).")
    print("Enter a blank line when done.")
    print("Examples: STM32F407VG, ESP32-S3, ATMEGA328P")
    
    while True:
        part_number = input("MCU part number (or blank to finish): ").strip()
        
        if not part_number:
            # Done adding
            break
        
        # Validate part number (basic validation)
        if len(part_number) < 3:
            print("⚠️  Part number too short. Please enter a valid MCU part number.")
            continue
        
        # Check if already in list
        if part_number.upper() in [p.upper() for p in additional] or part_number.upper() == primary.upper():
            print(f"⚠️  {part_number} is already in the configuration.")
            continue
        
        additional.append(part_number)
        print(f"✓ Added {part_number}")
    
    config = MCUConfiguration(
        primary_mcu=primary,
        additional_mcus=additional
    )
    
    print(f"\n✓ Final configuration:")
    print(f"  Primary MCU: {config.primary_mcu}")
    if config.additional_mcus:
        print(f"  Additional MCUs: {', '.join(config.additional_mcus)}")
    
    logger.info(f"User configured MCUs: primary={config.primary_mcu}, additional={config.additional_mcus}")
    return config


def save_mcu_configuration(mcu_config: MCUConfiguration) -> bool:
    """
    Save MCU configuration to config.json.
    
    Args:
        mcu_config: MCU configuration to save
    
    Returns:
        True if successful, False otherwise
    """
    try:
        config_path = app_dirs.config_file_path
        
        if not config_path.exists():
            logger.error("config.json not found, cannot save MCU configuration")
            print("⚠️  Error: config.json not found")
            return False
        
        # Read existing config
        with open(config_path, 'r') as f:
            config_data = json.load(f)
        
        # Update MCU config
        config_data['mcu_config'] = mcu_config.model_dump()
        
        # Write back
        with open(config_path, 'w') as f:
            json.dump(config_data, f, indent=2)
        
        logger.info(f"Saved MCU configuration to {config_path}")
        print(f"\n✓ MCU configuration saved to config.json")
        return True
    
    except Exception as e:
        logger.exception(e)
        logger.error(f"Failed to save MCU configuration: {e}")
        print(f"\n⚠️  Error saving MCU configuration: {e}")
        return False


def load_mcu_configuration() -> Optional[MCUConfiguration]:
    """
    Load MCU configuration from config.json.
    
    Returns:
        MCUConfiguration object or None if not configured
    """
    try:
        config_path = app_dirs.config_file_path
        
        if not config_path.exists():
            return None
        
        with open(config_path, 'r') as f:
            config_data = json.load(f)
        
        if 'mcu_config' in config_data and config_data['mcu_config']:
            return MCUConfiguration(**config_data['mcu_config'])
        
        return None
    
    except Exception as e:
        logger.exception(e)
        logger.error(f"Failed to load MCU configuration: {e}")
        return None


def reconfigure_mcus_cli():
    """
    CLI command to reconfigure MCUs interactively.
    This allows users to change MCU configuration after initial setup.
    """
    from mfcli.crud.project import read_project_config_file
    from mfcli.pipeline.analysis.mcu_identifier import (
        identify_mcus_from_bom,
        identify_mcus_from_datasheets,
        merge_mcu_detections
    )
    from mfcli.utils.orm import Session
    from mfcli.crud.pipeline_run import get_latest_pipeline_run
    from mfcli.crud.project import get_project_by_name
    
    try:
        # Load project config
        project_config = read_project_config_file()
        
        with Session() as db:
            # Get project and latest pipeline run
            project = get_project_by_name(db, project_config.name)
            pipeline_run = get_latest_pipeline_run(db, project.id)
            
            if not pipeline_run:
                print("\n⚠️  No pipeline runs found. Please run 'mfcli run' first to analyze your design.")
                return
            
            # Identify MCUs from latest run
            bom_mcus = identify_mcus_from_bom(db, pipeline_run.id)
            datasheet_mcus = identify_mcus_from_datasheets(db, pipeline_run.id)
            detected_mcus = merge_mcu_detections(bom_mcus, datasheet_mcus)
            
            if not detected_mcus:
                print("\n⚠️  No microcontrollers detected in the latest pipeline run.")
                print("    Please ensure your BOM or schematic contains MCU information.")
                return
            
            # Show current configuration if exists
            current_config = load_mcu_configuration()
            if current_config and current_config.primary_mcu:
                print(f"\nCurrent MCU Configuration:")
                print(f"  Primary MCU: {current_config.primary_mcu}")
                if current_config.additional_mcus:
                    print(f"  Additional MCUs: {', '.join(current_config.additional_mcus)}")
                print()
            
            # Prompt for new configuration
            new_config = prompt_mcu_configuration(detected_mcus)
            
            if new_config:
                save_mcu_configuration(new_config)
                print("\n✅ MCU configuration updated successfully!")
            else:
                print("\n Configuration cancelled.")
    
    except Exception as e:
        logger.exception(e)
        print(f"\n❌ Error during MCU reconfiguration: {e}")
