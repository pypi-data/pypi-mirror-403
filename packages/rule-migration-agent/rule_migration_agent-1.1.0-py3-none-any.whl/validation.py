#!/usr/bin/env python3
"""
Validation module for rule-migration-agent

Validates Cursor rules and Claude Skills according to format specifications.
"""

import re
import yaml
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from datetime import datetime

# Import ValidationError from utils to avoid duplication
try:
    from utils import ValidationError
except ImportError:
    # Fallback if utils not available
    class ValidationError(Exception):
        """Custom exception for validation errors."""
        pass


class ValidationResult:
    """Result of validation with issues and warnings."""
    
    def __init__(self, valid: bool = True):
        self.valid = valid
        self.issues: List[Dict] = []
        self.warnings: List[Dict] = []
    
    def add_issue(self, type: str, message: str, fix: Optional[str] = None, severity: str = "error"):
        """Add a validation issue."""
        self.issues.append({
            "type": type,
            "message": message,
            "fix": fix,
            "severity": severity
        })
        if severity == "error":
            self.valid = False
    
    def add_warning(self, type: str, message: str, fix: Optional[str] = None):
        """Add a validation warning."""
        self.warnings.append({
            "type": type,
            "message": message,
            "fix": fix
        })
    
    def has_issues(self) -> bool:
        """Check if there are any issues."""
        return len(self.issues) > 0
    
    def get_summary(self) -> str:
        """Get summary of validation results."""
        if self.valid and not self.warnings:
            return "✅ Valid"
        elif self.valid:
            return f"✅ Valid ({len(self.warnings)} warning(s))"
        else:
            return f"❌ Invalid ({len(self.issues)} error(s), {len(self.warnings)} warning(s))"


def validate_cursor_rule(rule_path: Path, content: Optional[str] = None) -> ValidationResult:
    """Validate a Cursor rule file."""
    result = ValidationResult()
    
    if content is None:
        if not rule_path.exists():
            result.add_issue("file_not_found", f"Rule file does not exist: {rule_path}")
            return result
        try:
            content = rule_path.read_text(encoding='utf-8')
        except Exception as e:
            result.add_issue("read_error", f"Could not read file: {e}")
            return result
    
    # Check for frontmatter
    if not content.startswith('---'):
        result.add_warning("no_frontmatter", "Rule does not have YAML frontmatter", 
                          "Add YAML frontmatter with --- delimiters")
        return result
    
    # Parse frontmatter
    try:
        parts = content.split('---', 2)
        if len(parts) < 3:
            result.add_issue("invalid_frontmatter", "Invalid frontmatter format", 
                           "Ensure frontmatter is properly delimited with ---")
            return result
        
        frontmatter_str = parts[1].strip()
        frontmatter = yaml.safe_load(frontmatter_str)
        
        if frontmatter is None:
            frontmatter = {}
        
        # Check required fields
        if 'description' not in frontmatter:
            result.add_issue("missing_description", "Missing required 'description' field",
                          "Add description field to frontmatter")
        
        # Validate description
        if 'description' in frontmatter:
            desc = frontmatter['description']
            if not isinstance(desc, str):
                result.add_issue("invalid_description", "Description must be a string",
                               "Change description to a string value")
            elif len(desc) == 0:
                result.add_warning("empty_description", "Description is empty",
                                 "Add a meaningful description")
        
        # Validate globs if present
        if 'globs' in frontmatter:
            globs = frontmatter['globs']
            if not isinstance(globs, list):
                result.add_issue("invalid_globs", "globs must be an array",
                               "Change globs to an array format: globs: [\"pattern\"]")
            else:
                for i, glob in enumerate(globs):
                    if not isinstance(glob, str):
                        result.add_issue("invalid_glob_item", f"globs[{i}] must be a string",
                                       f"Change globs[{i}] to a string")
        
        # Validate alwaysApply if present
        if 'alwaysApply' in frontmatter:
            always_apply = frontmatter['alwaysApply']
            if not isinstance(always_apply, bool):
                result.add_issue("invalid_alwaysApply", "alwaysApply must be a boolean",
                               "Change alwaysApply to true or false")
        
        # Validate YAML syntax
        try:
            yaml.safe_load(frontmatter_str)
        except yaml.YAMLError as e:
            result.add_issue("yaml_syntax_error", f"Invalid YAML syntax: {e}",
                           "Fix YAML syntax errors in frontmatter")
        
    except Exception as e:
        result.add_issue("parse_error", f"Error parsing frontmatter: {e}",
                        "Check YAML syntax and structure")
    
    return result


def validate_claude_skill(skill_path: Path, content: Optional[str] = None) -> ValidationResult:
    """Validate a Claude Skill file."""
    result = ValidationResult()
    
    if content is None:
        skill_file = skill_path / 'SKILL.md' if skill_path.is_dir() else skill_path
        if not skill_file.exists():
            result.add_issue("file_not_found", f"Skill file does not exist: {skill_file}")
            return result
        try:
            content = skill_file.read_text(encoding='utf-8')
        except Exception as e:
            result.add_issue("read_error", f"Could not read file: {e}")
            return result
    
    # Check for frontmatter
    if not content.startswith('---'):
        result.add_issue("no_frontmatter", "Skill must have YAML frontmatter",
                        "Add YAML frontmatter with --- delimiters")
        return result
    
    # Parse frontmatter
    try:
        parts = content.split('---', 2)
        if len(parts) < 3:
            result.add_issue("invalid_frontmatter", "Invalid frontmatter format",
                           "Ensure frontmatter is properly delimited with ---")
            return result
        
        frontmatter_str = parts[1].strip()
        frontmatter = yaml.safe_load(frontmatter_str)
        
        if frontmatter is None:
            frontmatter = {}
        
        # Check required fields
        if 'name' not in frontmatter:
            result.add_issue("missing_name", "Missing required 'name' field",
                          "Add name field to frontmatter")
        else:
            name = frontmatter['name']
            if not isinstance(name, str):
                result.add_issue("invalid_name", "name must be a string",
                               "Change name to a string value")
            else:
                # Validate name constraints
                if not name.islower():
                    result.add_issue("name_not_lowercase", "name must be lowercase",
                                   f"Change name to lowercase: {name.lower()}")
                if ' ' in name or '_' in name:
                    result.add_issue("name_invalid_chars", "name must use hyphens, not spaces or underscores",
                                   f"Change name to use hyphens: {name.replace(' ', '-').replace('_', '-')}")
                if not re.match(r'^[a-z0-9-]+$', name):
                    result.add_issue("name_invalid_format", "name contains invalid characters",
                                   "Name must contain only lowercase letters, numbers, and hyphens")
                if name.startswith('-') or name.endswith('-'):
                    result.add_issue("name_trailing_hyphens", "name cannot start or end with hyphens",
                                   f"Remove leading/trailing hyphens: {name.strip('-')}")
        
        if 'description' not in frontmatter:
            result.add_issue("missing_description", "Missing required 'description' field",
                          "Add description field to frontmatter")
        else:
            desc = frontmatter['description']
            if not isinstance(desc, str):
                result.add_issue("invalid_description", "description must be a string",
                               "Change description to a string value")
            elif len(desc) == 0:
                result.add_warning("empty_description", "Description is empty",
                                 "Add a meaningful description")
            elif len(desc) > 1024:
                result.add_issue("description_too_long", f"Description is {len(desc)} chars (limit: 1024)",
                               f"Truncate description to 1024 chars: {desc[:1021]}...")
            elif len(desc) > 900:
                result.add_warning("description_near_limit", f"Description is {len(desc)} chars (limit: 1024)",
                                 "Consider shortening description")
        
        # Validate optional fields
        if 'allowed-tools' in frontmatter:
            tools = frontmatter['allowed-tools']
            if not isinstance(tools, list):
                result.add_issue("invalid_allowed_tools", "allowed-tools must be an array",
                               "Change allowed-tools to an array format")
        
        if 'model' in frontmatter:
            model = frontmatter['model']
            if not isinstance(model, str):
                result.add_issue("invalid_model", "model must be a string",
                               "Change model to a string value")
        
        # Validate YAML syntax
        try:
            yaml.safe_load(frontmatter_str)
        except yaml.YAMLError as e:
            result.add_issue("yaml_syntax_error", f"Invalid YAML syntax: {e}",
                           "Fix YAML syntax errors in frontmatter")
        
    except Exception as e:
        result.add_issue("parse_error", f"Error parsing frontmatter: {e}",
                        "Check YAML syntax and structure")
    
    return result


def validate_glob_pattern(pattern: str) -> bool:
    """Validate a glob pattern."""
    # Basic validation - check for common issues
    if not pattern:
        return False
    
    # Check for balanced brackets
    if pattern.count('[') != pattern.count(']'):
        return False
    
    if pattern.count('{') != pattern.count('}'):
        return False
    
    return True


def auto_fix_validation_issue(issue: Dict, content: str) -> Optional[str]:
    """Attempt to auto-fix a validation issue."""
    issue_type = issue.get("type")
    fix = issue.get("fix")
    
    if not fix:
        return None
    
    # Simple auto-fixes
    if issue_type == "name_not_lowercase":
        # Find and replace name in frontmatter
        lines = content.split('\n')
        for i, line in enumerate(lines):
            if line.strip().startswith('name:'):
                value = line.split(':', 1)[1].strip().strip('"\'')
                fixed_value = value.lower()
                lines[i] = f"name: {fixed_value}"
                return '\n'.join(lines)
    
    if issue_type == "description_too_long":
        # Truncate description
        lines = content.split('\n')
        for i, line in enumerate(lines):
            if line.strip().startswith('description:'):
                # Extract and truncate
                desc_match = re.search(r'description:\s*["\'](.*)["\']', line)
                if desc_match:
                    desc = desc_match.group(1)
                    if len(desc) > 1024:
                        truncated = desc[:1021] + "..."
                        lines[i] = f'description: "{truncated}"'
                        return '\n'.join(lines)
    
    return None
