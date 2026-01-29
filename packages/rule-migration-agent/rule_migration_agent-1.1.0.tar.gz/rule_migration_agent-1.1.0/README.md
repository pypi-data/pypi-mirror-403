# Rule Migration Agent

A production-ready bidirectional conversion tool for migrating between **Cursor rules** (`.cursor/rules`) and **Claude Skills** (`.claude/skills`). Keep your AI agent configurations synchronized across both platforms with automatic validation, conflict resolution, and state tracking.

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![Claude Code Plugin](https://img.shields.io/badge/Claude%20Code-Plugin-blue)](https://code.claude.com/docs/en/discover-plugins)

## Installation

### Option 1: Install via PyPI (Recommended)

```bash
pip install rule-migration-agent
```

After installation, use the command:
```bash
rule-migration [project-path]
# or
migrate-rules [project-path]
```

### Option 2: Install as Claude Code Plugin

This agent is available as a Claude Code plugin! Install it to use `/migrate` and `/setup` commands directly in [Claude Code](https://code.claude.com/docs/en/discover-plugins).

The plugin lives in `claude-code-plugin/`; the repo root has `.claude-plugin/marketplace.json` with `"source": "./claude-code-plugin"`, so adding the repo as a marketplace loads the plugin from that folder.

**From GitHub (recommended for publishing):**
```bash
/plugin marketplace add patrikmichi/rule-migration-agent
/plugin install rule-migration-agent@rule-migration-agent
```

**From a local path** (e.g. clone or `agents/rule-migration-agent`):
```bash
# Path to the repo root (the folder that contains .claude-plugin/marketplace.json)
/plugin marketplace add ./rule-migration-agent
# or, if you're in the parent:  /plugin marketplace add ./agents/rule-migration-agent

# Then install (use the marketplace name from /plugin marketplace list if it differs)
/plugin install rule-migration-agent@rule-migration-agent
```

After installation, use `/migrate` and `/setup` in Claude Code. Run `/setup` once to install the Python tools (pip first, then GitHub clone).

### Option 3: Install from GitHub

```bash
git clone https://github.com/patrikmichi/rule-migration-agent.git
cd rule-migration-agent
python3 install_agent.py
```

## Features

- ✅ **Bidirectional Conversion** - Convert between Cursor rules and Claude Skills seamlessly
- ✅ **Auto-Detection** - Automatically detects conversion direction based on existing files
- ✅ **Latest Documentation** - Always fetches latest format specs from official sources
- ✅ **Validation** - Validates output to ensure compliance with format requirements
- ✅ **State Tracking** - Tracks changes and skips unchanged files for efficiency
- ✅ **Conflict Resolution** - Shows diffs and handles conflicts gracefully
- ✅ **History & Rollback** - Maintains conversion history with rollback support
- ✅ **AGENTS.md Generation** - Auto-generates documentation when both formats exist
- ✅ **Persistent Memory** - Synchronizes project context (`brief.md`, `decisions.md`) across platforms
- ✅ **Legacy Modernization** - Automatically converts old `.claude/commands/` to latest specs
- ✅ **Batch Processing** - Process multiple projects at once

## Table of Contents

- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Setup](#setup)
  - [For Beginners](#for-beginners-step-by-step)
  - [For Skilled Users](#for-skilled-users-quick-setup)
- [Usage](#usage)
- [Examples](#examples)
- [Advanced Features](#advanced-features)
- [Troubleshooting](#troubleshooting)
- [Documentation](#documentation)
- [Contributing](#contributing)

> **New to the agent?** Check out the [Quick Start Guide](QUICKSTART.md) for a 5-minute setup!

## Prerequisites

- **Python 3.8 or higher** - Check your version: `python3 --version` or `python --version`
  - *Note: The `/setup` command can install Python automatically on macOS/Linux*
- **pip** - Python package installer (usually comes with Python)
- **Internet connection** - For fetching latest documentation (optional, uses cache if offline)

### Checking Your Python Installation

**On macOS/Linux:**
```bash
python3 --version
# Should show: Python 3.8.x or higher
```

**On Windows:**
```bash
python --version
# Should show: Python 3.8.x or higher
```

If Python is not installed, download it from [python.org](https://www.python.org/downloads/).

## Setup

### 🚀 Quick Setup (Recommended)

**The easiest way - fully automated:**

Just run the `/setup` command in Cursor or Claude Code:
```
/setup
```

This automatically:
- ✅ Checks for Python 3.8+
- ✅ Installs Python if missing (macOS/Linux)
- ✅ Installs all dependencies
- ✅ Verifies installation
- ✅ Creates default configuration

**That's it!** You're ready to use `/migrate` to convert rules and skills.

### Manual Installation (Alternative)

If you prefer manual setup or the automated setup doesn't work:

### For Beginners (Step-by-Step)

#### Step 1: Download or Clone the Agent

**Option A: If you have Git installed:**
```bash
git clone <repository-url>
cd rule-migration-agent
```

**Option B: Download as ZIP:**
1. Download the repository as a ZIP file
2. Extract it to a folder (e.g., `~/Desktop/rule-migration-agent`)
3. Open Terminal/Command Prompt and navigate to the folder:
   ```bash
   cd ~/Desktop/rule-migration-agent
   ```

#### Step 2: Create a Virtual Environment (Recommended)

This keeps the agent's dependencies separate from your system Python:

**On macOS/Linux:**
```bash
python3 -m venv venv
source venv/bin/activate
```

**On Windows:**
```bash
python -m venv venv
venv\Scripts\activate
```

You should see `(venv)` at the start of your command prompt.

#### Step 3: Install Dependencies

```bash
pip install -r requirements.txt
```

This installs:
- `PyYAML` - For parsing YAML frontmatter
- `requests` - For fetching documentation
- `beautifulsoup4` - For parsing HTML documentation
- `tqdm` - For progress bars
- `rich` - For beautiful terminal output

#### Step 4: Verify Installation

Test that everything works:

```bash
python3 migrate.py --help
# or on Windows:
python migrate.py --help
```

You should see the help menu with all available options.

#### Step 5: Make the Script Executable (macOS/Linux only)

```bash
chmod +x migrate.py
```

Now you can run it directly:
```bash
./migrate.py --help
```

### For Skilled Users (Quick Setup)

```bash
# Clone and navigate
git clone <repository-url> && cd rule-migration-agent

# Create virtual environment (optional but recommended)
python3 -m venv venv && source venv/bin/activate  # Linux/macOS
# or: python -m venv venv && venv\Scripts\activate  # Windows

# Install dependencies
pip install -r requirements.txt

# Verify
python3 migrate.py --help
```

**One-liner for experienced users:**
```bash
git clone <repository-url> && cd rule-migration-agent && pip install -r requirements.txt && python3 migrate.py --help
```

## Usage

### Quick Start with Slash Commands (Recommended)

**The easiest way - fully automated:**

1. **Setup the agent (one command does everything):**
   ```
   /setup
   ```
   This automatically:
   - ✅ Checks for Python 3.8+
   - ✅ Installs Python if missing (macOS/Linux)
   - ✅ Installs all dependencies
   - ✅ Verifies installation
   - ✅ Creates default configuration

2. **Run migration:**
   ```
   /migrate [project-path]
   /migrate [project-path] --both
   /migrate [project-path] --cursor-to-claude --dry-run
   ```

**That's it!** These commands work in both Cursor and Claude Code editors.

### Basic Usage (Command Line)

The agent automatically detects what to convert:

```bash
python3 migrate.py <project-path>
```

**Example:**
```bash
python3 migrate.py ~/projects/my-project
```

### Conversion Directions

**Convert Cursor rules → Claude Skills:**
```bash
python3 migrate.py <project-path> --cursor-to-claude
```

**Convert Claude Skills → Cursor rules:**
```bash
python3 migrate.py <project-path> --claude-to-cursor
```

**Convert both directions (sync):**
```bash
python3 migrate.py <project-path> --both
```

### Common Options

| Option | Description |
|--------|-------------|
| `--force` | Overwrite existing files without confirmation |
| `--dry-run` | Preview changes without making them |
| `--skip-existing` | Skip files that already exist |
| `--show-diffs` | Show diff before overwriting files |
| `--auto-backup` | Create backup before overwriting |
| `--verbose` | Show detailed output and errors |
| `--validate` | Validate output (enabled by default) |
| `--no-validate` | Skip validation |

### Advanced Options

| Option | Description |
|--------|-------------|
| `--batch` | Process multiple projects |
| `--json` | Output results as JSON |
| `--check-sync` | Check sync status without converting |
| `--history` | Show conversion history |
| `--rollback <OP_ID>` | Rollback a specific operation |
| `--config <path>` | Use custom config file |

## Examples

### Using Slash Commands (Recommended)

**Setup the agent:**
```
/setup
```

**Migrate a project:**
```
/migrate ~/projects/my-app
/migrate ~/projects/my-app --both
/migrate ~/projects/my-app --cursor-to-claude --dry-run
```


### Using Command Line

### Example 1: First-Time Migration

Convert Cursor rules to Claude Skills for the first time:

```bash
python3 migrate.py ~/projects/my-app --cursor-to-claude
```

### Example 2: Preview Before Converting

See what would change without making changes:

```bash
python3 migrate.py ~/projects/my-app --both --dry-run
```

### Example 3: Sync Both Directions

Keep both formats synchronized:

```bash
python3 migrate.py ~/projects/my-app --both --auto-backup
```

### Example 4: Batch Process Multiple Projects

```bash
python3 migrate.py ~/projects/* --batch --both
```

### Example 5: Check Sync Status

See if rules and skills are in sync:

```bash
python3 migrate.py ~/projects/my-app --check-sync
```

### Example 6: View Conversion History

```bash
python3 migrate.py ~/projects/my-app --history
```

### Example 7: Rollback Last Conversion

```bash
# First, check history to get operation ID
python3 migrate.py ~/projects/my-app --history

# Then rollback
python3 migrate.py ~/projects/my-app --rollback op-123456
```

## Advanced Features

### State Management

The agent maintains state files in each project:
- `.migration-state.json` - Tracks file hashes and sync status
- `.migration-history.json` - Conversion history
- `.migration-preferences.json` - User preferences

These files are automatically created and can be gitignored (they're project-specific).

### Configuration File

Create `.migration-config.yaml` in your project root for custom settings:

```yaml
preferences:
  auto_backup: true
  show_diffs: false
  skip_unchanged: true
  conflict_resolution: "ask"  # ask, ours, theirs, merge

skip_patterns:
  - "*.test.mdc"
  - "**/deprecated/**"

validation:
  strict: false
  auto_fix: true
```

### Memory System

The agent tracks:
- **State changes** - Only converts files that have changed
- **Conversion history** - Full audit trail of all operations
- **Memory Syncing** - Automatically keeps project context files in sync across platforms
- **Preferences** - Remembers your last used options
- **Global statistics** - Usage metrics across all projects

### Validation

The agent validates:
- ✅ YAML frontmatter syntax
- ✅ Required fields (`name`, `description` for Skills)
- ✅ Name constraints (lowercase, hyphens, no reserved words)
- ✅ Description length limits (<1024 chars for Skills)
- ✅ File structure compliance

## Troubleshooting

### "command not found: python3"

**Solution:** 
- **Easiest:** Run `/setup` - it will install Python automatically (macOS/Linux)
- **Manual:** Try `python` instead of `python3`, or install Python 3.8+

**On macOS:**
```bash
brew install python3
```

**On Linux (Ubuntu/Debian):**
```bash
sudo apt-get update
sudo apt-get install python3 python3-pip
```

**On Windows:**
Download from [python.org](https://www.python.org/downloads/) and make sure to check "Add Python to PATH"

### "No module named 'yaml'"

**Solution:** 
- **Easiest:** Run `/setup` - it will install all dependencies automatically
- **Manual:** Install dependencies:
```bash
pip install -r requirements.txt
```

If using a virtual environment, make sure it's activated:
```bash
source venv/bin/activate  # macOS/Linux
venv\Scripts\activate    # Windows
```

### "Permission denied"

**Solution:** Make the script executable:
```bash
chmod +x migrate.py
```

Or run with Python explicitly:
```bash
python3 migrate.py <project-path>
```

### "No `.cursor/rules` or `.claude/skills` directories found"

**Solution:** This means the project doesn't have rules or skills to convert. Either:
1. Create rules/skills first, or
2. Specify the correct project path

### "Documentation fetch failed"

**Solution:** The agent will use cached documentation. If you're offline, it will still work. If you need fresh docs, check your internet connection.

### Validation Errors

If you see validation errors:

1. **Check the error message** - It will tell you what's wrong
2. **Use `--verbose`** - For detailed error information
3. **Fix manually** - Edit the file and try again
4. **Use `--no-validate`** - Skip validation (not recommended)

### File Conflicts

When files already exist:

1. **Use `--show-diffs`** - See what would change
2. **Use `--auto-backup`** - Backup before overwriting
3. **Use `--force`** - Overwrite without asking
4. **Use `--skip-existing`** - Keep existing files

## Documentation

- **Complete Instructions:** [`instructions.md`](instructions.md) - Full agent documentation
- **Cursor Rules Docs:** https://cursor.com/docs/context/rules
- **Claude Skills Docs:** https://code.claude.com/docs/en/skills
- **Architecture:** [`docs/ARCHITECTURE_ANALYSIS.md`](docs/ARCHITECTURE_ANALYSIS.md)

## Project Structure

```
rule-migration-agent/
├── .claude-plugin/              # Claude Code marketplace (repo root)
│   └── marketplace.json         # Marketplace manifest; source: ./claude-code-plugin
├── claude-code-plugin/          # Claude Code plugin (commands, skills)
│   ├── .claude-plugin/
│   │   └── plugin.json          # Plugin manifest
│   ├── commands/
│   │   ├── migrate.md           # /migrate command
│   │   └── setup.md             # /setup command
│   └── skills/
│       └── rule-migration.md    # Skill for rule/skill files
├── package.json                 # Package metadata
├── pyproject.toml               # PyPI build (build: python -m build)
├── install_agent.py             # Agent setup when cloning from GitHub
├── migrate.py                   # Main entry point
├── converters.py           # Conversion logic
├── parsers.py              # File parsing
├── validation.py           # Format validation
├── utils.py                # Utilities
├── memory.py               # State management
├── config.py               # Configuration
├── requirements.txt        # Dependencies
├── README.md               # This file
├── QUICKSTART.md           # Quick start guide
├── instructions.md             # Agent instructions for Claude
├── .cursor/commands/           # Cursor slash commands
├── .claude/commands/           # Claude editor commands
└── tests/                      # Test suite
```

## Contributing

Contributions are welcome! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

Quick steps:
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request


## Support

- **Issues:** [GitHub Issues](https://github.com/patrikmichi/rule-migration-agent/issues)
- **Discussions:** [GitHub Discussions](https://github.com/patrikmichi/rule-migration-agent/discussions)

---

**Made with ❤️ for the AI coding community**
