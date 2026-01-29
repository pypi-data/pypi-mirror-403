#!/usr/bin/env python3
"""
Rule Migration Agent

Converts between Cursor rules (.cursor/rules) and Claude Skills (.claude/skills).
Always fetches latest documentation before conversion.
Automatically generates AGENTS.md when both folders are present.
"""

import os
import sys
import argparse
import json
import glob
import time
import shutil
from pathlib import Path
from typing import Dict, List

# Import from refactored modules
from converters import convert_cursor_to_claude, convert_claude_to_cursor
from utils import (
    generate_agents_md, print_info, print_success, print_warning, print_error,
    MigrationError
)

# Try to import optional dependencies
try:
    from rich.console import Console
    from rich.table import Table
    console = Console()
    RICH_AVAILABLE = True
except ImportError:
    console = None
    RICH_AVAILABLE = False

# Import memory module
try:
    from memory import MigrationStateManager, ConversionHistory, PreferencesManager, GlobalAgentMemory
    MEMORY_AVAILABLE = True
except ImportError:
    MEMORY_AVAILABLE = False
    # Create dummy memory classes
    class MigrationStateManager:
        def __init__(self, *args, **kwargs): pass
        def has_changed(self, *args, **kwargs): return True
        def update_state(self, *args, **kwargs): pass
        def save(self): pass
    class ConversionHistory:
        def __init__(self, *args, **kwargs): pass
        def log_operation(self, *args, **kwargs): return "op-000"
    class PreferencesManager:
        def __init__(self, *args, **kwargs): pass
        def get_preference(self, *args, **kwargs): return None
        def update_last_options(self, *args, **kwargs): pass
    class GlobalAgentMemory:
        def __init__(self, *args, **kwargs): pass
        def update_statistics(self, *args, **kwargs): pass
        def increment_project_conversion_count(self, *args, **kwargs): pass


def main():
    parser = argparse.ArgumentParser(
        description='Rule Migration Agent - Convert between Cursor rules and Claude Skills',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Convert Cursor rules to Claude Skills
  python migrate.py /path/to/project --cursor-to-claude
  
  # Convert with diff viewing and auto-backup
  python migrate.py /path/to/project --both --show-diffs --auto-backup
  
  # Batch process multiple projects
  python migrate.py projects/* --batch
  
  # Verbose output with validation
  python migrate.py /path/to/project --both --verbose --validate
        """
    )
    parser.add_argument('project_path', type=str, nargs='+', help='Path(s) to project/repo (supports glob patterns)')
    parser.add_argument('--cursor-to-claude', action='store_true', help='Convert Cursor rules to Claude Skills')
    parser.add_argument('--claude-to-cursor', action='store_true', help='Convert Claude Skills to Cursor rules')
    parser.add_argument('--both', action='store_true', help='Convert both directions')
    parser.add_argument('--force', action='store_true', help='Overwrite existing files')
    parser.add_argument('--dry-run', action='store_true', help='Show what would be converted without making changes')
    parser.add_argument('--skip-existing', action='store_true', help='Skip files that already exist')
    parser.add_argument('--show-diffs', action='store_true', help='Show diff before overwriting files')
    parser.add_argument('--auto-backup', action='store_true', help='Create backup before overwriting files')
    parser.add_argument('--validate', action='store_true', default=True, help='Validate rules/skills (default: True)')
    parser.add_argument('--no-validate', dest='validate', action='store_false', help='Skip validation')
    parser.add_argument('--verbose', '-v', action='store_true', help='Verbose output with detailed errors')
    parser.add_argument('--json', action='store_true', help='Output results as JSON')
    parser.add_argument('--batch', action='store_true', help='Process multiple projects (when multiple paths provided)')
    parser.add_argument('--config', type=str, help='Path to custom config file (default: .migration-config.yaml)')
    parser.add_argument('--no-memory', action='store_true', help='Disable context memory system')
    parser.add_argument('--check-sync', action='store_true', help='Check sync status without converting')
    parser.add_argument('--history', action='store_true', help='Show conversion history')
    parser.add_argument('--rollback', type=str, metavar='OP_ID', help='Rollback a specific operation by ID')
    parser.add_argument('--set-preference', type=str, metavar='KEY=VALUE', help='Set a preference (e.g., auto_backup=true)')
    parser.add_argument('--clear-history', action='store_true', help='Clear conversion history')
    
    args = parser.parse_args()
    
    # Handle multiple project paths (batch processing)
    project_paths = []
    for path_pattern in args.project_path:
        # Expand glob patterns
        expanded = glob.glob(path_pattern)
        if expanded:
            project_paths.extend([Path(p).resolve() for p in expanded])
        else:
            # Try as direct path
            path = Path(path_pattern).resolve()
            if path.exists():
                project_paths.append(path)
            else:
                print_error(f"Project path does not exist: {path}")
                if not args.batch:
                    sys.exit(1)
    
    if not project_paths:
        print_error("No valid project paths found")
        sys.exit(1)
    
    # Process projects
    if len(project_paths) > 1 and not args.batch:
        print_warning("Multiple paths provided. Use --batch to process all, or specify single path.")
        sys.exit(1)
    
    # Handle memory-specific commands
    try:
        from memory_commands import check_sync_status, show_history, rollback_operation, set_preference, clear_history
        
        if args.check_sync:
            for project_path in project_paths:
                check_sync_status(project_path, args)
            return
        
        if args.history:
            for project_path in project_paths:
                show_history(project_path, args)
            return
        
        if args.rollback:
            for project_path in project_paths:
                rollback_operation(project_path, args.rollback, args)
            return
        
        if args.set_preference:
            for project_path in project_paths:
                set_preference(project_path, args.set_preference, args)
            return
        
        if args.clear_history:
            for project_path in project_paths:
                clear_history(project_path, args)
            return
    except ImportError:
        if args.check_sync or args.history or args.rollback or args.set_preference or args.clear_history:
            print_error("Memory commands not available. Install required dependencies.")
            sys.exit(1)
    
    # Process each project
    all_results = []
    for project_path in project_paths:
        if not project_path.exists():
            print_error(f"Project path does not exist: {project_path}")
            continue
        
        result = process_project(project_path, args)
        all_results.append(result)
    
    # Summary for batch processing
    if args.batch and len(project_paths) > 1:
        print_batch_summary(all_results, args.json)


def _initialize_memory_managers(project_path: Path, args) -> Tuple:
    """Initialize memory managers and apply preferences."""
    state_manager = None
    history = None
    preferences = None
    global_memory = None
    skip_unchanged = False
    
    if MEMORY_AVAILABLE and not getattr(args, 'no_memory', False):
        state_manager = MigrationStateManager(project_path)
        history = ConversionHistory(project_path)
        preferences = PreferencesManager(project_path)
        global_memory = GlobalAgentMemory()
        
        # Apply preferences if not explicitly set
        if not hasattr(args, 'show_diffs') or args.show_diffs is None:
            args.show_diffs = preferences.get_preference("show_diffs", False)
        if not hasattr(args, 'auto_backup') or args.auto_backup is None:
            args.auto_backup = preferences.get_preference("auto_backup", False)
        skip_unchanged = preferences.get_preference("skip_unchanged", True)
    
    # Load configuration if available
    try:
        from config import MigrationConfig
        config = MigrationConfig(project_path)
        # Override args with config preferences if not explicitly set
        if not hasattr(args, 'show_diffs') or not args.show_diffs:
            args.show_diffs = config.get_preference("show_diffs", False)
        if not hasattr(args, 'auto_backup') or not args.auto_backup:
            args.auto_backup = config.get_preference("auto_backup", False)
        if not skip_unchanged:
            skip_unchanged = config.get_preference("skip_unchanged", True)
    except ImportError:
        pass
    
    return state_manager, history, preferences, global_memory, skip_unchanged


def _determine_conversion_direction(project_path: Path, args) -> Tuple[bool, bool]:
    """Determine which conversion directions to perform."""
    cursor_rules_dir = project_path / '.cursor' / 'rules'
    claude_skills_dir = project_path / '.claude' / 'skills'
    has_cursor = cursor_rules_dir.exists()
    has_claude = claude_skills_dir.exists()
    
    print_info(f"   Cursor rules: {'✅' if has_cursor else '❌'}")
    print_info(f"   Claude skills: {'✅' if has_claude else '❌'}")
    
    if args.both or (not args.cursor_to_claude and not args.claude_to_cursor):
        # Auto-detect: convert both if both exist, otherwise convert what exists
        if has_cursor and has_claude:
            return True, True
        elif has_cursor:
            return True, False
        elif has_claude:
            return False, True
        else:
            print_error("No `.cursor/rules` or `.claude/skills` directories found")
            if args.batch:
                return None, None
            sys.exit(1)
    else:
        return args.cursor_to_claude, args.claude_to_cursor


def process_project(project_path: Path, args) -> Dict:
    """Process a single project."""
    from utils import validate_project_path
    
    start_time = time.time()
    
    # Validate project path for security
    if not validate_project_path(project_path):
        error_msg = f"Invalid or unsafe project path: {project_path}"
        print_error(error_msg)
        return {"project": str(project_path), "error": error_msg}
    
    # Initialize memory managers
    state_manager, history, preferences, global_memory, skip_unchanged = _initialize_memory_managers(project_path, args)
    
    print_info(f"📁 Working with project: {project_path}")
    
    # Determine conversion direction
    convert_cursor, convert_claude = _determine_conversion_direction(project_path, args)
    if convert_cursor is None:
        return {"project": str(project_path), "error": "No rules or skills directories found"}
    
    # Check what exists (needed for command syncing and AGENTS.md generation)
    cursor_rules_dir = project_path / '.cursor' / 'rules'
    claude_skills_dir = project_path / '.claude' / 'skills'
    has_cursor = cursor_rules_dir.exists()
    has_claude = claude_skills_dir.exists()
    
    # Perform conversions
    converted_cursor = []
    converted_claude = []
    all_errors = []
    all_warnings = []
    
    # Initialize variables for conversion results
    errors = []
    warnings = []
    
    if convert_cursor:
        print_info("\n🔄 Converting Cursor rules → Claude Skills...")
        result = convert_cursor_to_claude(
            project_path, 
            args.force, 
            args.dry_run,
            args.show_diffs,
            args.auto_backup,
            args.validate,
            args.verbose,
            state_manager,
            skip_unchanged
        )
        converted_claude = result['converted']
        all_errors.extend(result['errors'])
        all_warnings.extend(result['warnings'])
    
    if convert_claude:
        print_info("\n🔄 Converting Claude Skills → Cursor rules...")
        result = convert_claude_to_cursor(
            project_path, 
            args.force, 
            args.dry_run,
            args.show_diffs,
            args.auto_backup,
            args.validate,
            args.verbose,
            state_manager,
            skip_unchanged
        )
        converted_cursor = result['converted']
        all_errors.extend(result['errors'])
        all_warnings.extend(result['warnings'])
    
    # Sync memory if both folders exist
    if has_cursor and has_claude:
        cursor_memory_dir = project_path / '.cursor' / 'memory'
        claude_memory_dir = project_path / '.claude' / 'memory'
        
        if cursor_memory_dir.exists() and claude_memory_dir.exists():
            print_info("\n🧠 Syncing project memory...")
            # Sync core memory files (brief, decisions)
            for filename in ['brief.md', 'decisions.md']:
                src_cursor = cursor_memory_dir / filename
                src_claude = claude_memory_dir / filename
                
                # Use state manager to check which one is newer/changed
                if state_manager and MEMORY_AVAILABLE:
                    cursor_changed = state_manager.has_changed(src_cursor, "context")
                    claude_changed = state_manager.has_changed(src_claude, "context")
                    
                    if cursor_changed and not claude_changed:
                        if not args.dry_run:
                            shutil.copy2(src_cursor, src_claude)
                            state_manager.update_state(f".cursor/memory/{filename}", src_cursor, "context")
                            state_manager.update_state(f".claude/memory/{filename}", src_claude, "context")
                        print_success(f"Synced: Cursor/{filename} → Claude/{filename}")
                    elif claude_changed and not cursor_changed:
                        if not args.dry_run:
                            shutil.copy2(src_claude, src_cursor)
                            state_manager.update_state(f".cursor/memory/{filename}", src_cursor, "context")
                            state_manager.update_state(f".claude/memory/{filename}", src_claude, "context")
                        print_success(f"Synced: Claude/{filename} → Cursor/{filename}")
        
        # Sync and transform commands (Cursor .md -> Claude Skill folder)
        cursor_commands_dir = project_path / '.cursor' / 'commands'
        if cursor_commands_dir.exists():
            print_info("\n🔄 Migrating commands to Claude skills...")
            for cmd_file in cursor_commands_dir.glob('*.md'):
                if cmd_file.name == 'TEMPLATE.md': continue
                
                skill_name = cmd_file.stem
                # Proper migration using converter logic
                from converters import cursor_rule_to_claude_skill
                # Dummy rule dict for converter
                rule_dict = {
                    'name': skill_name,
                    'frontmatter': {'description': f"Command: {skill_name}"},
                    'body': cmd_file.read_text(encoding='utf-8')
                }
                skill = cursor_rule_to_claude_skill(rule_dict, project_path)
                # Inject user-invocable: true for commands
                skill['content'] = skill['content'].replace('description:', 'user-invocable: true\ndescription:')
                
                if not args.dry_run:
                    skill['directory'].mkdir(parents=True, exist_ok=True)
                    (skill['directory'] / 'SKILL.md').write_text(skill['content'], encoding='utf-8')
                print_success(f"Migrated command: {cmd_file.name} → .claude/skills/{skill_name}/")

        # Support legacy Claude commands migration
        claude_commands_dir = project_path / '.claude' / 'commands'
        if claude_commands_dir.exists():
            legacy_cmds = list(claude_commands_dir.glob('*.md'))
            if legacy_cmds:
                print_info(f"\n🧹 Found {len(legacy_cmds)} legacy Claude commands. Migrating to skills...")
                for cmd_file in legacy_cmds:
                    skill_name = cmd_file.stem
                    from converters import cursor_rule_to_claude_skill
                    rule_dict = {
                        'name': skill_name,
                        'frontmatter': {'description': f"Command: {skill_name}"},
                        'body': cmd_file.read_text(encoding='utf-8')
                    }
                    skill = cursor_rule_to_claude_skill(rule_dict, project_path, is_command=True)
                    
                    if not args.dry_run:
                        skill['directory'].mkdir(parents=True, exist_ok=True)
                        (skill['directory'] / 'SKILL.md').write_text(skill['content'], encoding='utf-8')
                        # Remove legacy file after migration (if not dry run)
                        cmd_file.unlink()
                    print_success(f"Migrated legacy command: {cmd_file.name} → .claude/skills/{skill_name}/")
                
                # Cleanup empty legacy commands dir
                if not args.dry_run and not any(claude_commands_dir.iterdir()):
                    claude_commands_dir.rmdir()
                    print_info("Removed empty legacy .claude/commands/ directory")

        # Generate AGENTS.md if both folders exist
        agents_md_path = project_path / 'AGENTS.md'
        if not agents_md_path.exists() or args.force:
            if args.dry_run:
                print_info(f"\n🔍 [DRY RUN] Would create/update: {agents_md_path}")
            else:
                agents_md_path.write_text(generate_agents_md(project_path), encoding='utf-8')
                print_success(f"\nCreated/updated: {agents_md_path}")
    
    # Log operation to history
    duration_ms = int((time.time() - start_time) * 1000)
    if history and MEMORY_AVAILABLE:
        direction = "both" if (convert_cursor and convert_claude) else ("cursor-to-claude" if convert_cursor else "claude-to-cursor")
        command_str = " ".join(sys.argv)
        history.log_operation(
            direction=direction,
            rules_converted=converted_claude if convert_cursor else [],
            skills_created=converted_cursor if convert_claude else [],
            errors=all_errors,
            warnings=all_warnings,
            duration_ms=duration_ms,
            command=command_str
        )
    
    # Update global statistics
    if global_memory and MEMORY_AVAILABLE:
        total_converted = len(converted_claude) + len(converted_cursor)
        global_memory.update_statistics(
            conversions=1 if total_converted > 0 else 0,
            rules_converted=len(converted_claude),
            skills_converted=len(converted_cursor),
            duration_ms=duration_ms
        )
        global_memory.increment_project_conversion_count(project_path)
    
    # Save state
    if state_manager and MEMORY_AVAILABLE:
        state_manager.save()
    
    # Update preferences with last used options
    if preferences and MEMORY_AVAILABLE:
        preferences.update_last_options({
            "force": args.force,
            "dry_run": args.dry_run,
            "skip_existing": getattr(args, 'skip_existing', False)
        })
    
    # Store result for batch processing
    result = {
        "project": str(project_path),
        "converted_to_claude": len(converted_claude),
        "converted_to_cursor": len(converted_cursor),
        "errors": len(all_errors),
        "warnings": len(all_warnings),
        "duration_ms": duration_ms
    }
    
    # Summary
    if args.json:
        summary = {
            "converted_to_claude": len(converted_claude),
            "converted_to_cursor": len(converted_cursor),
            "errors": len(all_errors),
            "warnings": len(all_warnings),
            "converted_claude": converted_claude,
            "converted_cursor": converted_cursor,
            "error_messages": all_errors,
            "warning_messages": all_warnings
        }
        print(json.dumps(summary, indent=2))
    else:
        if console:
            table = Table(title="Migration Summary", show_header=True, header_style="bold magenta")
            table.add_column("Metric", style="cyan")
            table.add_column("Count", style="green")
            
            if converted_claude:
                table.add_row("Converted to Claude Skills", str(len(converted_claude)))
            if converted_cursor:
                table.add_row("Converted to Cursor rules", str(len(converted_cursor)))
            if all_errors:
                table.add_row("Errors", str(len(all_errors)), style="red")
            if all_warnings:
                table.add_row("Warnings", str(len(all_warnings)), style="yellow")
            
            if not converted_claude and not converted_cursor:
                table.add_row("Status", "No conversions performed", style="yellow")
            
            console.print("\n")
            console.print(table)
            
            if all_errors and args.verbose:
                print_error("\nErrors:")
                for error in all_errors:
                    print_error(f"  {error}")
            
            if all_warnings and args.verbose:
                print_warning("\nWarnings:")
                for warning in all_warnings:
                    print_warning(f"  {warning}")
        else:
            print_info("\n📊 Summary:")
            if converted_claude:
                print_info(f"   Converted to Claude Skills: {len(converted_claude)}")
            if converted_cursor:
                print_info(f"   Converted to Cursor rules: {len(converted_cursor)}")
            if all_errors:
                print_error(f"   Errors: {len(all_errors)}")
            if all_warnings:
                print_warning(f"   Warnings: {len(all_warnings)}")
            if not converted_claude and not converted_cursor:
                print_warning("   No conversions performed")
            
            if all_errors and args.verbose:
                print_error("\nErrors:")
                for error in all_errors:
                    print_error(f"  {error}")
            
            if all_warnings and args.verbose:
                print_warning("\nWarnings:")
                for warning in all_warnings:
                    print_warning(f"  {warning}")
    
    return result


def print_batch_summary(results: List[Dict], json_output: bool = False):
    """Print summary for batch processing."""
    if json_output:
        print(json.dumps(results, indent=2))
    else:
        if console:
            table = Table(title="Batch Migration Summary", show_header=True, header_style="bold magenta")
            table.add_column("Project", style="cyan")
            table.add_column("Claude", style="green")
            table.add_column("Cursor", style="green")
            table.add_column("Errors", style="red")
            table.add_column("Warnings", style="yellow")
            
            for result in results:
                table.add_row(
                    Path(result["project"]).name,
                    str(result.get("converted_to_claude", 0)),
                    str(result.get("converted_to_cursor", 0)),
                    str(result.get("errors", 0)),
                    str(result.get("warnings", 0))
                )
            
            console.print("\n")
            console.print(table)
        else:
            print("\n📊 Batch Summary:")
            print(f"{'Project':<40} {'Claude':<10} {'Cursor':<10} {'Errors':<10} {'Warnings':<10}")
            print("-" * 80)
            for result in results:
                print(f"{Path(result['project']).name:<40} "
                      f"{result.get('converted_to_claude', 0):<10} "
                      f"{result.get('converted_to_cursor', 0):<10} "
                      f"{result.get('errors', 0):<10} "
                      f"{result.get('warnings', 0):<10}")


if __name__ == '__main__':
    main()
