import json
from pathlib import Path
from typing import List
from mfcli.client.chroma_db import get_chromadb_client_for_project_name
from mfcli.models.file_docket import FileDocket
from mfcli.utils.directory_manager import app_dirs
from mfcli.utils.logger import get_logger
from mfcli.utils.orm import Session

logger = get_logger(__name__)


def _remove_from_file_docket(matching_files: set) -> int:
    """
    Remove files from the file_docket.json based on file names.
    
    Args:
        matching_files: Set of file names to remove
        
    Returns:
        Number of entries removed from docket
    """
    if not app_dirs.file_docket_path or not app_dirs.file_docket_path.exists():
        logger.warning("file_docket.json not found, skipping docket removal")
        return 0
    
    try:
        # Load existing file docket
        docket = FileDocket()
        docket.load_from_json(app_dirs.file_docket_path)
        
        # Track how many entries we remove
        removed_count = 0
        
        # Find and remove matching entries
        entries_to_remove = []
        for entry in docket._docket.entries:
            if entry.name in matching_files:
                entries_to_remove.append(entry)
        
        for entry in entries_to_remove:
            docket.remove(entry)
            removed_count += 1
            logger.debug(f"Removed from docket: {entry.name}")
        
        # Save updated docket back to file
        if removed_count > 0:
            json_data = json.dumps(docket.get_entries(), indent=2)
            with open(app_dirs.file_docket_path, "w") as f:
                f.write(json_data)
            logger.info(f"Updated file_docket.json, removed {removed_count} entries")
        
        return removed_count
        
    except Exception as e:
        logger.error(f"Failed to remove files from file_docket: {e}")
        logger.exception(e)
        return 0


def remove_files_from_kb(project_name: str, filename_pattern: str, confirm: bool = True) -> int:
    """
    Remove files from the ChromaDB knowledge base that match the given filename pattern.
    
    Args:
        project_name: Name of the project
        filename_pattern: Full or partial filename to match (case-insensitive)
        confirm: If True, ask for confirmation before deleting
        
    Returns:
        Number of chunks deleted
    """
    try:
        with Session() as db:
            chroma_client = get_chromadb_client_for_project_name(db, project_name)
        
        # Get all documents from the collection
        collection = chroma_client._collection
        results = collection.get()
        
        if not results or not results.get('metadatas'):
            logger.info("No files found in the knowledge base")
            print("No files found in the knowledge base.")
            return 0
        
        # Find matching file chunks
        matching_ids: List[str] = []
        matching_files: set = set()
        
        for idx, metadata in enumerate(results['metadatas']):
            if metadata:
                file_name = metadata.get('file_name', '')
                # Case-insensitive partial match
                if filename_pattern.lower() in file_name.lower():
                    matching_ids.append(results['ids'][idx])
                    matching_files.add(file_name)
        
        if not matching_ids:
            print(f"\nNo files matching '{filename_pattern}' found in the knowledge base.")
            return 0
        
        # Display matching files
        print(f"\nFound {len(matching_files)} file(s) matching '{filename_pattern}':")
        for file_name in sorted(matching_files):
            print(f"  • {file_name}")
        print(f"\nTotal chunks to delete: {len(matching_ids)}")
        
        # Confirm deletion
        if confirm:
            response = input("\nAre you sure you want to delete these files? (yes/no): ")
            if response.lower() not in ['yes', 'y']:
                print("Deletion cancelled.")
                return 0
        
        # Delete the chunks from ChromaDB
        collection.delete(ids=matching_ids)
        
        # Remove files from file_docket
        removed_from_docket = _remove_from_file_docket(matching_files)
        
        print(f"\nSuccessfully deleted {len(matching_ids)} chunks from {len(matching_files)} file(s).")
        if removed_from_docket > 0:
            print(f"Removed {removed_from_docket} file(s) from file_docket.json")
        logger.info(f"Deleted {len(matching_ids)} chunks from {len(matching_files)} files matching '{filename_pattern}'")
        logger.info(f"Removed {removed_from_docket} entries from file_docket")
        
        return len(matching_ids)
        
    except Exception as e:
        logger.error(f"Failed to remove files from knowledge base for project: {project_name}")
        logger.exception(e)
        print(f"\nError: Failed to remove files. Check logs for details.")
        raise


def list_matching_files(project_name: str, filename_pattern: str) -> List[str]:
    """
    List files that match the given filename pattern without deleting them.
    
    Args:
        project_name: Name of the project
        filename_pattern: Full or partial filename to match (case-insensitive)
        
    Returns:
        List of matching filenames
    """
    try:
        with Session() as db:
            chroma_client = get_chromadb_client_for_project_name(db, project_name)
        
        # Get all documents from the collection
        collection = chroma_client._collection
        results = collection.get()
        
        if not results or not results.get('metadatas'):
            return []
        
        # Find matching files
        matching_files: set = set()
        
        for metadata in results['metadatas']:
            if metadata:
                file_name = metadata.get('file_name', '')
                # Case-insensitive partial match
                if filename_pattern.lower() in file_name.lower():
                    matching_files.add(file_name)
        
        return sorted(list(matching_files))
        
    except Exception as e:
        logger.error(f"Failed to list matching files for project: {project_name}")
        logger.exception(e)
        return []
