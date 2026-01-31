import os.path
import shutil
import sys
from pathlib import Path
from textwrap import dedent
from typing import List

from mfcli.client.chroma_db import ChromaClient
from mfcli.models.datasheet import Datasheet
from mfcli.models.project import Project
from mfcli.utils.config import get_config
from mfcli.utils.directory_manager import app_dirs, init_directory_structure
from mfcli.utils.logger import get_logger, setup_logging
from mfcli.utils.orm import Session
from mfcli.utils.query_service import QueryService

logger = get_logger(__name__)

warning_message = dedent(
    """
    
    WARNING: This will permanently delete all mfcli data for the current project, including datasheets, cheat sheets, and project data.
    The design folder and its contents will be preserved.
    Should we proceed? (Y/n):
    
    """
)

warning_message_all = dedent(
    """
    
    ⚠️  DANGER ZONE ⚠️
    
    This will permanently delete ALL mfcli data across ALL projects:
    - Entire ChromaDB database (all vector embeddings)
    - Complete SQLite database (all project metadata)
    - All cached data
    
    This is a complete system reset and CANNOT BE UNDONE!
    
    Are you absolutely sure you want to proceed? (Y/n):
    
    """
)


class DataCleaner:
    def __init__(self, db: Session):
        self._db = db
        self._query_service = QueryService(db)
        self._config = get_config()

    @staticmethod
    def _remove_dir(dir_path: Path):
        if not os.path.isdir(dir_path):
            logger.warning(f"Directory does not exist: {dir_path}")
            return
        try:
            shutil.rmtree(dir_path)
        except Exception as e:
            logger.exception(e)
            logger.error(f"Error deleting directory: {dir_path}")

    @staticmethod
    def _remove_file(file_path: Path):
        if not os.path.isfile(file_path):
            logger.debug(f"File does not exist: {file_path}")
            return
        try:
            os.remove(file_path)
            logger.debug(f"Removed file: {file_path}")
        except Exception as e:
            logger.exception(e)
            logger.error(f"Error deleting file: {file_path}")

    def clean(self):
        logger.info("Cleaning mfcli data")
        
        # Clear all datasheet entries from the database
        datasheets: List[Datasheet] = self._query_service.query_all(Datasheet)
        if datasheets:
            logger.debug(f"Deleting {len(datasheets)} datasheet entries from database")
            for datasheet in datasheets:
                self._db.delete(datasheet)
            self._db.commit()
            logger.info(f"Deleted {len(datasheets)} datasheet entries")
        
        projects: List[Project] = self._query_service.query_all(Project)
        for project in projects:
            init_directory_structure(project.repo_dir)
            config_dir = Path(project.repo_dir) / "multifactor"
            
            # Delete ChromaDB collection
            try:
                chroma_db = ChromaClient(project.index_id)
                chroma_db.delete_collection()
                logger.debug(f"Deleted ChromaDB collection for project: {project.name}")
            except Exception as e:
                logger.warning(f"Failed to delete ChromaDB collection for {project.name}: {e}")
            
            # Remove config files
            if app_dirs.config_file_path:
                logger.debug(f"Removing config file: {app_dirs.config_file_path}")
                self._remove_file(app_dirs.config_file_path)
            if app_dirs.file_docket_path:
                logger.debug(f"Removing file docket: {app_dirs.file_docket_path}")
                self._remove_file(app_dirs.file_docket_path)
            
            # Remove directories (excluding design folder)
            for dir_path in [
                app_dirs.data_sheets_dir,
                app_dirs.fw_tasks_dir,
                app_dirs.generated_files_dir,
                app_dirs.reqs_dir,
                app_dirs.cheat_sheets_dir,
                app_dirs.pdf_parts_dir
            ]:
                logger.debug(f"Removing directory: {dir_path}")
                self._remove_dir(dir_path)
            
            # Note: design_dir is intentionally NOT removed to preserve user input files
            logger.info(f"Design folder preserved at: {app_dirs.design_dir}")
            
            # Delete project (CASCADE will handle related records like pipeline_runs)
            logger.debug(f"Deleting project from database: {project.name}")
            self._db.delete(project)
        
        # Commit all project deletions at once
        if projects:
            try:
                self._db.commit()
                logger.info(f"Deleted {len(projects)} project(s) from database")
            except Exception as e:
                logger.error(f"Error committing project deletions: {e}")
                self._db.rollback()
                raise
        
        logger.info("All mfcli data has been cleaned")


def run_data_cleaner():
    with Session() as db:
        DataCleaner(db).clean()


def _clean_multifactor_config_files():
    """
    Delete config.json and file_docket.json from the multifactor folder
    in the current working directory, regardless of database validity.
    """
    try:
        # Get current working directory
        current_dir = Path(os.getcwd())
        multifactor_dir = current_dir / "multifactor"
        
        if not multifactor_dir.exists():
            logger.debug(f"Multifactor directory does not exist: {multifactor_dir}")
            return
        
        # Delete config.json
        config_file = multifactor_dir / "config.json"
        if config_file.exists():
            try:
                os.remove(config_file)
                logger.info(f"Removed config file: {config_file}")
            except Exception as e:
                logger.exception(e)
                logger.error(f"Error deleting config file: {config_file}")
        else:
            logger.debug(f"Config file does not exist: {config_file}")
        
        # Delete file_docket.json
        file_docket = multifactor_dir / "file_docket.json"
        if file_docket.exists():
            try:
                os.remove(file_docket)
                logger.info(f"Removed file docket: {file_docket}")
            except Exception as e:
                logger.exception(e)
                logger.error(f"Error deleting file docket: {file_docket}")
        else:
            logger.debug(f"File docket does not exist: {file_docket}")
    
    except Exception as e:
        logger.exception(e)
        logger.error("Error cleaning multifactor config files")


def clean_all_system_data(user_accepted: bool = False):
    """
    Completely delete all mfcli data across all projects for a fresh start.
    This removes:
    - Entire ChromaDB directory (all vector embeddings)
    - SQLite database file (all project metadata)
    - All app data
    """
    setup_logging()
    
    if not user_accepted:
        user_input = input(warning_message_all)
        if not user_input.strip() == 'Y':
            logger.debug("User cancelled complete system clean")
            sys.exit()
    
    logger.info("Starting complete system clean - deleting ALL mfcli data")
    
    # Remove ChromaDB directory (all vector embeddings)
    if app_dirs.chroma_db_dir and app_dirs.chroma_db_dir.exists():
        try:
            logger.info(f"Deleting entire ChromaDB directory: {app_dirs.chroma_db_dir}")
            shutil.rmtree(app_dirs.chroma_db_dir)
            logger.info("ChromaDB directory deleted successfully")
        except Exception as e:
            logger.exception(e)
            logger.error(f"Error deleting ChromaDB directory: {app_dirs.chroma_db_dir}")
    
    # Remove SQLite database file
    db_path = app_dirs.app_data_dir / "multifactor.db"
    if db_path.exists():
        try:
            logger.info(f"Deleting SQLite database: {db_path}")
            os.remove(db_path)
            logger.info("SQLite database deleted successfully")
        except Exception as e:
            logger.exception(e)
            logger.error(f"Error deleting SQLite database: {db_path}")
    
    # Remove any SQLite journal/wal files
    for db_file in [
        app_dirs.app_data_dir / "multifactor.db-shm",
        app_dirs.app_data_dir / "multifactor.db-wal",
        app_dirs.app_data_dir / "multifactor.db-journal"
    ]:
        if db_file.exists():
            try:
                logger.debug(f"Deleting SQLite auxiliary file: {db_file}")
                os.remove(db_file)
            except Exception as e:
                logger.exception(e)
                logger.error(f"Error deleting file: {db_file}")
    
    # Recreate the directories for a clean state
    app_dirs.chroma_db_dir.mkdir(exist_ok=True, parents=True)
    
    logger.info("Complete system clean finished - all mfcli data has been deleted")
    logger.info("You can now run 'mfcli init' to start fresh")


def clean_app_data(user_accepted: bool = False, clean_all: bool = False):
    """
    Clean mfcli data.
    
    Args:
        user_accepted: Skip confirmation prompt if True
        clean_all: If True, delete entire ChromaDB and SQLite database for complete reset.
                   If False, clean only current project data.
    """
    if clean_all:
        clean_all_system_data(user_accepted)
    else:
        setup_logging()
        if not user_accepted:
            user_input = input(warning_message)
            if not user_input.strip() == 'Y':
                logger.debug("User cancelled")
                sys.exit()
        
        # Always attempt to delete config.json and file_docket.json from multifactor folder
        # regardless of database validity
        _clean_multifactor_config_files()
        
        run_data_cleaner()
