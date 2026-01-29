#!/usr/bin/env python3
"""
Tests for conversion functions.
"""

import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
import sys

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from converters import (
    convert_cursor_to_claude,
    convert_claude_to_cursor,
    cursor_rule_to_claude_skill,
    claude_skill_to_cursor_rule
)
from utils import ConversionResult


class TestConversionResult(unittest.TestCase):
    """Test ConversionResult TypedDict."""
    
    def test_conversion_result_structure(self):
        """Test that ConversionResult has correct structure."""
        result = ConversionResult(
            converted=["skill1", "skill2"],
            errors=["error1"],
            warnings=["warning1"]
        )
        
        self.assertEqual(result['converted'], ["skill1", "skill2"])
        self.assertEqual(result['errors'], ["error1"])
        self.assertEqual(result['warnings'], ["warning1"])


class TestCursorToClaudeConversion(unittest.TestCase):
    """Test Cursor to Claude conversion."""
    
    def test_convert_empty_project(self):
        """Test conversion with no rules."""
        with TemporaryDirectory() as tmpdir:
            project_path = Path(tmpdir)
            rules_dir = project_path / '.cursor' / 'rules'
            rules_dir.mkdir(parents=True)
            
            result = convert_cursor_to_claude(project_path, dry_run=True)
            self.assertIsInstance(result, dict)
            self.assertEqual(result['converted'], [])
    
    def test_convert_single_rule(self):
        """Test converting a single rule."""
        with TemporaryDirectory() as tmpdir:
            project_path = Path(tmpdir)
            rules_dir = project_path / '.cursor' / 'rules'
            rules_dir.mkdir(parents=True)
            
            rule_file = rules_dir / "test.mdc"
            rule_file.write_text("""---
description: Test rule
---
Test content.
""")
            
            result = convert_cursor_to_claude(project_path, dry_run=True, force=True)
            self.assertIsInstance(result, dict)
            # Should have converted one rule
            self.assertEqual(len(result['converted']), 1)


class TestClaudeToCursorConversion(unittest.TestCase):
    """Test Claude to Cursor conversion."""
    
    def test_convert_empty_project(self):
        """Test conversion with no skills."""
        with TemporaryDirectory() as tmpdir:
            project_path = Path(tmpdir)
            skills_dir = project_path / '.claude' / 'skills'
            skills_dir.mkdir(parents=True)
            
            result = convert_claude_to_cursor(project_path, dry_run=True)
            self.assertIsInstance(result, dict)
            self.assertEqual(result['converted'], [])
    
    def test_convert_single_skill(self):
        """Test converting a single skill."""
        with TemporaryDirectory() as tmpdir:
            project_path = Path(tmpdir)
            skills_dir = project_path / '.claude' / 'skills'
            skills_dir.mkdir(parents=True)
            
            skill_dir = skills_dir / "test-skill"
            skill_dir.mkdir()
            skill_file = skill_dir / "SKILL.md"
            skill_file.write_text("""---
description: Test skill
---
Test content.
""")
            
            result = convert_claude_to_cursor(project_path, dry_run=True, force=True)
            self.assertIsInstance(result, dict)
            # Should have converted one skill
            self.assertEqual(len(result['converted']), 1)


if __name__ == '__main__':
    unittest.main()
