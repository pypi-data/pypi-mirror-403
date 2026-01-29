# Architecture Analysis: Claude-Cursor Parity

This document analyzes the current state of the Python scripts and project configuration after the manual sync of rules, skills, and memory.

## Python Scripts Analysis

### 1. `migrate.py`
- **Command Syncing**: Lines 317-331 still sync to `.claude/commands/`. This directory is deprecated in the January 2026 Claude docs in favor of `skills/`.
- **Memory Parity**: The script does not automatically sync the context memory files (`.cursor/memory/` and `.claude/memory/`), which violates Rule 4 of the memory management instructions.
- **Automation**: There is no logic yet to detect if a Claude skill is actually a command (`user-invocable: true`) and sync it back to Cursor as a slash command.

### 2. `memory.py`
- **Storage Location**: Internal migration state files (`.migration-state.json`, etc.) are in the project root. Moving these into `.cursor/memory/internal/` and `.claude/memory/internal/` would align better with the memory architecture and reduce root clutter.
- **Tracking Scope**: `MigrationStateManager` only tracks `RULE.md` and `SKILL.md` files. It should be expanded to track the context memory files (`brief.md`, `decisions.md`) to ensure they stay in sync.

### 3. `converters.py`
- **Command Handling**: The converters are strictly focused on rules/skills. They should be aware of the "command-as-skill" pattern for Claude and be able to map between `.cursor/commands/name.md` and `.claude/skills/name/SKILL.md` (with `user-invocable: true`).

### 4. `memory_commands.py`
- **Sync Checking**: `check_sync_status` currently ignores the context memory files. A project should not be considered "in sync" if `decisions.md` differs between platforms.

---

## Gitignore Analysis

Currently, the agent ignores root-level JSON files. With the addition of `.cursor/memory` and `.claude/memory`, we need a more granular approach:

### What to Commit
- `.cursor/memory/brief.md` & `.claude/memory/brief.md` (Project Context)
- `.cursor/memory/decisions.md` & `.claude/memory/decisions.md` (Architectural Log)

### What to Ignore
- `.cursor/memory/summaries/` & `.claude/memory/summaries/` (Transient session summaries)
- `.migration-state.json` (Local state)
- `.migration-history.json` (Local operation history)
- `.migration-preferences.json` (Local user preferences)

---

## Recommendations

1. **Refactor `migrate.py`** to use the `skills/` structure exclusively for Claude commands.
2. **Update `MigrationStateManager`** to track the context memory files.
3. **Update `.gitignore`** to include the `summaries/` subdirectories within memory.
4. **Extend `check_sync_status`** to include memory files in the parity check.
