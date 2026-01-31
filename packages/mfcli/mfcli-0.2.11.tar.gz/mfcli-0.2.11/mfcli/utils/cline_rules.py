"""Utility for creating and managing Cline workspace rules files."""
import os
from pathlib import Path
from mfcli.utils.tools import get_git_root
from mfcli.utils.logger import get_logger

logger = get_logger(__name__)


def get_cline_rules_content() -> str:
    """Get the content for the multifactor.md Cline rules file."""
    return """# Multifactor Hardware Project Guidelines

This project uses the **mfcli** (Multifactor CLI) tool for hardware engineering document processing and analysis.

## MCP Server Integration

This project has access to the **mfcli-mcp** Model Context Protocol server, which provides AI-powered access to the project's hardware documentation knowledge base.

### When to Use the MCP Server

**ALWAYS query the mfcli MCP server** when working on tasks that involve:
- Hardware specifications and datasheets
- MCU (microcontroller) information
- Component details and part numbers
- Schematic analysis
- BOM (Bill of Materials) data
- Debug setup configurations
- Functional block diagrams
- Pin configurations
- Power management specifications
- Any hardware-related context

### How to Use the MCP Server

Use the `query_local_rag` tool to search the project's knowledge base:

```
Query the local RAG for "<your search query>" in project "<project_name>"
```

**Examples:**
- "Query the local RAG for 'MSPM0L130x voltage specifications'"
- "Search the knowledge base for 'debug interface pinout'"
- "Find information about 'power supply requirements'"

The MCP server will return:
- Relevant document chunks from processed files
- Metadata (file names, document types)
- Similarity scores (lower = more relevant)

**Note:** After the first query, the project name is remembered, so you only need to specify it once per session.

## Hardware Cheat Sheets

The project includes a **`hw_cheat_sheets/`** folder within the `multifactor/` directory that contains AI-generated JSON summaries of key hardware information:

### Available Cheat Sheets

1. **MCU Datasheets** (`mcu_*.json`)
   - Register maps
   - Peripheral descriptions
   - Technical specifications
   - Pin configurations
   - Memory maps

2. **MCU Errata** (`errata_*.json`)
   - Known hardware issues
   - Workarounds and fixes
   - Affected chip revisions
   - Severity levels

3. **Debug Setup** (`debug_setup_*.json`)
   - Debug interface configurations
   - Pin assignments for debugging
   - Programming instructions
   - Tool requirements

4. **Functional Blocks** (`functional_blocks_*.json`)
   - System architecture
   - Block diagrams
   - Component interconnections
   - Signal flow

### Using Cheat Sheets

**When to use:**
- Quick reference for common specifications
- Understanding system architecture
- Getting started with a new MCU
- Identifying debug configurations

**How to access:**
1. List available cheat sheets: `ls multifactor/hw_cheat_sheets/`
2. Read specific cheat sheet: Read the JSON file directly
3. The JSON format makes it easy to extract specific information programmatically

**Example workflow:**
```
1. Check hw_cheat_sheets/ for a quick overview of the MCU
2. Use query_local_rag for detailed information from datasheets
3. Combine both sources for comprehensive understanding
```

## Project Structure

```
<project_root>/
└── multifactor/              # Main project folder
    ├── config.json           # Project configuration
    ├── file_docket.json      # File tracking metadata
    ├── design/               # Input files for processing
    ├── hw_cheat_sheets/      # AI-generated hardware summaries (JSON)
    ├── generated_files/      # Generated BOMs and outputs
    ├── data_sheets/          # Downloaded component datasheets
    └── pdf_parts/            # Extracted PDF segments
```

## Best Practices

### 1. Always Check Context First
- Review hw_cheat_sheets/ for quick reference
- Query the MCP server for detailed information
- This ensures accurate, project-specific responses

### 2. Be Specific in Queries
- Use part numbers when available
- Include relevant keywords (e.g., "voltage", "pinout", "timing")
- Reference specific sections when needed

### 3. Combine Multiple Sources
- Cheat sheets for overview
- MCP queries for detailed specs
- Cross-reference between documents

### 4. Project Awareness
- All hardware files should be placed in `multifactor/design/` for processing
- Run `mfcli run` to process new or modified files
- The knowledge base stays in sync with processed documents

## Common Tasks

### Getting MCU Specifications
1. Check `hw_cheat_sheets/mcu_*.json` for quick specs
2. Query MCP: "Find voltage and temperature specifications for [MCU_NAME]"
3. Cross-reference with datasheets in `data_sheets/`

### Understanding Debug Setup
1. Read `hw_cheat_sheets/debug_setup_*.json`
2. Query MCP: "What are the debug interface pin assignments?"
3. Look for programming instructions

### Analyzing Schematics
1. Query MCP: "What components are used in [section]?"
2. Check `generated_files/` for extracted BOMs
3. Review component datasheets in `data_sheets/`

### Finding Errata Information
1. Check `hw_cheat_sheets/errata_*.json` for known issues
2. Query MCP: "Are there any errata related to [feature]?"
3. Review workarounds and affected revisions

## Important Notes

- **Data Freshness**: The MCP knowledge base reflects files processed by mfcli. Run `mfcli run` after adding/updating files.
- **Local Processing**: All data is stored locally - no external data transmission.
- **File Changes**: Modified files need to be reprocessed. The system detects changes via MD5 checksums.

## Commands Reference

- `mfcli init` - Initialize project
- `mfcli run` - Process files and update knowledge base
- `mfcli add <file>` - Add specific file to knowledge base
- `mfcli ls` - List vectorized files
- `mfcli doctor` - Check system health
- `mfcli setup-mcp` - Configure MCP server

---

**Remember**: Always leverage the MCP server and hw_cheat_sheets/ for hardware-related tasks. This ensures responses are grounded in the actual project documentation rather than general knowledge.
"""


def create_cline_rules_file(root_dir: str | Path) -> bool:
    """
    Create .clinerules/multifactor.md workspace rules file if it doesn't exist.
    
    Args:
        root_dir: Root directory of the project (will look for git root)
        
    Returns:
        True if file was created or updated, False if it already exists
    """
    try:
        root_path = Path(root_dir)
        
        # Determine the base directory - use git root if available
        git_root = get_git_root(root_path)
        base_dir = git_root if git_root else root_path
        
        # Create .clinerules directory at the base
        clinerules_dir = base_dir / ".clinerules"
        clinerules_dir.mkdir(exist_ok=True, parents=True)
        
        # Path to multifactor.md
        multifactor_rules_file = clinerules_dir / "multifactor.md"
        
        # Check if file already exists
        if multifactor_rules_file.exists():
            logger.info(f"Cline rules file already exists: {multifactor_rules_file}")
            return False
        
        # Create the file with content
        with open(multifactor_rules_file, 'w', encoding='utf-8') as f:
            f.write(get_cline_rules_content())
        
        logger.info(f"Created Cline workspace rules file: {multifactor_rules_file}")
        return True
        
    except Exception as e:
        logger.error(f"Error creating Cline rules file: {e}")
        return False


def update_cline_rules_file(root_dir: str | Path) -> bool:
    """
    Update existing .clinerules/multifactor.md file with latest content.
    
    Args:
        root_dir: Root directory of the project
        
    Returns:
        True if file was updated, False otherwise
    """
    try:
        root_path = Path(root_dir)
        
        # Determine the base directory
        git_root = get_git_root(root_path)
        base_dir = git_root if git_root else root_path
        
        multifactor_rules_file = base_dir / ".clinerules" / "multifactor.md"
        
        if not multifactor_rules_file.exists():
            return create_cline_rules_file(root_dir)
        
        # Update with latest content
        with open(multifactor_rules_file, 'w', encoding='utf-8') as f:
            f.write(get_cline_rules_content())
        
        logger.info(f"Updated Cline workspace rules file: {multifactor_rules_file}")
        return True
        
    except Exception as e:
        logger.error(f"Error updating Cline rules file: {e}")
        return False
