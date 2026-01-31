from typing import List

from mfcli.agents.tools.general import format_error_for_llm
from mfcli.client.chroma_db import ChromaClient
from mfcli.crud.project import get_project_by_name
from mfcli.models.project import Project
from mfcli.utils.logger import get_logger
from mfcli.utils.orm import Session

logger = get_logger(__name__)


def list_projects() -> List[str]:
    """
    Agent will use this tool to list the names of projects.
    If the user does not supply a project name this tool must be called and the user prompted to select a project.
    :return: list of project names
    """
    with Session() as db:
        projects: List[Project] = db.query(Project).all()
        return [project.name for project in projects]


def query_knowledgebase(project_name: str, query: str) -> str:
    """
    Agent will use this tool to do RAG (query knowledgebase).
    The user must supply a project_name to select the right knowledgebase.
    :param project_name:
    :param query:
    :return:
    """
    with Session() as db:
        project = get_project_by_name(db, project_name)
        logger.debug(f"Querying knowledge base for query: {query}")
        try:
            chunks = ChromaClient(project.index_id).query(query)
            return str([{
                "chunk": chunk.document,
                "metadata": chunk.metadata
            } for chunk in chunks])
        except Exception as e:
            return format_error_for_llm(e)
