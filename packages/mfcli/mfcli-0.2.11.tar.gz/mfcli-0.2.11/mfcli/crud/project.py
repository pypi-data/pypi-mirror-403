import json
import os
import re
import sys
from pathlib import Path
from typing import List
from uuid import uuid4

from mfcli.utils.directory_manager import app_dirs
from pydantic import ValidationError

from mfcli.models.project import Project, project_name_regex
from mfcli.models.project_metadata import ProjectConfig
from mfcli.utils.logger import get_logger
from mfcli.utils.migrations import run_migrations
from mfcli.utils.orm import Session
from mfcli.utils.tools import get_git_repo_name

project_name_const = "Project name length must be between 3 and 45 and have any of these characters: [A-Za-z0-9_-]"

logger = get_logger()


def create_project(db: Session, repo_dir: str, name: str) -> Project:
    logger.debug(f"Creating project with name: {name}")
    name = name.strip()
    if not re.match(project_name_regex, name):
        raise ValueError(project_name_const)
    existing_project = db.query(Project).filter(Project.name == name).one_or_none()
    if existing_project:
        raise ValueError("A project with this name already exists")
    project = Project(
        name=name,
        repo_dir=str(Path(repo_dir)),
        index_id=uuid4().hex
    )
    db.add(project)
    db.flush()
    logger.debug(f"Project created: {project}")
    return project


def get_project_by_name(db: Session, name: str) -> Project:
    project: Project | None = (
        db.query(Project)
        .filter(Project.name == name)
        .one_or_none()
    )
    if not project:
        raise ValueError(f"A project by this name does not exist: {name}")
    return project


def _list_projects(db: Session) -> List[Project]:
    return db.query(Project).all()


def read_project_config_file() -> ProjectConfig:
    file_path = app_dirs.config_file_path
    logger.debug(f"Reading metadata file: {file_path}")
    if not os.path.exists(file_path):
        print('Could not find metadata file. Are you in the correct directory? Or if this is a new project, please initialize this repo with "mfcli init"')
        sys.exit(1)
    if not os.access(file_path, os.R_OK):
        print(f"Could not access repo file: {file_path}")
        sys.exit(1)
    with open(file_path, "r") as f:
        try:
            return ProjectConfig(**json.loads(f.read()))
        except ValidationError as e:
            logger.error(f"Metadata file is corrupted: {file_path}")
            raise e


def init_project(project_name: str | None, repo_dir: Path | None = None):
    try:
        with Session() as db:
            run_migrations()
            if not repo_dir:
                repo_dir = Path(os.getcwd())
            logger.debug(f"Initializing project for repo dir: {repo_dir}")
            file_path = app_dirs.config_file_path
            if os.path.exists(file_path):
                project_config = read_project_config_file()
                
                # Check if project exists in database
                try:
                    get_project_by_name(db, project_config.name)
                    logger.debug(f"Project has already been initialized: {project_config.name}")
                    
                    # Create Cline workspace rules file if it doesn't exist
                    try:
                        from mfcli.utils.cline_rules import create_cline_rules_file
                        if create_cline_rules_file(repo_dir):
                            print("\n✅ Created Cline workspace rules file: .clinerules/multifactor.md")
                            print("   This file provides AI assistants with context about using the MCP server and hw_cheat_sheets/")
                    except Exception as e:
                        print(f"\n⚠️  Warning: Could not create Cline rules file: {e}")
                        logger.error(f"Error creating Cline rules file: {e}")
                    
                    # Run MCP verification even for already initialized projects
                    try:
                        from mfcli.utils.mcp_configurator import verify_and_prompt_mcp_setup
                        verify_and_prompt_mcp_setup()
                    except Exception as e:
                        print(f"\n⚠️  Warning: Could not verify MCP setup: {e}")
                        logger.error(f"Error during MCP verification: {e}")
                    return
                except ValueError:
                    # Project config exists but not in database - ask user if they want to add it
                    print(f"\n⚠️  Found existing config.json with project name: {project_config.name}")
                    print(f"   However, this project is not in the database.")
                    print(f"   This can happen if the database was deleted or you moved to a new machine.\n")
                    
                    response = input(f"Would you like to add '{project_config.name}' to the database? (y/n): ").strip().lower()
                    
                    if response in ['y', 'yes']:
                        logger.debug(f"Adding existing project to database: {project_config.name}")
                        project = Project(
                            name=project_config.name,
                            repo_dir=str(repo_dir),
                            index_id=uuid4().hex
                        )
                        db.add(project)
                        db.flush()
                        db.commit()
                        print(f"\n✅ Successfully added project '{project_config.name}' to the database!")
                        
                        # Create Cline workspace rules file if it doesn't exist
                        try:
                            from mfcli.utils.cline_rules import create_cline_rules_file
                            if create_cline_rules_file(repo_dir):
                                print("\n✅ Created Cline workspace rules file: .clinerules/multifactor.md")
                                print("   This file provides AI assistants with context about using the MCP server and hw_cheat_sheets/")
                        except Exception as e:
                            print(f"\n⚠️  Warning: Could not create Cline rules file: {e}")
                            logger.error(f"Error creating Cline rules file: {e}")
                        
                        # Run MCP verification
                        try:
                            from mfcli.utils.mcp_configurator import verify_and_prompt_mcp_setup
                            verify_and_prompt_mcp_setup()
                        except Exception as e:
                            print(f"\n⚠️  Warning: Could not verify MCP setup: {e}")
                            logger.error(f"Error during MCP verification: {e}")
                        return
                    else:
                        print(f"\n❌ Project not added to database.")
                        print(f"   If you want to reinitialize with a different name, delete config.json first.")
                        sys.exit(1)

            repo_dir_path = repo_dir
            repo_dir = str(repo_dir)
            if not project_name:
                # Try to get git repository name as default
                git_repo_name = get_git_repo_name(repo_dir_path)
                if git_repo_name:
                    user_input = input(f"Please choose a project name [A-Za-z0-9_-] (default press enter to accept: {git_repo_name}): ").strip()
                    project_name = user_input if user_input else git_repo_name
                else:
                    project_name = input("Please choose a project name [A-Za-z0-9_-]: ")
            create_project(db, repo_dir, project_name)
            project_config = ProjectConfig(name=project_name)
            logger.debug(f"Creating metadata file: {file_path}")
            with open(file_path, "w") as f:
                f.write(json.dumps(project_config.model_dump(), indent=2))
            db.commit()
            
            # Create Cline workspace rules file
            try:
                from mfcli.utils.cline_rules import create_cline_rules_file
                if create_cline_rules_file(repo_dir):
                    print("\n✅ Created Cline workspace rules file: .clinerules/multifactor.md")
                    print("   This file provides AI assistants with context about using the MCP server and hw_cheat_sheets/")
            except Exception as e:
                print(f"\n⚠️  Warning: Could not create Cline rules file: {e}")
                logger.error(f"Error creating Cline rules file: {e}")
            
            # Verify and prompt for MCP setup after successful initialization
            try:
                from mfcli.utils.mcp_configurator import verify_and_prompt_mcp_setup
                verify_and_prompt_mcp_setup()
            except Exception as e:
                print(f"\n⚠️  Warning: Could not verify MCP setup: {e}")
                logger.error(f"Error during MCP verification: {e}")
    except Exception as e:
        logger.exception(e)
        print(f"\n❌ Error initializing project: {e}")
        logger.error("Error initializing project")
