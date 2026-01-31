import sys

import chromadb
from chromadb.utils import embedding_functions

from mfcli.mcp.mcp_instance import mcp
from mfcli.utils.config import get_config
from mfcli.utils.directory_manager import app_dirs

# Import tools to register them with mcp
import mfcli.mcp.tools.query_knowledgebase


def chroma_db_connection_test():
    try:
        config = get_config()
        test_chroma_client = chromadb.PersistentClient(path=app_dirs.chroma_db_dir)
        test_openai_ef = embedding_functions.OpenAIEmbeddingFunction(
            api_key=config.openai_api_key,
            model_name=config.embedding_model
        )
        test_chroma_client.get_or_create_collection("engineering_docs", embedding_function=test_openai_ef)
        print(f"✓ Connected to ChromaDB at: {app_dirs.chroma_db_dir}", file=sys.stderr, flush=True)
        print(f"✓ Collection: engineering_docs", file=sys.stderr, flush=True)
    except Exception as e:
        print(f"✗ Failed to connect to ChromaDB: {e}", file=sys.stderr, flush=True)
        raise


def main():
    """Entry point for mfcli-mcp command."""
    chroma_db_connection_test()
    mcp.run()


if __name__ == "__main__":
    main()
