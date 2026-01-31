# MCP Server Setup Guide

Complete guide to setting up the mfcli Model Context Protocol (MCP) server for AI coding assistants.

## Table of Contents

- [What is MCP?](#what-is-mcp)
- [Quick Setup](#quick-setup)
- [Manual Setup](#manual-setup)
- [Supported Editors](#supported-editors)
- [Testing](#testing)
- [Troubleshooting](#troubleshooting)
- [Advanced Configuration](#advanced-configuration)

## What is MCP?

The **Model Context Protocol (MCP)** is a standard that allows AI coding assistants to securely access external tools and data sources. The mfcli MCP server provides:

- 🔍 **Semantic search** across your hardware documentation
- 📚 **RAG-powered queries** using ChromaDB vector database
- 🤖 **AI assistant integration** with Cline, Claude Code, and other MCP-compatible tools
- 🔒 **Local execution** - your data never leaves your machine

### Available Tools

The MCP server exposes one primary tool:

**`query_local_rag`** - Query your local hardware knowledge base
- Search across processed schematics, datasheets, BOMs, and netlists
- Get relevant document chunks with metadata
- Specify projects to query specific document sets
- Adjustable result count for focused or broad searches

## Quick Setup

### Prerequisites

1. **mfcli installed** - See [INSTALL.md](INSTALL.md)
2. **Documents processed** - Run `mfcli run` at least once
3. **AI coding assistant installed** - Cline, Claude Code, etc.

### Automatic Configuration

The easiest way to set up the MCP server:

```bash
mfcli setup-mcp
```

This command will:
- 🔍 Detect installed AI coding assistants automatically
- 📝 Locate MCP configuration files
- 💾 Backup existing configurations
- ✅ Add mfcli-mcp server configuration
- ✨ Verify the setup

**That's it!** Just restart your editor and the MCP server will be available.

### MCP Verification During Project Initialization

When you run `mfcli init` to set up a new project, the command will automatically:
- ✅ Check if the mfcli-mcp command is installed
- 🔍 Detect installed AI coding assistants (Cline, Claude Code, etc.)
- ⚠️ Alert you if MCP server is not configured
- 💬 Prompt you to configure MCP server if assistants are detected

This ensures you don't forget to set up the MCP server when starting a new project!

**Example:**
```bash
cd /path/to/hardware/project
mfcli init

# You'll see:
# ======================================================================
#   MCP SERVER VERIFICATION
# ======================================================================
# 
#   ⚠️  Found 1 AI coding assistant(s) but mfcli-mcp is not configured yet.
#
#   Would you like to configure MCP server now? (y/n):
```

If you answer **yes**, the setup will run automatically. If you answer **no**, you can always run `mfcli setup-mcp` later.

## Manual Setup

If automatic setup doesn't work or you prefer manual configuration:

### Step 1: Locate Your MCP Configuration File

**Cline (VS Code Extension)**

- Windows: `%APPDATA%\Code\User\globalStorage\saoudrizwan.claude-dev\settings\cline_mcp_settings.json`
- macOS: `~/Library/Application Support/Code/User/globalStorage/saoudrizwan.claude-dev/settings/cline_mcp_settings.json`
- Linux: `~/.config/Code/User/globalStorage/saoudrizwan.claude-dev/settings/cline_mcp_settings.json`

**Cline (Standalone)**

- All platforms: `~/.cline/mcp_settings.json` or `%USERPROFILE%\.cline\mcp_settings.json` (Windows)

**Claude Desktop**

- macOS: `~/Library/Application Support/Claude/claude_desktop_config.json`
- Linux: `~/.config/Claude/claude_desktop_config.json`
- Windows: `%APPDATA%\Claude\claude_desktop_config.json`

### Step 2: Create or Edit the Configuration File

If the file doesn't exist, create it with this content:

```json
{
  "mcpServers": {
    "mfcli-mcp": {
      "disabled": false,
      "timeout": 60,
      "type": "stdio",
      "command": "mfcli-mcp",
      "autoApprove": ["query_local_rag"]
    }
  }
}
```

If the file exists, add the `mfcli-mcp` entry to the existing `mcpServers` object:

```json
{
  "mcpServers": {
    "existing-server": {
      ...
    },
    "mfcli-mcp": {
      "disabled": false,
      "timeout": 60,
      "type": "stdio",
      "command": "mfcli-mcp",
      "autoApprove": ["query_local_rag"]
    }
  }
}
```

**Note about `autoApprove`:** The `autoApprove` option allows the `query_local_rag` tool to run automatically without requiring explicit user approval each time. This streamlines the workflow when working with hardware documentation, as the tool is read-only and simply queries your local knowledge base.

### Step 3: Restart Your Editor

Close and reopen your AI coding assistant for the changes to take effect.

## Supported Editors

### Cline (VS Code Extension)

- **Installation**: Install from [VS Code Marketplace](https://marketplace.visualstudio.com/items?itemName=saoudrizwan.claude-dev)
- **MCP Support**: ✅ Full support
- **Auto-config**: ✅ Detected automatically

### Cline (Standalone/Windsurf)

- **Installation**: Download from [Cline website](https://cline.bot/)
- **MCP Support**: ✅ Full support
- **Auto-config**: ✅ Detected automatically

### Claude Code

- **Installation**: Download from Anthropic
- **MCP Support**: ✅ Full support
- **Auto-config**: ✅ Detected automatically

### Other MCP-Compatible Tools

Any tool supporting the Model Context Protocol can use mfcli-mcp. Add the configuration manually using the format above.

## Testing

### Verify MCP Server is Running

```bash
# Run system health check
mfcli doctor
```

Look for the "MCP Configuration" section in the output.

### Test in Your AI Assistant

Once configured, try these queries in your AI coding assistant:

**Basic Query:**
```
Query the local RAG for "MSPM0L130x" in project "my_board"
```

**Specific Search:**
```
Use query_local_rag to find information about "power management" with 10 results
```

**Context-Aware:**
```
What are the voltage specifications for this MCU?
(The assistant will use query_local_rag automatically)
```

### Expected Response

The MCP server will return:
- Document chunks matching your query
- Metadata (file names, document types)
- Similarity scores
- ChromaDB database path
- Project name used

## Troubleshooting

### MCP Server Not Detected

**Symptom**: `mfcli setup-mcp` reports no editors found

**Solutions**:

1. **Verify editor installation** - Ensure Cline or Claude Code is actually installed
2. **Check config file exists** - Create the config file manually if it doesn't exist
3. **Run from correct location** - The config files must exist before setup
4. **Restart after editor install** - Install your AI assistant first, then run setup

### Command Not Found Error

**Symptom**: MCP server fails with "mfcli-mcp command not found"

**Solutions**:

1. **Verify installation**:
   ```bash
   which mfcli-mcp  # Linux/macOS
   where mfcli-mcp  # Windows
   ```

2. **Reinstall with pipx**:
   ```bash
   pipx reinstall mfcli
   ```

3. **Check PATH** - Ensure pipx bin directory is in PATH

### ChromaDB Not Found

**Symptom**: "ChromaDB directory not found" error

**Solution**:
```bash
# Process documents to create the database
cd /path/to/hardware/project
mfcli init
mfcli run
```

### Timeout Errors

**Symptom**: MCP server times out during queries

**Solutions**:

1. **Increase timeout** in configuration:
   ```json
   {
     "mfcli-mcp": {
       "timeout": 120
     }
   }
   ```

2. **Check database size** - Large databases may need more time
3. **Reduce n_results** - Request fewer results in queries

### Permission Errors

**Symptom**: Permission denied accessing ChromaDB

**Solutions**:

- Check file permissions on ChromaDB directory
- On Windows: Run editor as same user who installed mfcli
- On Linux/macOS: Ensure user has read access to `~/.local/share/Multifactor/chromadb`

### API Key Errors

**Symptom**: OpenAI API key errors in MCP server

**Solution**:
```bash
# Reconfigure API keys
mfcli configure
```

The MCP server needs OpenAI API key for embeddings.

## Advanced Configuration

### Custom Command Path

If mfcli-mcp is not in PATH, specify full path:

**Windows:**
```json
{
  "mfcli-mcp": {
    "command": "C:\\Users\\username\\.local\\bin\\mfcli-mcp.exe"
  }
}
```

**Linux/macOS:**
```json
{
  "mfcli-mcp": {
    "command": "/home/username/.local/bin/mfcli-mcp"
  }
}
```

### Multiple Projects

The MCP server can query different projects. The `project_name` parameter is remembered between queries:

```python
# First query - specify project
query_local_rag(query="MCU specs", project_name="project_a")

# Subsequent queries - uses last project
query_local_rag(query="power specs")  # Still uses project_a

# Switch projects
query_local_rag(query="different board", project_name="project_b")
```

### Adjusting Result Count

Control how many results are returned:

```python
# More results for broader context
query_local_rag(query="power management", n_results=15)

# Fewer results for focused answers
query_local_rag(query="specific part number", n_results=3)
```

Valid range: 1-20 results (default: 8)

### Environment-Specific Configuration

You can have different MCP configurations for different environments:

**Development:**
```json
{
  "mfcli-mcp": {
    "disabled": false,
    "timeout": 120,
    "command": "mfcli-mcp"
  }
}
```

**Production:**
```json
{
  "mfcli-mcp": {
    "disabled": true
  }
}
```

### Debug Mode

Enable verbose logging for troubleshooting:

```json
{
  "mfcli-mcp": {
    "env": {
      "MFCLI_DEBUG": "1"
    }
  }
}
```

### Auto-Approval for Tools

The `autoApprove` option allows specific tools to run automatically without requiring user approval each time:

```json
{
  "mfcli-mcp": {
    "autoApprove": ["query_local_rag"]
  }
}
```

**Benefits:**
- ✅ Streamlined workflow - No manual approval needed for each query
- ✅ Faster responses - AI assistant can query documentation immediately
- ✅ Better UX - More natural conversation flow
- ✅ Safe for read-only tools - `query_local_rag` only reads local data

**Security Note:** The `query_local_rag` tool is safe to auto-approve because:
- It only performs read operations on your local knowledge base
- No data is modified or transmitted externally
- It operates within your local filesystem permissions
- All data stays on your machine

If you prefer to manually approve each tool use, simply omit the `autoApprove` field from the configuration.

## Best Practices

### Document Organization

- **Use descriptive project names** - Makes queries easier to specify
- **Process regularly** - Keep knowledge base up to date
- **Clean old data** - Remove obsolete documents with `mfcli rm`

### Query Optimization

- **Be specific** - "STM32F4 power consumption" vs "power"
- **Use technical terms** - Part numbers, specifications work best
- **Iterate** - Refine queries based on results

### Security

- **Local only** - MCP server runs locally, no external data transmission
- **API key safety** - Store keys securely in .env file
- **Access control** - MCP server inherits user file permissions

## Usage Examples

### In Cline

```
You: "What's the operating voltage range for the MCU in my board project?"

Cline: [Uses query_local_rag with project_name="board"]
"According to the datasheet, the MCU operates at 1.8V to 3.6V..."
```

### Advanced Queries

```
You: "Find all components rated for automotive temperature range"

Cline: [Uses query_local_rag with optimized query]
"I found 12 components with -40°C to +125°C ratings..."
```

### Cross-Document Search

```
You: "Compare the debug interfaces mentioned in the schematic and reference manual"

Cline: [Queries both document types]
"The schematic shows JTAG on pins 15-19, while the reference manual..."
```

## Getting Help

- **Command Help**: `mfcli setup-mcp --help`
- **System Check**: `mfcli doctor`
- **Issues**: [GitHub Issues](https://github.com/MultifactorAI/multifactor-adk-backend/issues)
- **Documentation**: [README.md](README.md)

## Related Documentation

- [Installation Guide](INSTALL.md)
- [Configuration Guide](CONFIGURATION.md)
- [Main README](README.md)

---

**Note**: The MCP server requires processed documents to function. Run `mfcli run` in your project directory first!
