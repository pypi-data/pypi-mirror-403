import chromadb
from chromadb.utils import embedding_functions
from typing import Annotated, Optional

from mfcli.crud.project import get_project_by_name
from mfcli.mcp.mcp_instance import mcp
from mfcli.mcp.state_manager import state_manager
from mfcli.utils.config import get_config
from mfcli.utils.directory_manager import app_dirs
from mfcli.utils.orm import Session


def get_chroma_index(index_name: str):
    config = get_config()
    chroma_client = chromadb.PersistentClient(path=app_dirs.chroma_db_dir)
    openai_ef = embedding_functions.OpenAIEmbeddingFunction(
        api_key=config.openai_api_key,
        model_name=config.embedding_model
    )
    return chroma_client.get_collection(index_name, embedding_function=openai_ef)


def get_index_id_for_project_name(project_name: str):
    with Session() as db:
        project = get_project_by_name(db, project_name)
        return project.index_id


@mcp.tool()
def query_local_rag(
    query: Annotated[str, "Search query for engineering documentation (e.g., 'IEC 61000-4-2', 'power management')"],
    project_name: Annotated[Optional[str], "The name of the project. RECOMMENDED: Provide this parameter even though it's optional. The project name can be found in the config.json file located in the multifactor folder. If not provided, uses the last known project name."] = None,
    n_results: Annotated[int, "Number of results to return (1-20, default: 8)"] = 8,
    task_progress: Annotated[Optional[str], "A checklist showing task progress after this tool use is completed"] = None
) -> dict:
    """Query local hardware engineering documentation.

    Use this tool to search for engineering documentation, design patterns,
    technical specifications, and best practices from the local knowledge base.

    Args:
        query: Search query for engineering documentation (e.g., "IEC 61000-4-2", "power management")
        project_name: RECOMMENDED - The name of the project. Although optional, it is recommended to provide this parameter. 
                     The project name can be found in the config.json file located in the multifactor folder. 
                     If not provided, uses the last known project name.
        n_results: Number of results to return (1-20, default: 8)
        task_progress: A checklist showing task progress after this tool use is completed

    Returns:
        Dictionary containing:
        - documents: List of text chunks matching the query
        - metadatas: Metadata for each document
        - distances: Similarity distances (lower is more similar)
        - count: Number of results returned
        - chromadb_path: Path to the ChromaDB database
        - project_name: The project name that was used for the query
    """
    
    # If project_name is not provided, use the last known project name
    if project_name is None:
        project_name = state_manager.get_last_project_name()
        if project_name is None:
            return {
                "error": "No project name provided and no previous project name found. Please provide a project_name parameter. The project name can be found in the config.json file located in the multifactor folder.",
                "documents": [],
                "metadatas": [],
                "distances": [],
                "count": 0,
                "chromadb_path": app_dirs.chroma_db_dir,
                "project_name": None
            }
    
    # Store the project name for future use
    state_manager.set_last_project_name(project_name)
    
    collection = get_chroma_index(get_index_id_for_project_name(project_name))

    # Clamp n_results between 1 and 20
    n_results = min(max(n_results, 1), 20)

    try:
        results = collection.query(
            query_texts=[query],
            n_results=n_results
        )

        documents = results["documents"][0] if results["documents"] else []
        metadatas = results["metadatas"][0] if results["metadatas"] else []
        distances = results["distances"][0] if results["distances"] else []

        return {
            "documents": documents,
            "metadatas": metadatas,
            "distances": distances,
            "count": len(documents),
            "chromadb_path": app_dirs.chroma_db_dir,
            "project_name": project_name
        }
    except Exception as e:
        return {
            "error": str(e),
            "documents": [],
            "metadatas": [],
            "distances": [],
            "count": 0,
            "chromadb_path": app_dirs.chroma_db_dir,
            "project_name": project_name
        }
