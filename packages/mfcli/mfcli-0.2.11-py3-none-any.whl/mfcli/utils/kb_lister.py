from typing import Dict, List, Set
from mfcli.client.chroma_db import get_chromadb_client_for_project_name
from mfcli.utils.logger import get_logger
from mfcli.utils.orm import Session

logger = get_logger(__name__)


def list_vectorized_files(project_name: str) -> Dict[str, List[str]]:
    """
    List all files that have been vectorized into the ChromaDB database for a project.
    
    Args:
        project_name: Name of the project
        
    Returns:
        Dictionary mapping purpose to list of file names
    """
    try:
        with Session() as db:
            chroma_client = get_chromadb_client_for_project_name(db, project_name)
            
        # Get all documents from the collection
        collection = chroma_client._collection
        results = collection.get()
        
        if not results or not results.get('metadatas'):
            logger.info("No vectorized files found in the knowledge base")
            return {}
        
        # Group files by purpose
        files_by_purpose: Dict[str, Set[str]] = {}
        
        for metadata in results['metadatas']:
            if metadata:
                file_name = metadata.get('file_name', 'Unknown')
                purpose = metadata.get('purpose', 'unknown')
                
                if purpose not in files_by_purpose:
                    files_by_purpose[purpose] = set()
                files_by_purpose[purpose].add(file_name)
        
        # Convert sets to sorted lists for consistent output
        result = {
            purpose: sorted(list(files)) 
            for purpose, files in files_by_purpose.items()
        }
        
        return result
        
    except Exception as e:
        logger.error(f"Failed to list vectorized files for project: {project_name}")
        logger.exception(e)
        raise


def print_vectorized_files(project_name: str) -> None:
    """
    Print all vectorized files in a formatted manner.
    
    Args:
        project_name: Name of the project
    """
    try:
        files_by_purpose = list_vectorized_files(project_name)
        
        if not files_by_purpose:
            print(f"\nNo files have been vectorized for project '{project_name}' yet.")
            return
        
        print(f"\nVectorized files in knowledge base for project '{project_name}':")
        print("=" * 70)
        
        total_files = 0
        for purpose in sorted(files_by_purpose.keys()):
            files = files_by_purpose[purpose]
            print(f"\n{purpose.upper()} ({len(files)} file{'s' if len(files) != 1 else ''}):")
            print("-" * 70)
            for file_name in files:
                print(f"  • {file_name}")
            total_files += len(files)
        
        print("\n" + "=" * 70)
        print(f"Total: {total_files} unique file{'s' if total_files != 1 else ''} vectorized\n")
        
    except Exception as e:
        logger.error(f"Failed to print vectorized files for project: {project_name}")
        print(f"\nError: Failed to list vectorized files. Check logs for details.")
        raise
