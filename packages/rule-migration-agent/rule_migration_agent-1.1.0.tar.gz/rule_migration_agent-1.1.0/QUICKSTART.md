# Quick Start Guide

Get up and running with the Rule Migration Agent in 5 minutes!

## Automated Setup (Recommended)

**Just run the setup command - it handles everything:**

```
/setup
```

This automatically:
- ✅ Checks for Python 3.8+
- ✅ Installs Python if missing (macOS/Linux)
- ✅ Installs all dependencies
- ✅ Verifies installation
- ✅ Creates configuration

## Manual Setup (Alternative)

If you prefer manual setup:

```bash
# 1. Check Python (should be 3.8+)
python3 --version

# 2. Navigate to the agent directory
cd rule-migration-agent

# 3. Install dependencies
pip install -r requirements.txt

# 4. Verify installation
python3 migrate.py --help
```

## Your First Conversion

### Using Slash Commands (Easiest)

**Setup first:**
```
/setup
```

**Then migrate:**
```
/migrate /path/to/your/project
/migrate /path/to/your/project --both
/migrate /path/to/your/project --cursor-to-claude
```

### Using Command Line

```bash
# Convert Cursor rules to Claude Skills
python3 migrate.py /path/to/your/project --cursor-to-claude

# Or convert Claude Skills to Cursor rules
python3 migrate.py /path/to/your/project --claude-to-cursor

# Or sync both directions
python3 migrate.py /path/to/your/project --both
```

## Common Commands

### Slash Commands (Recommended)

| What you want to do | Command |
|---------------------|---------|
| Setup the agent | `/setup` |
| Migrate project | `/migrate <project>` |
| Preview changes | `/migrate <project> --dry-run` |
| Sync both directions | `/migrate <project> --both` |
| Check sync status | `/migrate <project> --check-sync` |

### Command Line

| What you want to do | Command |
|---------------------|---------|
| Preview changes | `python3 migrate.py <project> --dry-run` |
| Force overwrite | `python3 migrate.py <project> --both --force` |
| Safe conversion with backup | `python3 migrate.py <project> --both --auto-backup` |
| Check sync status | `python3 migrate.py <project> --check-sync` |

## Next Steps

- Read the full [README.md](README.md) for detailed documentation
- Check [instructions.md](instructions.md) for complete agent documentation
- See [CHANGELOG.md](CHANGELOG.md) for recent updates

## Need Help?

- Check the [Troubleshooting](#troubleshooting) section in README.md
- Review error messages with `--verbose` flag
- Use `--dry-run` to preview changes safely

## New in v1.1.0

- 🧠 **Persistent Memory**: Shared context across platforms via `brief.md` and `decisions.md`.
- 🔄 **Unified Commands**: All slash commands are now skill-based for better performance.
- 🧹 **Legacy Support**: Automatic modernization of old Claude commands.

---

**That's it! You're ready to migrate rules and skills.** 🚀
