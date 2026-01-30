# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Stata-MCP is an MCP (Model Context Protocol) server that enables LLMs to execute Stata commands and perform regression analysis. It supports both MCP server mode and agent mode for interactive Stata analysis.

## Common Development Commands

### Environment Setup
```bash
# Install dependencies and create virtual environment
uv sync

# Install the package in development mode
uv pip install -e .

# Verify installation
stata-mcp --version
stata-mcp --usable
```

### Building and Distribution
```bash
# Build source distribution and wheels
uv build

# Build specific formats
uv build --sdist    # Source distribution only
uv build --wheel    # Wheel only

# Specify output directory
uv build --out-dir dist/
```

### Running the Application

#### MCP Server Mode (default)
```bash
# Start MCP server with stdio transport (default)
stata-mcp

# Start with specific transport
stata-mcp -t http    # HTTP transport
stata-mcp -t sse     # SSE transport
```

#### Agent Mode
```bash
# Run interactive agent mode
stata-mcp --agent

# Or use uvx for direct execution
uvx stata-mcp --agent
```

#### Utility Commands
```bash
# Check system compatibility
stata-mcp --usable

# Install to Claude Desktop
stata-mcp --install

# Check version
stata-mcp --version
```

### Development with uvx
```bash
# Run without local installation
uvx stata-mcp --version
uvx stata-mcp --agent
uvx stata-mcp --usable
```

## Architecture Overview

### Core Components

1. **MCP Server (`src/stata_mcp/mcp_servers.py`)**
   - FastMCP-based server providing Stata tools and resources
   - Main entry point for LLM interactions
   - Handles cross-platform Stata execution
   - Configurable working directory via `STATA_MCP_CWD` environment variable

2. **Stata Integration (`src/stata_mcp/core/stata/`)**
   - `StataFinder`: Locates Stata executable on different platforms (macOS, Windows, Linux)
   - `StataController`: Manages Stata command execution
   - `StataDo`: Handles do-file execution with logging
   - `builtin_tools/`: Built-in Stata tools
     - `ado_install/`: Package installation (SSC, GitHub, net)
     - `stata_help.py`: Stata command documentation

3. **Data Processing (`src/stata_mcp/core/data_info/`)**
   - `_base.py`: Base class for data info handlers
   - `csv.py`: CSV file analysis and statistics
   - `dta.py`: Stata .dta file analysis
   - `xlsx.py`: Excel file analysis
   - Automatic data type detection and summary statistics

4. **CLI Interface (`src/stata_mcp/cli/`)**
   - Command-line interface for running stata-mcp
   - Support for multiple modes: server, agent, install, version check

### MCP Tools Provided

- `help`: Get Stata command documentation (macOS and Linux only)
- `stata_do`: Execute Stata do-files
- `write_dofile`: Create Stata do-files from code
- `append_dofile`: Append code to existing do-files
- `get_data_info`: Analyze data files (CSV, DTA, XLSX)
- `read_file`: Read file contents
- `ado_package_install`: Install Stata packages from SSC, GitHub, or net sources
- `load_figure`: Load Stata-generated figures
- `mk_dir`: Create directories safely

### File Structure Conventions

Working directory is configurable via `STATA_MCP_CWD` environment variable.
- If not set, tries current directory (if writable) or falls back to `~/Documents`

```
<cwd>/stata-mcp-folder/
├── stata-mcp-log/      # Stata execution logs
├── stata-mcp-dofile/   # Generated do-files
├── stata-mcp-result/   # Analysis results
└── stata-mcp-tmp/      # Temporary files
```

Configuration directory: `~/.statamcp/`
- `config.toml`: Configuration file
- `help/`: Cached help texts
- `stata_mcp_debug.log`: Debug log file (if logging enabled)

### Cross-Platform Support

The project supports:
- **macOS**: Uses Stata MP from `/Applications/Stata/`
- **Windows**: Uses Stata MP from `Program Files`
- **Linux**: Uses `stata-mp` from system PATH

### Configuration

Environment variables:
- `STATA_MCP_CWD`: Working directory (defaults to current directory or `~/Documents`)
- `STATA_MCP_LOGGING_ON`: Enable/disable logging (default: true)
- `STATA_MCP_LOGGING_CONSOLE_HANDLER`: Enable console logging (default: false)
- `STATA_MCP_LOGGING_FILE_HANDLER`: Enable file logging (default: true)
- `STATA_MCP_LOG_FILE`: Custom log file path
- `STATA_MCP_CACHE_HELP`: Enable help caching (default: true)
- `STATA_MCP_DATA_INFO_DECIMAL_PLACES`: Decimal places for data info output
- `STATA_MCP_DATA_INFO_STRING_KEEP_NUMBER`: Max string values to display
- Stata executable path detection via `StataFinder` (or set environment variable)

Configuration file: `~/.statamcp/config.toml`

## Git Commit Standards

This project follows the [Conventional Commits](https://www.conventionalcommits.org/en/v1.0.0/) specification. For detailed guidelines, see [CONTRIBUTING.md](CONTRIBUTING.md).

**Key points:**
- Use format: `<type>[optional scope]: <description>`
- Common types: feat, fix, docs, style, refactor, test, chore, perf, ci, build, revert
- Subject under 50 characters, imperative mood, lowercase
- Reference issues with `Closes #` or `Fixes #`
- **Important:** No co-author information in commits
- Breaking changes: use `!` after type/scope or `BREAKING CHANGE:` footer

**Examples:**
```bash
feat: add user authentication
fix(api): resolve null response issue
docs: update installation guide
```

## Important Notes

- All Python functions must have type annotations and English docstrings
- Use descriptive variable names
- Maintain proper code indentation
- The project requires a valid Stata license
- Default data output is in `<STATA_MCP_CWD>/stata-mcp-folder/` (or auto-detected location)
- For comprehensive documentation, see the `docs/` directory
