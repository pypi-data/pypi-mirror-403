import os
import sys
from pathlib import Path
from mfcli.utils.tools import get_git_root


class DirectoryManager:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        # OS-specific base appdata location
        if os.name == "nt":
            app_data_base = Path(os.getenv("LOCALAPPDATA", os.getenv("APPDATA")))
        elif sys.platform == "darwin":
            app_data_base = Path.home() / "Library" / "Application Support"
        else:
            app_data_base = Path.home() / ".local" / "share"

        self.home_dir: Path = Path(os.path.expanduser("~")) / "Multifactor"
        self.env_file_path: Path = self.home_dir / ".env"

        # User app directories
        self.app_data_dir: Path = app_data_base / "Multifactor"
        self.chroma_db_dir: Path = self.app_data_dir / "chromadb"

        self.app_data_dir.mkdir(exist_ok=True, parents=True)
        self.chroma_db_dir.mkdir(exist_ok=True, parents=True)
        self.home_dir.mkdir(exist_ok=True, parents=True)

        # Repo dirs
        self.root_dir: Path | None = None
        self.design_dir: Path | None = None
        self.data_sheets_dir: Path | None = None
        self.fw_tasks_dir: Path | None = None
        self.generated_files_dir: Path | None = None
        self.cheat_sheets_dir: Path | None = None
        self.reqs_dir: Path | None = None
        self.pdf_parts_dir: Path | None = None
        self.metadata_dir: Path | None = None
        self.config_file_path: Path | None = None
        self.file_docket_path: Path | None = None

        self._initialized = True

    def initialize(self, root: str):
        # Accept file or directory
        root_path = Path(root)
        if root_path.is_file():
            self.root_dir = root_path.parent
        else:
            self.root_dir = root_path

        # Determine the base directory for project folders
        # If in a git repo, use the git root; otherwise use the current directory
        git_root = get_git_root(self.root_dir)
        if git_root:
            # Use git root for all project folders
            base_dir = git_root
        else:
            # Not a git repo, use the current directory
            base_dir = self.root_dir
        
        # Create "multifactor" parent folder at the base directory
        multifactor_parent = base_dir / "multifactor"
        
        # Design folder - where users place files to be ingested
        self.design_dir = multifactor_parent / "design"
        
        # Repo directories - all created within the "multifactor" folder
        self.data_sheets_dir = multifactor_parent / "data_sheets"
        self.fw_tasks_dir = multifactor_parent / "fw_tasks"
        self.generated_files_dir = multifactor_parent / "generated_files"
        self.cheat_sheets_dir = multifactor_parent / "hw_cheat_sheets"
        self.reqs_dir = multifactor_parent / "requirements"
        self.pdf_parts_dir = multifactor_parent / "pdf_parts"
        
        # Metadata directory - also within the "multifactor" folder
        self.metadata_dir = multifactor_parent
        self.config_file_path = self.metadata_dir / "config.json"
        self.file_docket_path = self.metadata_dir / "file_docket.json"

        # Create all dirs
        self._create_directory_structure()

    def _create_directory_structure(self):
        for directory in [
            self.design_dir,
            self.data_sheets_dir,
            self.fw_tasks_dir,
            self.generated_files_dir,
            self.cheat_sheets_dir,
            self.reqs_dir,
            self.pdf_parts_dir,
            self.app_data_dir,
            self.chroma_db_dir,
            self.metadata_dir
        ]:
            directory.mkdir(parents=True, exist_ok=True)


app_dirs = DirectoryManager()


def init_directory_structure(root_dir: str):
    app_dirs.initialize(root_dir)
