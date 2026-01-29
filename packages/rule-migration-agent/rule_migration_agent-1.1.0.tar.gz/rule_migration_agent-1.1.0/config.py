#!/usr/bin/env python3
"""
Configuration file support for rule-migration-agent

Supports .migration-config.yaml for project-specific settings.
"""

import yaml
from pathlib import Path
from typing import Dict, Optional, List


class MigrationConfig:
    """Manages migration configuration from .migration-config.yaml"""
    
    def __init__(self, project_path: Path):
        self.project_path = project_path
        self.config_file = project_path / '.migration-config.yaml'
        self.config = self._load_config()
    
    def _load_config(self) -> Dict:
        """Load configuration from file or return defaults."""
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    config = yaml.safe_load(f) or {}
                    return config
            except Exception as e:
                print(f"⚠️  Warning: Could not load config file: {e}")
                return self._default_config()
        return self._default_config()
    
    def _default_config(self) -> Dict:
        """Return default configuration."""
        return {
            "preferences": {
                "cursor_format": "folder",  # "folder" or "file"
                "claude_format": "folder",
                "auto_backup": True,
                "conflict_resolution": "ask",  # "ask", "ours", "theirs", "merge"
                "skip_unchanged": True,
                "validate_after_conversion": True,
                "show_diffs": False,
                "verbose_logging": False
            },
            "skip_patterns": [],
            "custom_mappings": {},
            "validation": {
                "strict": False,
                "auto_fix": False
            }
        }
    
    def get_preference(self, key: str, default=None):
        """Get a preference value."""
        return self.config.get("preferences", {}).get(key, default)
    
    def should_skip(self, file_path: Path) -> bool:
        """Check if file should be skipped based on patterns."""
        skip_patterns = self.config.get("skip_patterns", [])
        file_str = str(file_path.relative_to(self.project_path))
        
        for pattern in skip_patterns:
            # Simple glob matching (can be enhanced with fnmatch)
            if pattern in file_str or file_path.match(pattern):
                return True
        return False
    
    def get_custom_mapping(self, name: str) -> Optional[str]:
        """Get custom name mapping."""
        return self.config.get("custom_mappings", {}).get(name)
    
    def is_strict_validation(self) -> bool:
        """Check if strict validation is enabled."""
        return self.config.get("validation", {}).get("strict", False)
    
    def should_auto_fix(self) -> bool:
        """Check if auto-fix is enabled."""
        return self.config.get("validation", {}).get("auto_fix", False)
