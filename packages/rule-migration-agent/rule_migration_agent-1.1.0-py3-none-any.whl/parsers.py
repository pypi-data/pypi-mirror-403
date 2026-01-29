#!/usr/bin/env python3
"""
File parsing module for rule-migration-agent

Handles parsing of Cursor rules and Claude Skills.
"""

import yaml
from pathlib import Path
from typing import Dict, Optional
from utils import read_file_with_cache


def parse_cursor_rule(file_path: Path) -> Optional[Dict]:
    """Parse a Cursor rule file (.mdc, RULE.md, or INDEX.md)."""
    try:
        content = read_file_with_cache(file_path)
        
        # Handle INDEX.md files (no frontmatter, just content)
        if file_path.name == 'INDEX.md':
            return {
                'name': 'rules-index',
                'frontmatter': {'description': 'Master index of all Cursor rules and Claude Skills organized by category'},
                'body': content,
                'path': file_path
            }
        
        # Split frontmatter and body
        if content.startswith('---'):
            parts = content.split('---', 2)
            if len(parts) >= 3:
                frontmatter_str = parts[1].strip()
                body = parts[2].strip()
                
                # Parse YAML frontmatter
                frontmatter = yaml.safe_load(frontmatter_str) or {}
                
                return {
                    'name': file_path.stem if file_path.suffix == '.mdc' else file_path.parent.name,
                    'frontmatter': frontmatter,
                    'body': body,
                    'path': file_path
                }
        
        # If no frontmatter, treat whole file as body (common for commands)
        return {
            'name': file_path.stem,
            'frontmatter': {},
            'body': content.strip(),
            'path': file_path
        }
    except Exception as e:
        # Import here to avoid circular dependency
        from utils import ParseError
        raise ParseError(f"Error parsing {file_path}: {e}") from e


def parse_claude_skill(skill_dir: Path) -> Optional[Dict]:
    """Parse a Claude Skill (SKILL.md file)."""
    skill_file = skill_dir / 'SKILL.md'
    if not skill_file.exists():
        return None
    
    try:
        content = read_file_with_cache(skill_file)
        
        # Split frontmatter and body
        if content.startswith('---'):
            parts = content.split('---', 2)
            if len(parts) >= 3:
                frontmatter_str = parts[1].strip()
                body = parts[2].strip()
                
                # Parse YAML frontmatter
                frontmatter = yaml.safe_load(frontmatter_str) or {}
                
                return {
                    'name': skill_dir.name,
                    'frontmatter': frontmatter,
                    'body': body,
                    'path': skill_file
                }
    except Exception as e:
        # Import here to avoid circular dependency
        from utils import ParseError
        raise ParseError(f"Error parsing {skill_dir}: {e}") from e
