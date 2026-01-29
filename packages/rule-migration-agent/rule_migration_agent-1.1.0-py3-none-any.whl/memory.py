#!/usr/bin/env python3
"""
Context Memory System for Rule Migration Agent

Provides persistent memory for tracking state, history, preferences, and validation results.
"""

import json
import hashlib
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime, timezone, timedelta
import os
import shutil


class MigrationStateManager:
    """Manages project state memory for migration operations."""
    
    def __init__(self, project_path: Path):
        self.project_path = project_path
        self.state_file = project_path / '.migration-state.json'
        self.state = self._load_state()
    
    def _load_state(self) -> Dict:
        """Load state from file or create new."""
        if self.state_file.exists():
            try:
                with open(self.state_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                # Use basic print here since utils may not be available during import
                # In the future, this could use logging module
                import warnings
                warnings.warn(f"Could not load state file: {e}", UserWarning)
                return self._create_empty_state()
        return self._create_empty_state()
    
    def _create_empty_state(self) -> Dict:
        """Create empty state structure."""
        return {
            "version": "1.0",
            "project_path": str(self.project_path),
            "last_updated": None,
            "cursor_rules": {},
            "claude_skills": {},
            "project_context": {},
            "sync_status": {
                "last_sync": None,
                "rules_count": 0,
                "skills_count": 0,
                "in_sync": False
            }
        }
    
    def save(self) -> None:
        """Save state to file."""
        self.state["last_updated"] = datetime.now(timezone.utc).isoformat()
        self.state_file.parent.mkdir(parents=True, exist_ok=True)
        with open(self.state_file, 'w', encoding='utf-8') as f:
            json.dump(self.state, f, indent=2, ensure_ascii=False)
    
    def get_file_hash(self, file_path: Path) -> str:
        """Calculate SHA256 hash of file."""
        if not file_path.exists():
            return ""
        try:
            with open(file_path, 'rb') as f:
                return hashlib.sha256(f.read()).hexdigest()
        except Exception:
            return ""
    
    def has_changed(self, file_path: Path, track_type: str = "cursor") -> bool:
        """Check if file has changed since last state."""
        if track_type == "cursor":
            items = self.state.get("cursor_rules", {})
        elif track_type == "claude":
            items = self.state.get("claude_skills", {})
        else:
            items = self.state.get("project_context", {})
        
        # Determine tracking name
        if track_type == "context":
            # For context files, use the relative path as key
            try:
                item_name = str(file_path.relative_to(self.project_path))
            except ValueError:
                item_name = file_path.name
        else:
            item_name = file_path.parent.name if file_path.name == "RULE.md" else file_path.stem
            
        current_hash = self.get_file_hash(file_path)
        
        if item_name in items:
            stored_hash = items[item_name].get("hash", "")
            return current_hash != stored_hash
        
        return True  # New file, consider it changed
    
    def update_state(self, item_name: str, item_path: Path, track_type: str = "cursor", 
                    converted_to: Optional[str] = None) -> None:
        """Update state for an item (rule, skill, or context file)."""
        if track_type == "cursor":
            items = self.state.setdefault("cursor_rules", {})
        elif track_type == "claude":
            items = self.state.setdefault("claude_skills", {})
        else:
            items = self.state.setdefault("project_context", {})
        
        file_hash = self.get_file_hash(item_path)
        mtime = datetime.fromtimestamp(item_path.stat().st_mtime, tz=timezone.utc).isoformat()
        
        item_state = {
            "path": str(item_path.relative_to(self.project_path)),
            "hash": file_hash,
            "last_modified": mtime,
            "converted_to_claude": converted_to == "claude" if track_type == "cursor" else None,
            "converted_to_cursor": converted_to == "cursor" if track_type == "claude" else None,
            "conversion_date": datetime.now(timezone.utc).isoformat() if converted_to else None
        }
        
        if converted_to:
            if track_type == "cursor":
                item_state["claude_skill_name"] = converted_to
            elif track_type == "claude":
                item_state["cursor_rule_name"] = converted_to
        
        items[item_name] = item_state
        self.save()
    
    def get_sync_status(self) -> Dict:
        """Get current sync status."""
        return self.state.get("sync_status", {})
    
    def update_sync_status(self, rules_count: int, skills_count: int, in_sync: bool) -> None:
        """Update sync status."""
        self.state.setdefault("sync_status", {})
        self.state["sync_status"].update({
            "last_sync": datetime.now(timezone.utc).isoformat(),
            "rules_count": rules_count,
            "skills_count": skills_count,
            "in_sync": in_sync
        })
        self.save()


class ConversionHistory:
    """Manages conversion history log."""
    
    def __init__(self, project_path: Path):
        self.project_path = project_path
        self.history_file = project_path / '.migration-history.json'
        self.history = self._load_history()
    
    def _load_history(self) -> Dict:
        """Load history from file or create new."""
        if self.history_file.exists():
            try:
                with open(self.history_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception:
                return self._create_empty_history()
        return self._create_empty_history()
    
    def _create_empty_history(self) -> Dict:
        """Create empty history structure."""
        return {
            "version": "1.0",
            "operations": []
        }
    
    def log_operation(self, direction: str, rules_converted: List[str], 
                     skills_created: List[str], errors: List[str] = None,
                     warnings: List[str] = None, duration_ms: int = 0,
                     command: str = "") -> str:
        """Log a conversion operation."""
        operation_id = f"op-{len(self.history['operations']) + 1:03d}"
        
        operation = {
            "id": operation_id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "direction": direction,
            "rules_converted": rules_converted,
            "skills_created": skills_created,
            "errors": errors or [],
            "warnings": warnings or [],
            "duration_ms": duration_ms,
            "user": os.getenv("USER", "unknown"),
            "command": command
        }
        
        self.history["operations"].append(operation)
        self._save_history()
        return operation_id
    
    def _save_history(self) -> None:
        """Save history to file."""
        self.history_file.parent.mkdir(parents=True, exist_ok=True)
        with open(self.history_file, 'w', encoding='utf-8') as f:
            json.dump(self.history, f, indent=2, ensure_ascii=False)
    
    def get_recent_operations(self, limit: int = 10) -> List[Dict]:
        """Get recent operations."""
        return self.history["operations"][-limit:]
    
    def get_operation(self, operation_id: str) -> Optional[Dict]:
        """Get specific operation by ID."""
        for op in self.history["operations"]:
            if op["id"] == operation_id:
                return op
        return None


class PreferencesManager:
    """Manages user preferences per project."""
    
    def __init__(self, project_path: Path):
        self.project_path = project_path
        self.prefs_file = project_path / '.migration-preferences.json'
        self.preferences = self._load_preferences()
    
    def _load_preferences(self) -> Dict:
        """Load preferences from file or create defaults."""
        if self.prefs_file.exists():
            try:
                with open(self.prefs_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception:
                return self._create_default_preferences()
        return self._create_default_preferences()
    
    def _create_default_preferences(self) -> Dict:
        """Create default preferences."""
        return {
            "version": "1.0",
            "preferences": {
                "default_format": "folder",
                "auto_backup": True,
                "conflict_resolution": "ask",
                "skip_unchanged": True,
                "validate_after_conversion": True,
                "show_diffs": True,
                "verbose_logging": False
            },
            "last_used_options": {
                "force": False,
                "dry_run": False,
                "skip_existing": True
            }
        }
    
    def get_preference(self, key: str, default: Any = None) -> Any:
        """Get a preference value."""
        return self.preferences.get("preferences", {}).get(key, default)
    
    def set_preference(self, key: str, value: Any) -> None:
        """Set a preference value."""
        self.preferences.setdefault("preferences", {})[key] = value
        self._save_preferences()
    
    def get_last_options(self) -> Dict:
        """Get last used command options."""
        return self.preferences.get("last_used_options", {})
    
    def update_last_options(self, options: Dict) -> None:
        """Update last used options."""
        self.preferences["last_used_options"].update(options)
        self._save_preferences()
    
    def _save_preferences(self) -> None:
        """Save preferences to file."""
        self.prefs_file.parent.mkdir(parents=True, exist_ok=True)
        with open(self.prefs_file, 'w', encoding='utf-8') as f:
            json.dump(self.preferences, f, indent=2, ensure_ascii=False)


class DocumentationCache:
    """Manages persistent documentation cache."""
    
    def __init__(self):
        cache_dir = Path.home() / '.cache' / 'rule-migration-agent' / 'docs'
        cache_dir.mkdir(parents=True, exist_ok=True)
        self.cache_dir = cache_dir
        self.metadata_file = cache_dir / 'cache-metadata.json'
        self.metadata = self._load_metadata()
    
    def _load_metadata(self) -> Dict:
        """Load cache metadata."""
        if self.metadata_file.exists():
            try:
                with open(self.metadata_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception:
                return {}
        return {}
    
    def get_cached_doc(self, doc_type: str, ttl_hours: int = 24) -> Optional[str]:
        """Get cached documentation if not expired."""
        if doc_type not in self.metadata:
            return None
        
        doc_info = self.metadata[doc_type]
        cached_at = datetime.fromisoformat(doc_info["cached_at"])
        expires_at = datetime.fromisoformat(doc_info["expires_at"])
        
        if datetime.now(timezone.utc) > expires_at:
            return None  # Expired
        
        cache_file = self.cache_dir / f"{doc_type}.html"
        if cache_file.exists():
            try:
                return cache_file.read_text(encoding='utf-8')
            except Exception:
                return None
        
        return None
    
    def cache_doc(self, doc_type: str, content: str, ttl_hours: int = 24, url: Optional[str] = None) -> None:
        """Cache documentation."""
        cache_file = self.cache_dir / f"{doc_type}.html"
        cache_file.write_text(content, encoding='utf-8')
        
        now = datetime.now(timezone.utc)
        expires_at = now + timedelta(hours=ttl_hours)
        content_hash = hashlib.sha256(content.encode('utf-8')).hexdigest()
        
        self.metadata[doc_type] = {
            "url": url or "",
            "cached_at": now.isoformat(),
            "expires_at": expires_at.isoformat(),
            "ttl_hours": ttl_hours,
            "hash": content_hash
        }
        
        self._save_metadata()
    
    def _save_metadata(self) -> None:
        """Save cache metadata."""
        with open(self.metadata_file, 'w', encoding='utf-8') as f:
            json.dump(self.metadata, f, indent=2, ensure_ascii=False)


class GlobalAgentMemory:
    """Manages global agent-level memory (user-level, not project-specific)."""
    
    def __init__(self):
        config_dir = Path.home() / '.config' / 'rule-migration-agent'
        config_dir.mkdir(parents=True, exist_ok=True)
        self.memory_file = config_dir / 'agent-memory.json'
        self.memory = self._load_memory()
    
    def _load_memory(self) -> Dict:
        """Load global memory from file or create new."""
        if self.memory_file.exists():
            try:
                with open(self.memory_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                # Use warnings module for import-time errors
                import warnings
                warnings.warn(f"Could not load agent memory: {e}", UserWarning)
                return self._create_empty_memory()
        return self._create_empty_memory()
    
    def _create_empty_memory(self) -> Dict:
        """Create empty global memory structure."""
        return {
            "version": "1.0",
            "statistics": {
                "total_conversions": 0,
                "total_projects": 0,
                "total_rules_converted": 0,
                "total_skills_converted": 0,
                "average_conversion_time_ms": 0
            },
            "preferences": {
                "default_ttl_hours": 24,
                "auto_update_docs": True,
                "preferred_format": "folder"
            },
            "recent_projects": []
        }
    
    def save(self) -> None:
        """Save global memory to file."""
        self.memory_file.parent.mkdir(parents=True, exist_ok=True)
        with open(self.memory_file, 'w', encoding='utf-8') as f:
            json.dump(self.memory, f, indent=2, ensure_ascii=False)
    
    def update_statistics(self, conversions: int = 0, rules_converted: int = 0,
                         skills_converted: int = 0, duration_ms: int = 0) -> None:
        """Update global statistics."""
        stats = self.memory.setdefault("statistics", {})
        stats["total_conversions"] = stats.get("total_conversions", 0) + conversions
        stats["total_rules_converted"] = stats.get("total_rules_converted", 0) + rules_converted
        stats["total_skills_converted"] = stats.get("total_skills_converted", 0) + skills_converted
        
        # Update average conversion time
        total_conversions = stats["total_conversions"]
        if total_conversions > 0:
            current_avg = stats.get("average_conversion_time_ms", 0)
            # Weighted average
            stats["average_conversion_time_ms"] = int(
                (current_avg * (total_conversions - 1) + duration_ms) / total_conversions
            )
        self.save()
    
    def add_recent_project(self, project_path: Path) -> None:
        """Add or update a recent project."""
        project_str = str(project_path)
        recent = self.memory.setdefault("recent_projects", [])
        
        # Remove if exists
        recent = [p for p in recent if p["path"] != project_str]
        
        # Add to front
        recent.insert(0, {
            "path": project_str,
            "last_used": datetime.now(timezone.utc).isoformat(),
            "conversion_count": 1
        })
        
        # Keep only last 20
        self.memory["recent_projects"] = recent[:20]
        self.save()
    
    def increment_project_conversion_count(self, project_path: Path) -> None:
        """Increment conversion count for a project."""
        project_str = str(project_path)
        recent = self.memory.setdefault("recent_projects", [])
        
        for project in recent:
            if project["path"] == project_str:
                project["conversion_count"] = project.get("conversion_count", 0) + 1
                project["last_used"] = datetime.now(timezone.utc).isoformat()
                self.save()
                return
        
        # Not found, add it
        self.add_recent_project(project_path)
    
    def get_preference(self, key: str, default: Any = None) -> Any:
        """Get a global preference."""
        return self.memory.get("preferences", {}).get(key, default)
    
    def set_preference(self, key: str, value: Any) -> None:
        """Set a global preference."""
        self.memory.setdefault("preferences", {})[key] = value
        self.save()
    
    def get_statistics(self) -> Dict:
        """Get global statistics."""
        return self.memory.get("statistics", {})
