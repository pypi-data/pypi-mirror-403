import json
import traceback
from functools import lru_cache
from pathlib import Path
from textwrap import dedent
from typing import Optional, Type

import yaml
from pydantic import BaseModel
from typing_extensions import TypeVar

from mfcli.utils.logger import get_logger

logger = get_logger(__name__)


class AgentConfig(BaseModel):
    name: str
    description: str
    model: str
    instructions: str


@lru_cache
def load_agent_config(path: str | Path) -> AgentConfig:
    with open(path, "r") as f:
        config = yaml.safe_load(f)
        return AgentConfig(
            name=config["name"],
            description=config["description"],
            model=config["model"],
            instructions=config["instructions"]
        )


def format_instructions(instructions: str) -> str:
    return dedent(instructions).strip()


def validation_response(validated: bool, e: Exception | str | None = None) -> dict[str:bool | str]:
    return {"validated": validated, "errors": str(e)}


def format_error_for_llm(e: Exception, msg: str | None = None) -> str:
    return json.dumps({"error": msg or str(e), "stack_trace": traceback.format_exc()})


T = TypeVar('T', bound=BaseModel)


def validate_schema(model: Type[T], response: str) -> T:
    return model.model_validate_json(response)


def head(file_path: str) -> str:
    """
    Get the head of any text file. The agent will run this to determine file subtype.
    :param file_path: path of the file.
    :return: first 50 lines of the file.
    """
    try:
        logger.debug(f"Reading: {file_path}")
        with open(file_path, encoding="utf-8", errors="ignore") as f:
            return str([line for _, line in zip(range(50), f)])
    except Exception as e:
        logger.exception(e)
        format_error_for_llm(e)


# TODO: vectorize_generated_file needs to be updated with project name or chromadb client and placed elsewhere
def vectorize_generated_file(
        file_path: str,
        purpose: str,
        agent_name: str,
        project_id: Optional[str] = None
) -> str:
    """
    Vectorize a generated file into the vector database for future RAG queries.
    
    This shared tool can be used by any agent to vectorize their output files
    (PDFs, CSVs, JSON, etc.) into the vector database for context retrieval.
    
    Args:
        file_path: Path to the file to vectorize
        purpose: Purpose/category of the file (e.g., 'bom', 'errata', 'functional_blocks', 'datasheet')
        agent_name: Name of the agent generating the file
        project_id: Optional project ID for metadata
        
    Returns:
        Success message or error details
    """
    try:
        # Import here to avoid circular dependencies
        from mfcli.utils.datasheet_vectorizer import DatasheetVectorizer

        vectorizer = DatasheetVectorizer()

        # Build metadata
        additional_metadata = {
            "agent": agent_name,
            "generated": True
        }
        if project_id:
            additional_metadata["project_id"] = project_id

        # Vectorize the file
        vectorizer.vectorize_local_file(
            file_path=file_path,
            purpose=purpose,
            additional_metadata=additional_metadata
        )

        logger.info(f"Successfully vectorized file: {file_path} (agent: {agent_name}, purpose: {purpose})")
        return f"Successfully vectorized file: {file_path} with purpose '{purpose}'"

    except Exception as e:
        logger.error(f"Error vectorizing file {file_path}: {e}")
        return format_error_for_llm(e)
