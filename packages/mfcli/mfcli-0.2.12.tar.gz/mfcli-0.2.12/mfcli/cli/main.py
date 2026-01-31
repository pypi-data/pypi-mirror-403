import argparse
import asyncio
import os.path
import sys
from pathlib import Path

from mfcli import __version__

# Defer heavy imports until needed to speed up simple commands like --version
# This significantly reduces startup time for commands like -v, --help

cli_prog_name = "mfcli"

desc = "Multifactor AI-powered pipeline to analyze hardware engineering documents like schematics and BOMs"


def init():
    from mfcli.utils.config import get_config
    config = get_config()
    os.environ["GOOGLE_API_KEY"] = config.google_api_key


def run_web_server(port: int):
    import uvicorn
    from fastapi import FastAPI
    from google.adk.cli.fast_api import get_fast_api_app
    agent_dir = str(Path(__file__).parent.parent / "agents")
    db_dir = Path(__file__).parent.parent.parent
    db_url = f"sqlite:///{db_dir / "sessions.db"}"
    app: FastAPI = get_fast_api_app(
        agents_dir=agent_dir,
        session_service_uri=db_url,
        allow_origins=["*"],
        web=True
    )
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=port,
        reload=False
    )


def start_pipeline(project_config):
    from mfcli.pipeline.pipeline import run_with_config
    asyncio.run(run_with_config(project_config))


def run_cli():
    # Parse arguments FIRST before any expensive initialization
    parser = argparse.ArgumentParser(
        prog=cli_prog_name,
        description=desc
    )
    parser.add_argument(
        "-v", "--version",
        action="version",
        version=f"%(prog)s {__version__}"
    )
    sub = parser.add_subparsers(
        dest="command", 
        required=True,
        title="Available Commands",
        description="Run 'mfcli <command> --help' for detailed information about each command"
    )
    
    init_cmd = sub.add_parser(
        "init",
        help="Initialize a new project [--name NAME]",
        description="Initialize a new mfcli project in the current directory. This creates the necessary "
                    "configuration files and directory structure for processing hardware design documents."
    )
    init_cmd.add_argument(
        "--name",
        type=str,
        default=None,
        metavar="NAME",
        help="Project name (optional, defaults to current directory name)"
    )

    sub.add_parser(
        "run",
        help="Process all files in the design folder",
        description="Run the analysis pipeline on all hardware design documents in the current project's "
                    "design folder. This includes BOMs, schematics, datasheets, netlists, and other supported "
                    "file types. Files are classified, analyzed, and vectorized into the knowledge base."
    )
    
    web_cmd = sub.add_parser(
        "web",
        help="Start the interactive web UI [--port PORT]",
        description="Launch the mfcli web interface for interactive analysis and querying of your hardware "
                    "design documents."
    )
    web_cmd.add_argument(
        "--port", 
        type=int, 
        default=9999,
        metavar="PORT",
        help="Port number for the web server (default: 9999)"
    )

    clean_cmd = sub.add_parser(
        "clean",
        help="Remove processed data [--accept] [--all]",
        description="Clean mfcli data for the current project or all projects. This removes vectorized "
                    "documents from the knowledge base and clears the processing history."
    )
    clean_cmd.add_argument(
        "--accept",
        action="store_true",
        help="Skip confirmation prompt"
    )
    clean_cmd.add_argument(
        "--all",
        action="store_true",
        help="Delete entire ChromaDB and SQLite database for a complete fresh start (instead of just current project)"
    )

    add_cmd = sub.add_parser(
        "add",
        help="Add a file to the knowledge base <FILE> [--purpose PURPOSE]",
        description="Manually add a specific file (e.g., datasheet, manual) to the knowledge base without "
                    "running the full pipeline. The file will be vectorized and made searchable."
    )
    add_cmd.add_argument(
        "file",
        type=Path,
        metavar="FILE",
        help="Path to the file to add (e.g., ./datasheets/IC123.pdf)"
    )
    add_cmd.add_argument(
        "--purpose",
        type=str,
        default="datasheet",
        metavar="PURPOSE",
        help="Category for the file: 'datasheet', 'manual', 'specification', etc. (default: datasheet)"
    )

    sub.add_parser(
        "ls",
        help="List all files in the knowledge base",
        description="Display all files that have been vectorized and stored in the knowledge base for the "
                    "current project. Shows file names, types, and purposes."
    )

    rm_cmd = sub.add_parser(
        "rm",
        help="Remove files from knowledge base <PATTERN> [--yes]",
        description="Remove one or more files from the knowledge base by searching for a filename or partial "
                    "match. This does not delete the original files, only removes them from the searchable index."
    )
    rm_cmd.add_argument(
        "filename",
        type=str,
        metavar="PATTERN",
        help="Filename or partial pattern to match (case-insensitive, e.g., 'stm32' or 'datasheet.pdf')"
    )
    rm_cmd.add_argument(
        "--yes",
        action="store_true",
        help="Skip confirmation prompt and remove immediately"
    )

    configure_cmd = sub.add_parser(
        "configure",
        help="Configure API keys and settings [--check]",
        description="Run an interactive wizard to set up or modify your API keys (Google Gemini, OpenAI, DigiKey) "
                    "and other configuration settings. Use --check to validate existing configuration."
    )
    configure_cmd.add_argument(
        "--check",
        action="store_true",
        help="Check and display current configuration without making changes"
    )

    sub.add_parser(
        "setup-mcp",
        help="Configure MCP server for AI code editors",
        description="Automatically configure the mfcli MCP (Model Context Protocol) server for use with "
                    "Cline, Claude Code, and other MCP-compatible AI coding assistants."
    )

    sub.add_parser(
        "doctor",
        help="Run system diagnostics",
        description="Perform comprehensive health checks on your mfcli installation, including Python version, "
                    "API connectivity, database status, and configuration validation."
    )

    sub.add_parser(
        "pre-uninstall",
        help="Prepare for uninstallation",
        description="Check for running mfcli processes and prepare the system for safe uninstallation. "
                    "Run this before uninstalling mfcli to avoid orphaned processes."
    )

    log_level_cmd = sub.add_parser(
        "log-level",
        help="View or change logging verbosity [LEVEL]",
        description="Display the current logging level or set a new one to control how much diagnostic "
                    "information mfcli outputs. Use DEBUG for troubleshooting, INFO for normal operation."
    )
    log_level_cmd.add_argument(
        "level",
        type=str,
        nargs="?",
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        metavar="LEVEL",
        help="New logging level: DEBUG, INFO, WARNING, ERROR, or CRITICAL (omit to view current level)"
    )

    regenerate_cmd = sub.add_parser(
        "regenerate",
        help="Force regeneration of a specific cheat sheet <TYPE> [--list]",
        description="Force regeneration of specific cheat sheet types without running the full pipeline. "
                    "This is useful when you want to update a cheat sheet with new prompts or logic, or "
                    "when a previous generation failed. Uses the most recent pipeline run data."
    )
    regenerate_cmd.add_argument(
        "type",
        type=str,
        nargs="?",
        metavar="TYPE",
        help="Cheat sheet type to regenerate: mcu, errata, debug_setup, schematic, functional_blocks, "
             "summary, or 'all' for all types (use --list to see descriptions)"
    )
    regenerate_cmd.add_argument(
        "--list",
        action="store_true",
        help="List all available cheat sheet types and their descriptions"
    )
    regenerate_cmd.add_argument(
        "--file",
        type=Path,
        metavar="FILE",
        help="Specific file to generate cheat sheet from (bypasses database lookup)"
    )

    sub.add_parser(
        "configure-mcu",
        help="Configure microcontroller settings",
        description="Interactively configure which microcontrollers are in your design. "
                    "Identifies MCUs from BOM and datasheets, then prompts you to select a primary MCU "
                    "and any additional MCUs. This configuration is saved to config.json and helps the "
                    "system understand your hardware architecture."
    )

    # Parse early to catch --version and --help before initialization
    args = parser.parse_args()

    
    # Only initialize if we're running a real command (not --version or --help which exit early)
    # Import logger here to avoid loading logging infrastructure for --version
    from mfcli.utils.logger import setup_logging, get_logger
    from mfcli.utils.ssl_installer import check_and_install_ssl_certificates
    
    setup_logging()
    logger = get_logger(__name__)
    logger.debug("Starting CLI")
    
    # Commands that don't need full initialization
    lightweight_commands = {"pre-uninstall", "doctor", "setup-mcp", "configure", "log-level"}
    
    # Only run expensive checks for commands that need them
    if args.command not in lightweight_commands:
        from mfcli.cli.dependencies import check_dependencies
        init()
        check_and_install_ssl_certificates()
        logger.debug("Checking dependencies")
        check_dependencies()
    
    from mfcli.utils.directory_manager import init_directory_structure, app_dirs
    init_directory_structure(os.getcwd())
    
    if args.command == "init":
        from mfcli.crud.project import init_project
        init_project(args.name)
    elif args.command == "clean":
        from mfcli.utils.data_cleaner import clean_app_data
        clean_app_data(args.accept, args.all)
    elif args.command == "configure":
        from mfcli.utils.configurator import run_configuration_wizard, check_configuration
        if args.check:
            check_configuration()
        else:
            run_configuration_wizard()
    elif args.command == "setup-mcp":
        from mfcli.utils.mcp_configurator import setup_mcp_servers
        setup_mcp_servers()
    elif args.command == "doctor":
        from mfcli.utils.system_check import run_system_check
        run_system_check()
    elif args.command == "pre-uninstall":
        from mfcli.utils.pre_uninstall import run_pre_uninstall_check
        run_pre_uninstall_check()
    elif args.command == "log-level":
        from mfcli.utils.configurator import set_log_level
        set_log_level(args.level)
    elif args.command == "regenerate":
        from mfcli.utils.cheatsheet_regenerator import list_cheatsheet_types, regenerate_cheatsheet
        if args.list:
            list_cheatsheet_types()
        elif not args.type:
            print("Error: Please specify a cheat sheet type to regenerate or use --list to see available types.")
            print("Usage: mfcli regenerate <TYPE>")
            print("       mfcli regenerate --list")
            sys.exit(1)
        else:
            # Need project config for regenerate
            from mfcli.crud.project import read_project_config_file
            config_file_path = app_dirs.config_file_path
            if not os.path.exists(config_file_path):
                print('Could not find metadata file. Are you in the correct directory? Or if this is a new project, please initialize this repo with "mfcli init"')
                sys.exit(1)
            project_config = read_project_config_file()
            regenerate_cheatsheet(project_config, args.type, args.file)
    else:
        # Commands that need project config
        from mfcli.crud.project import read_project_config_file, init_project
        
        # Check if config file exists before reading
        config_file_path = app_dirs.config_file_path
        
        if not os.path.exists(config_file_path):
            if args.command == "run":
                # Prompt user to run init for the run command
                print('\nCould not find metadata file. This project has not been initialized yet.')
                response = input('Would you like to initialize this project now? (y/n): ').strip().lower()
                
                if response in ['y', 'yes']:
                    print('\nInitializing project...')
                    init_project(None)
                    print('\nProject initialized successfully! Continuing with run command...\n')
                    # Now read the config that was just created
                    project_config = read_project_config_file()
                else:
                    print('\nProject not initialized. Please run "mfcli init" to initialize the project.')
                    sys.exit(1)
            else:
                # For other commands, just show the standard error message
                print('Could not find metadata file. Are you in the correct directory? Or if this is a new project, please initialize this repo with "mfcli init"')
                sys.exit(1)
        else:
            # Config file exists, read it normally
            project_config = read_project_config_file()
        
        if args.command == "run":
            start_pipeline(project_config)
        elif args.command == "web":
            run_web_server(args.port)
        elif args.command == "add":
            from mfcli.utils.vectorizer import add_file_to_db
            add_file_to_db(project_config.name, args.file, args.purpose)
        elif args.command == "ls":
            from mfcli.utils.kb_lister import print_vectorized_files
            print_vectorized_files(project_config.name)
        elif args.command == "rm":
            from mfcli.utils.kb_remover import remove_files_from_kb
            remove_files_from_kb(project_config.name, args.filename, confirm=not args.yes)
        elif args.command == "configure-mcu":
            from mfcli.utils.mcu_configurator import reconfigure_mcus_cli
            reconfigure_mcus_cli()
