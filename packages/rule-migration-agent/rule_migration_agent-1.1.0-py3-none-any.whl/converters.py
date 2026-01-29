#!/usr/bin/env python3
"""
Conversion logic for rule-migration-agent

Handles conversion between Cursor rules and Claude Skills.
"""

import re
import yaml
from pathlib import Path
from typing import Dict, List, Tuple, Optional
from utils import ConversionResult

from parsers import parse_cursor_rule, parse_claude_skill
from utils import (
    normalize_skill_name, show_diff, create_backup,
    print_info, print_success, print_warning, print_error, print_dim,
    ParseError, ConversionError
)

try:
    from rich.console import Console
    from rich.syntax import Syntax
    console = Console()
    RICH_AVAILABLE = True
except ImportError:
    console = None
    RICH_AVAILABLE = False
    Syntax = None

try:
    from validation import validate_cursor_rule, validate_claude_skill, ValidationResult
    VALIDATION_AVAILABLE = True
except ImportError:
    VALIDATION_AVAILABLE = False
    def validate_cursor_rule(*args, **kwargs):
        result = type('obj', (object,), {'valid': True, 'issues': [], 'warnings': []})()
        return result
    def validate_claude_skill(*args, **kwargs):
        result = type('obj', (object,), {'valid': True, 'issues': [], 'warnings': []})()
        return result

try:
    from memory import MigrationStateManager, DocumentationCache
    MEMORY_AVAILABLE = True
except ImportError:
    MEMORY_AVAILABLE = False
    class MigrationStateManager:
        def __init__(self, *args, **kwargs): pass
        def has_changed(self, *args, **kwargs): return True
        def update_state(self, *args, **kwargs): pass
        def save(self): pass
    class DocumentationCache:
        def __init__(self, *args, **kwargs): pass
        def get_cached_doc(self, *args, **kwargs): return None
        def cache_doc(self, *args, **kwargs): pass

try:
    from tqdm import tqdm
    TQDM_AVAILABLE = True
except ImportError:
    TQDM_AVAILABLE = False

# Documentation URLs
CURSOR_RULES_URL = "https://cursor.com/docs/context/rules"
CLAUDE_SKILLS_URL = "https://code.claude.com/docs/en/skills"


def _find_cursor_rule_files(rules_dir: Path) -> List[Path]:
    """Find all Cursor rule files, prioritizing folder-based format."""
    rule_files = []
    rule_names_processed = set()
    
    # First, check for rule folders with RULE.md (preferred format)
    for rule_dir in rules_dir.iterdir():
        if rule_dir.is_dir() and not rule_dir.name.startswith('.'):
            rule_file = rule_dir / 'RULE.md'
            if rule_file.exists():
                rule_files.append(rule_file)
                rule_names_processed.add(rule_dir.name)
    
    # Then, add .mdc files that don't have a corresponding folder
    for mdc_file in rules_dir.glob('*.mdc'):
        rule_name = mdc_file.stem
        if rule_name not in rule_names_processed:
            rule_files.append(mdc_file)
    
    # Also handle INDEX.md files (documentation/index files)
    index_file = rules_dir / 'INDEX.md'
    if index_file.exists() and 'index' not in rule_names_processed:
        rule_files.append(index_file)
    
    return rule_files


def _process_single_cursor_rule(rule_file: Path, project_path: Path, force: bool, 
                                dry_run: bool, show_diffs: bool, auto_backup: bool,
                                validate: bool, verbose: bool, state_manager: Optional[MigrationStateManager],
                                skip_unchanged: bool) -> Tuple[Optional[str], List[str], List[str]]:
    """Process a single Cursor rule file and convert it to Claude Skill."""
    errors = []
    warnings = []
    
    # Determine if this is a command (from .cursor/commands/)
    is_command = ".cursor/commands" in str(rule_file)
    
    # Check if file has changed (skip unchanged if enabled)
    if skip_unchanged and state_manager and MEMORY_AVAILABLE:
        track_type = "cursor_command" if is_command else "cursor"
        if not state_manager.has_changed(rule_file, track_type):
            if verbose:
                print_dim(f"⏭️  Skipping {rule_file.name} (unchanged)")
            return None, [], []
    
    # Validate source rule if validation is enabled
    # Commands don't need the same validation as rules
    if not is_command and validate and VALIDATION_AVAILABLE:
        validation_result = validate_cursor_rule(rule_file)
        if not validation_result.valid:
            error_msg = f"Validation failed for {rule_file.name}: {validation_result.issues[0]['message']}"
            errors.append(error_msg)
            if verbose:
                for issue in validation_result.issues:
                    print_error(f"  {issue['message']}")
            return None, errors, []
        elif validation_result.warnings:
            for warning in validation_result.warnings:
                warnings.append(f"{rule_file.name}: {warning['message']}")
    
    # Parse rule
    try:
        rule = parse_cursor_rule(rule_file)
        if not rule:
            raise ParseError(f"Failed to parse {rule_file}")
    except Exception as e:
        error_msg = f"Failed to parse {rule_file}: {e}"
        errors.append(error_msg)
        if verbose:
            print_error(error_msg)
        return None, errors, []
    
    # Convert to Claude Skill
    skill = cursor_rule_to_claude_skill(rule, project_path, is_command=is_command)
    skill_dir = skill['directory']
    skill_file = skill_dir / 'SKILL.md'
    
    # Validate target skill if validation is enabled
    if validate and VALIDATION_AVAILABLE:
        validation_result = validate_claude_skill(skill_dir, skill['content'])
        if not validation_result.valid:
            error_msg = f"Target validation failed for {skill['name']}: {validation_result.issues[0]['message']}"
            errors.append(error_msg)
            if verbose:
                for issue in validation_result.issues:
                    print_error(f"  {issue['message']}")
            return None, errors, warnings
    
    # Handle existing files
    if skill_file.exists():
        if not force:
            print_warning(f"⏭️  Skipping {skill['name']} (already exists, use --force to overwrite)")
            return None, [], []
        
        # Show diff if requested
        if show_diffs:
            existing_content = skill_file.read_text(encoding='utf-8')
            show_diff(existing_content, skill['content'], skill_file)
        
        # Create backup if requested
        if auto_backup:
            create_backup(skill_file)
    
    # Write file
    if dry_run:
        print_info(f"🔍 [DRY RUN] Would create: {skill_file}")
        return skill['name'], [], warnings
    else:
        skill_dir.mkdir(parents=True, exist_ok=True)
        skill_file.write_text(skill['content'], encoding='utf-8')
        print_success(f"Converted: {rule['name']} → {skill['name']}")
        
        # Update state if memory is available
        if state_manager and MEMORY_AVAILABLE:
            state_manager.update_state(rule['name'], rule_file, "cursor", "claude")
        
        return skill['name'], [], warnings


def cursor_rule_to_claude_skill(rule: Dict, project_path: Path, is_command: bool = False) -> Dict:
    """Convert a Cursor rule to Claude Skill format."""
    # Normalize skill name
    skill_name = normalize_skill_name(rule['name'])
    
    # Build frontmatter
    frontmatter = {
        'name': skill_name,
        'description': rule['frontmatter'].get('description', '')
    }
    
    # Add globs info to description if present
    globs = rule['frontmatter'].get('globs', [])
    if globs:
        globs_str = ', '.join(f'`{g}`' for g in globs)
        frontmatter['description'] += f" Use when editing files matching {globs_str}."
    
    # Handle alwaysApply
    if rule['frontmatter'].get('alwaysApply', False):
        frontmatter['description'] = "Always active. " + frontmatter['description']
    
    # Ensure description is not too long
    from utils import MAX_DESCRIPTION_LENGTH
    if len(frontmatter['description']) > MAX_DESCRIPTION_LENGTH:
        frontmatter['description'] = frontmatter['description'][:MAX_DESCRIPTION_LENGTH-3] + "..."
    
    # Build SKILL.md content with proper YAML escaping
    # Escape quotes in description for YAML
    description_escaped = frontmatter['description'].replace('"', '\\"')
    invocable_yaml = 'user-invocable: true\n' if is_command else ''
    
    skill_content = f"""---
name: {frontmatter['name']}
{invocable_yaml}description: "{description_escaped}"
---

{rule['body']}
"""
    
    return {
        'name': skill_name,
        'content': skill_content,
        'directory': project_path / '.claude' / 'skills' / skill_name
    }


def claude_skill_to_cursor_rule(skill: Dict, project_path: Path) -> Dict:
    """Convert a Claude Skill to Cursor rule or command format."""
    # Use skill name as rule name
    rule_name = skill['name']
    is_command = skill['frontmatter'].get('user-invocable', False)
    
    # Build frontmatter
    frontmatter = {
        'description': skill['frontmatter'].get('description', '')
    }
    
    # Try to extract globs from description
    description = frontmatter['description']
    glob_pattern = r'`([^`]+)`'
    globs = re.findall(glob_pattern, description)
    if globs:
        frontmatter['globs'] = globs
        # Remove glob mentions from description
        for glob in globs:
            description = description.replace(f'`{glob}`', '').replace('Use when editing files matching', '').strip()
        frontmatter['description'] = description.strip(' .,')
    
    # Check if always active
    always_apply = 'always active' in description.lower() or 'always apply' in description.lower()
    frontmatter['alwaysApply'] = always_apply
    
    # Build content
    if is_command:
        # Commands are just .md files in .cursor/commands/ without frontmatter (usually)
        # or with simple description
        content = f"# {rule_name}\n\n{skill['body']}"
        target_path = project_path / '.cursor' / 'commands' / f"{rule_name}.md"
    else:
        # Rules use folder-based format with RULE.md
        globs_yaml = ''
        if globs:
            globs_yaml = yaml.dump({'globs': frontmatter['globs']}, default_flow_style=False).strip()
            globs_yaml = f"{globs_yaml}\n" if globs_yaml else ''
        
        always_apply_yaml = f"alwaysApply: {str(always_apply).lower()}\n" if always_apply else ''
        
        content = f"""---
description: "{frontmatter['description']}"
{globs_yaml}{always_apply_yaml}---

{skill['body']}
"""
        target_path = project_path / '.cursor' / 'rules' / rule_name / 'RULE.md'
    
    return {
        'name': rule_name,
        'content': content,
        'path': target_path,
        'is_command': is_command
    }


def convert_cursor_to_claude(project_path: Path, force: bool = False, dry_run: bool = False, 
                             show_diffs: bool = False, auto_backup: bool = False, 
                             validate: bool = True, verbose: bool = False,
                             state_manager: Optional[MigrationStateManager] = None,
                             skip_unchanged: bool = True) -> ConversionResult:
    """Convert Cursor rules to Claude Skills with enhanced features."""
    from utils import fetch_documentation
    
    rules_dir = project_path / '.cursor' / 'rules'
    commands_dir = project_path / '.cursor' / 'commands'
    
    if not rules_dir.exists() and not commands_dir.exists():
        print_warning(f"No `.cursor/rules` or `.cursor/commands` directory found in {project_path}")
        return ConversionResult(converted=[], errors=[], warnings=[])
    
    # Initialize documentation cache
    doc_cache = DocumentationCache() if MEMORY_AVAILABLE else None
    
    # Fetch latest Claude Skills documentation
    fetch_documentation(CLAUDE_SKILLS_URL, 'claude_skills', doc_cache=doc_cache)
    
    # Find all rule and command files
    rule_files = []
    if rules_dir.exists():
        rule_files.extend(_find_cursor_rule_files(rules_dir))
    if commands_dir.exists():
        rule_files.extend([f for f in commands_dir.glob('*.md') if f.name != 'TEMPLATE.md'])
    
    if not rule_files:
        print_warning(f"No rule files found in {rules_dir}")
        return ConversionResult(converted=[], errors=[], warnings=[])
    
    converted = []
    errors = []
    warnings = []
    skills_dir = project_path / '.claude' / 'skills'
    skills_dir.mkdir(parents=True, exist_ok=True)
    
    # Use progress bar if available
    iterator = tqdm(rule_files, desc="Converting rules", unit="rule") if TQDM_AVAILABLE else rule_files
    
    for rule_file in iterator:
        try:
            skill_name, file_errors, file_warnings = _process_single_cursor_rule(
                rule_file, project_path, force, dry_run, show_diffs, auto_backup,
                validate, verbose, state_manager, skip_unchanged
            )
            if skill_name:
                converted.append(skill_name)
            errors.extend(file_errors)
            warnings.extend(file_warnings)
        except Exception as e:
            error_msg = f"Error converting {rule_file}: {e}"
            errors.append(error_msg)
            if verbose:
                import traceback
                print_error(error_msg)
                if console and Syntax:
                    console.print(Syntax(traceback.format_exc(), "python", theme="monokai"))
                else:
                    traceback.print_exc()
    
    return ConversionResult(converted=converted, errors=errors, warnings=warnings)


def _process_single_claude_skill(skill_dir: Path, project_path: Path, force: bool,
                                 dry_run: bool, show_diffs: bool, auto_backup: bool,
                                 validate: bool, verbose: bool, state_manager: Optional[MigrationStateManager],
                                 skip_unchanged: bool) -> Tuple[Optional[str], List[str], List[str]]:
    """Process a single Claude Skill and convert it to Cursor rule."""
    errors = []
    warnings = []
    skill_file = skill_dir / 'SKILL.md'
    
    # Check if file has changed (skip unchanged if enabled)
    if skip_unchanged and state_manager and MEMORY_AVAILABLE:
        if not state_manager.has_changed(skill_file, "claude"):
            if verbose:
                print_dim(f"⏭️  Skipping {skill_dir.name} (unchanged)")
            return None, [], []
    
    # Validate source skill if validation is enabled
    if validate and VALIDATION_AVAILABLE:
        validation_result = validate_claude_skill(skill_dir)
        if not validation_result.valid:
            error_msg = f"Validation failed for {skill_dir.name}: {validation_result.issues[0]['message']}"
            errors.append(error_msg)
            if verbose:
                for issue in validation_result.issues:
                    print_error(f"  {issue['message']}")
            return None, errors, []
        elif validation_result.warnings:
            for warning in validation_result.warnings:
                warnings.append(f"{skill_dir.name}: {warning['message']}")
    
    # Parse skill
    try:
        skill = parse_claude_skill(skill_dir)
        if not skill:
            raise ParseError(f"Failed to parse {skill_dir}")
    except Exception as e:
        error_msg = f"Failed to parse {skill_dir}: {e}"
        errors.append(error_msg)
        if verbose:
            print_error(error_msg)
        return None, errors, []
    
    # Convert to Cursor rule
    rule = claude_skill_to_cursor_rule(skill, project_path)
    rule_file = rule['path']
    
    # Validate target rule if validation is enabled
    if validate and VALIDATION_AVAILABLE:
        validation_result = validate_cursor_rule(rule_file.parent, rule['content'])
        if not validation_result.valid:
            error_msg = f"Target validation failed for {rule['name']}: {validation_result.issues[0]['message']}"
            errors.append(error_msg)
            if verbose:
                for issue in validation_result.issues:
                    print_error(f"  {issue['message']}")
            return None, errors, warnings
    
    # Handle existing files
    if rule_file.exists():
        if not force:
            print_warning(f"⏭️  Skipping {rule['name']} (already exists, use --force to overwrite)")
            return None, [], []
        
        # Show diff if requested
        if show_diffs:
            existing_content = rule_file.read_text(encoding='utf-8')
            show_diff(existing_content, rule['content'], rule_file)
        
        # Create backup if requested
        if auto_backup:
            create_backup(rule_file)
    
    # Write file
    if dry_run:
        print_info(f"🔍 [DRY RUN] Would create: {rule_file}")
        return rule['name'], [], warnings
    else:
        # Create folder for rule (folder-based format)
        rule_file.parent.mkdir(parents=True, exist_ok=True)
        rule_file.write_text(rule['content'], encoding='utf-8')
        print_success(f"Converted: {skill['name']} → {rule['name']}")
        
        # Update state if memory is available
        if state_manager and MEMORY_AVAILABLE:
            state_manager.update_state(skill['name'], skill_file, "claude", "cursor")
        
        return rule['name'], [], warnings


def convert_claude_to_cursor(project_path: Path, force: bool = False, dry_run: bool = False,
                             show_diffs: bool = False, auto_backup: bool = False,
                             validate: bool = True, verbose: bool = False,
                             state_manager: Optional[MigrationStateManager] = None,
                             skip_unchanged: bool = True) -> ConversionResult:
    """Convert Claude Skills to Cursor rules."""
    from utils import fetch_documentation
    
    skills_dir = project_path / '.claude' / 'skills'
    if not skills_dir.exists():
        print_warning(f"No `.claude/skills` directory found in {project_path}")
        return ConversionResult(converted=[], errors=[], warnings=[])
    
    # Initialize documentation cache
    doc_cache = DocumentationCache() if MEMORY_AVAILABLE else None
    
    # Fetch latest Cursor Rules documentation
    fetch_documentation(CURSOR_RULES_URL, 'cursor_rules', doc_cache=doc_cache)
    
    # Find all skill directories
    skill_dirs = [d for d in skills_dir.iterdir() if d.is_dir() and (d / 'SKILL.md').exists()]
    
    if not skill_dirs:
        print_warning(f"No skill directories found in {skills_dir}")
        return ConversionResult(converted=[], errors=[], warnings=[])
    
    converted = []
    errors = []
    warnings = []
    rules_dir = project_path / '.cursor' / 'rules'
    rules_dir.mkdir(parents=True, exist_ok=True)
    
    # Use progress bar if available
    iterator = tqdm(skill_dirs, desc="Converting skills", unit="skill") if TQDM_AVAILABLE else skill_dirs
    
    # Sequential processing (parallel can be added later with proper state management)
    for skill_dir in iterator:
        try:
            rule_name, file_errors, file_warnings = _process_single_claude_skill(
                skill_dir, project_path, force, dry_run, show_diffs, auto_backup,
                validate, verbose, state_manager, skip_unchanged
            )
            if rule_name:
                converted.append(rule_name)
            errors.extend(file_errors)
            warnings.extend(file_warnings)
        except Exception as e:
            error_msg = f"Error converting {skill_dir}: {e}"
            errors.append(error_msg)
            if verbose:
                import traceback
                print_error(error_msg)
                if console and Syntax:
                    console.print(Syntax(traceback.format_exc(), "python", theme="monokai"))
                else:
                    traceback.print_exc()
    
    return ConversionResult(converted=converted, errors=errors, warnings=warnings)
