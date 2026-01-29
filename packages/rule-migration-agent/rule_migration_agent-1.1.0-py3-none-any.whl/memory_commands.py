#!/usr/bin/env python3
"""
Memory-specific command handlers for rule-migration-agent
"""

from pathlib import Path
from typing import Optional
from datetime import datetime, timezone
import json

try:
    from memory import MigrationStateManager, ConversionHistory, PreferencesManager
    MEMORY_AVAILABLE = True
except ImportError:
    MEMORY_AVAILABLE = False

try:
    from rich.console import Console
    from rich.table import Table
    from rich.panel import Panel
    console = Console()
    RICH_AVAILABLE = True
except ImportError:
    console = None
    RICH_AVAILABLE = False

from utils import print_info, print_success, print_warning, print_error


def check_sync_status(project_path: Path, args):
    """Check sync status between Cursor rules and Claude Skills."""
    if not MEMORY_AVAILABLE:
        print_error("Memory system not available. Install required dependencies.")
        return
    
    state_manager = MigrationStateManager(project_path)
    sync_status = state_manager.get_sync_status()
    
    # Count rules and skills
    rules_dir = project_path / '.cursor' / 'rules'
    skills_dir = project_path / '.claude' / 'skills'
    
    rules_count = 0
    skills_count = 0
    changed_rules = []
    missing_in_claude = []
    missing_in_cursor = []
    
    if rules_dir.exists():
        for rule_dir in rules_dir.iterdir():
            if rule_dir.is_dir():
                rule_file = rule_dir / 'RULE.md'
                if rule_file.exists():
                    rules_count += 1
                    if state_manager.has_changed(rule_file, "cursor"):
                        changed_rules.append(rule_dir.name)
                    # Check if corresponding skill exists
                    skill_dir = skills_dir / rule_dir.name
                    if not (skill_dir / 'SKILL.md').exists():
                        missing_in_claude.append(rule_dir.name)
    
    if skills_dir.exists():
        for skill_dir in skills_dir.iterdir():
            if skill_dir.is_dir():
                skill_file = skill_dir / 'SKILL.md'
                if skill_file.exists():
                    skills_count += 1
                    # Check if corresponding rule exists
                    rule_dir = rules_dir / skill_dir.name
                    if not (rule_dir / 'RULE.md').exists():
                        missing_in_cursor.append(skill_dir.name)
    
    in_sync = len(changed_rules) == 0 and len(missing_in_claude) == 0 and len(missing_in_cursor) == 0
    
    if args.json:
        result = {
            "in_sync": in_sync,
            "rules_count": rules_count,
            "skills_count": skills_count,
            "changed_rules": changed_rules,
            "missing_in_claude": missing_in_claude,
            "missing_in_cursor": missing_in_cursor
        }
        print(json.dumps(result, indent=2))
    else:
        if console:
            table = Table(title="Sync Status", show_header=True, header_style="bold magenta")
            table.add_column("Metric", style="cyan")
            table.add_column("Value", style="green")
            
            table.add_row("Status", "[green]✅ In Sync[/green]" if in_sync else "[yellow]⚠️  Out of Sync[/yellow]")
            table.add_row("Cursor Rules", str(rules_count))
            table.add_row("Claude Skills", str(skills_count))
            table.add_row("Changed Rules", str(len(changed_rules)), style="yellow" if changed_rules else "green")
            table.add_row("Missing in Claude", str(len(missing_in_claude)), style="red" if missing_in_claude else "green")
            table.add_row("Missing in Cursor", str(len(missing_in_cursor)), style="red" if missing_in_cursor else "green")
            
            console.print("\n")
            console.print(table)
            
            if changed_rules:
                print_warning(f"\nChanged rules: {', '.join(changed_rules)}")
            if missing_in_claude:
                print_error(f"\nMissing in Claude: {', '.join(missing_in_claude)}")
            if missing_in_cursor:
                print_error(f"\nMissing in Cursor: {', '.join(missing_in_cursor)}")
        else:
            print_info(f"\n📊 Sync Status:")
            print_info(f"   Status: {'✅ In Sync' if in_sync else '⚠️  Out of Sync'}")
            print_info(f"   Cursor Rules: {rules_count}")
            print_info(f"   Claude Skills: {skills_count}")
            print_info(f"   Changed Rules: {len(changed_rules)}")
            print_info(f"   Missing in Claude: {len(missing_in_claude)}")
            print_info(f"   Missing in Cursor: {len(missing_in_cursor)}")
            
            if changed_rules:
                print_warning(f"\n   Changed rules: {', '.join(changed_rules)}")
            if missing_in_claude:
                print_error(f"\n   Missing in Claude: {', '.join(missing_in_claude)}")
            if missing_in_cursor:
                print_error(f"\n   Missing in Cursor: {', '.join(missing_in_cursor)}")


def show_history(project_path: Path, args):
    """Show conversion history."""
    if not MEMORY_AVAILABLE:
        print_error("Memory system not available. Install required dependencies.")
        return
    
    history = ConversionHistory(project_path)
    limit = 10 if not hasattr(args, 'limit') else args.limit
    operations = history.get_recent_operations(limit)
    
    if args.json:
        print(json.dumps(operations, indent=2, default=str))
    else:
        if console:
            if not operations:
                print_warning("No conversion history found.")
                return
            
            table = Table(title="Conversion History", show_header=True, header_style="bold magenta")
            table.add_column("ID", style="cyan")
            table.add_column("Timestamp", style="green")
            table.add_column("Direction", style="yellow")
            table.add_column("Converted", style="green")
            table.add_column("Errors", style="red")
            table.add_column("Duration", style="blue")
            
            for op in operations:
                converted_count = len(op.get("rules_converted", [])) + len(op.get("skills_created", []))
                errors_count = len(op.get("errors", []))
                duration = f"{op.get('duration_ms', 0)}ms"
                
                table.add_row(
                    op.get("id", "N/A"),
                    op.get("timestamp", "N/A")[:19],  # Truncate to date+time
                    op.get("direction", "N/A"),
                    str(converted_count),
                    str(errors_count),
                    duration
                )
            
            console.print("\n")
            console.print(table)
        else:
            if not operations:
                print("No conversion history found.")
                return
            
            print(f"\n📜 Conversion History (last {len(operations)} operations):")
            print(f"{'ID':<10} {'Timestamp':<20} {'Direction':<20} {'Converted':<10} {'Errors':<10} {'Duration':<10}")
            print("-" * 90)
            for op in operations:
                converted_count = len(op.get("rules_converted", [])) + len(op.get("skills_created", []))
                errors_count = len(op.get("errors", []))
                print(f"{op.get('id', 'N/A'):<10} "
                      f"{op.get('timestamp', 'N/A')[:19]:<20} "
                      f"{op.get('direction', 'N/A'):<20} "
                      f"{converted_count:<10} "
                      f"{errors_count:<10} "
                      f"{op.get('duration_ms', 0)}ms")


def rollback_operation(project_path: Path, operation_id: str, args):
    """Rollback a specific operation."""
    if not MEMORY_AVAILABLE:
        print_error("Memory system not available. Install required dependencies.")
        return
    
    import shutil
    from pathlib import Path
    
    history = ConversionHistory(project_path)
    operation = history.get_operation(operation_id)
    
    if not operation:
        print_error(f"Operation {operation_id} not found")
        return
    
    direction = operation.get("direction", "")
    rules_converted = operation.get("rules_converted", [])
    skills_created = operation.get("skills_created", [])
    
    print_warning(f"⚠️  Rolling back operation {operation_id}...")
    print_info(f"Direction: {direction}")
    print_info(f"Rules converted: {len(rules_converted)}")
    print_info(f"Skills created: {len(skills_created)}")
    
    # Confirm rollback
    if not getattr(args, 'force', False):
        if console:
            response = console.input("[yellow]Are you sure you want to rollback? (yes/no): [/yellow]")
        else:
            response = input("Are you sure you want to rollback? (yes/no): ")
        if response.lower() not in ['yes', 'y']:
            print_warning("Rollback cancelled")
            return
    
    rolled_back = []
    errors = []
    
    # Rollback based on direction
    # Note: In operation history:
    # - "rules_converted" = Cursor rules converted to Claude Skills (skill names created)
    # - "skills_created" = Claude Skills converted to Cursor rules (rule names created)
    
    if direction in ["cursor-to-claude", "both"]:
        # Delete skills that were created from Cursor rules
        skills_dir = project_path / '.claude' / 'skills'
        for skill_name in rules_converted:  # Fixed: use rules_converted, not skills_created
            skill_path = skills_dir / skill_name
            if skill_path.exists():
                try:
                    # Check for backup first
                    skill_file = skill_path / 'SKILL.md'
                    if skill_file.exists():
                        backups = list(skill_file.parent.glob(f"SKILL.md.backup.*"))
                        if backups:
                            # Restore from most recent backup
                            latest_backup = max(backups, key=lambda p: p.stat().st_mtime)
                            print_info(f"Restoring from backup: {latest_backup.name}")
                            shutil.copy2(str(latest_backup), str(skill_file))
                            rolled_back.append(f"Restored skill: {skill_name}")
                        else:
                            # Delete the skill directory
                            shutil.rmtree(skill_path)
                            rolled_back.append(f"Deleted skill: {skill_name}")
                except Exception as e:
                    error_msg = f"Failed to rollback skill {skill_name}: {e}"
                    errors.append(error_msg)
                    print_error(error_msg)
    
    if direction in ["claude-to-cursor", "both"]:
        # Delete rules that were created from Claude Skills
        rules_dir = project_path / '.cursor' / 'rules'
        for rule_name in skills_created:  # Fixed: skills_created contains rule names when converting claude-to-cursor
            rule_path = rules_dir / rule_name
            if rule_path.exists():
                try:
                    # Check for backup first
                    rule_file = rule_path / 'RULE.md'
                    if rule_file.exists():
                        backups = list(rule_file.parent.glob(f"RULE.md.backup.*"))
                        if backups:
                            # Restore from most recent backup
                            latest_backup = max(backups, key=lambda p: p.stat().st_mtime)
                            print_info(f"Restoring from backup: {latest_backup.name}")
                            shutil.copy2(str(latest_backup), str(rule_file))
                            rolled_back.append(f"Restored rule: {rule_name}")
                        else:
                            # Delete the rule directory
                            shutil.rmtree(rule_path)
                            rolled_back.append(f"Deleted rule: {rule_name}")
                except Exception as e:
                    error_msg = f"Failed to rollback rule {rule_name}: {e}"
                    errors.append(error_msg)
                    print_error(error_msg)
    
    # Report results
    if rolled_back:
        print_success(f"Rolled back {len(rolled_back)} items")
    if errors:
        print_error(f"{len(errors)} errors during rollback")
        for error in errors:
            print_error(f"  {error}")
    
    # Mark operation as rolled back in history
    operation["rolled_back"] = True
    operation["rollback_timestamp"] = datetime.now(timezone.utc).isoformat()
    history._save_history()


def set_preference(project_path: Path, preference_str: str, args):
    """Set a preference."""
    if not MEMORY_AVAILABLE:
        print_error("Memory system not available. Install required dependencies.")
        return
    
    try:
        key, value = preference_str.split('=', 1)
        # Convert string boolean/number to proper type
        if value.lower() == 'true':
            value = True
        elif value.lower() == 'false':
            value = False
        elif value.isdigit():
            value = int(value)
        elif value.replace('.', '', 1).isdigit():
            value = float(value)
        
        preferences = PreferencesManager(project_path)
        preferences.set_preference(key, value)
        
        print_success(f"Set preference: {key} = {value}")
    except ValueError:
        print_error("Invalid preference format. Use KEY=VALUE")


def clear_history(project_path: Path, args):
    """Clear conversion history."""
    if not MEMORY_AVAILABLE:
        print_error("Memory system not available. Install required dependencies.")
        return
    
    history_file = project_path / '.migration-history.json'
    if history_file.exists():
        history_file.unlink()
        print_success("Cleared conversion history")
    else:
        print_warning("No history file found")
