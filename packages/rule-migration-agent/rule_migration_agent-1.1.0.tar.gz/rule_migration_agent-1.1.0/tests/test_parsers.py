#!/usr/bin/env python3
"""
Tests for file parsers.
"""

import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
import sys
import yaml

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from parsers import parse_cursor_rule, parse_claude_skill
from utils import ParseError


class TestParseCursorRule(unittest.TestCase):
    """Test Cursor rule parsing."""
    
    def test_parse_with_frontmatter(self):
        """Test parsing rule with YAML frontmatter."""
        with TemporaryDirectory() as tmpdir:
            rule_file = Path(tmpdir) / "test.mdc"
            content = """---
description: Test rule
---
This is the body content.
"""
            rule_file.write_text(content)
            
            result = parse_cursor_rule(rule_file)
            self.assertIsNotNone(result)
            self.assertEqual(result['name'], 'test')
            self.assertEqual(result['frontmatter']['description'], 'Test rule')
            self.assertEqual(result['body'], 'This is the body content.')
    
    def test_parse_index_file(self):
        """Test parsing INDEX.md file."""
        with TemporaryDirectory() as tmpdir:
            index_file = Path(tmpdir) / "INDEX.md"
            content = "Index content"
            index_file.write_text(content)
            
            result = parse_cursor_rule(index_file)
            self.assertIsNotNone(result)
            self.assertEqual(result['name'], 'rules-index')
            self.assertEqual(result['body'], 'Index content')
    
    def test_parse_invalid_file(self):
        """Test parsing invalid file raises ParseError."""
        with TemporaryDirectory() as tmpdir:
            invalid_file = Path(tmpdir) / "invalid.txt"
            # Create a file that will cause parsing to fail
            invalid_file.write_bytes(b'\xff\xfe\x00\x00')  # Invalid UTF-8
            
            with self.assertRaises(ParseError):
                parse_cursor_rule(invalid_file)


class TestParseClaudeSkill(unittest.TestCase):
    """Test Claude Skill parsing."""
    
    def test_parse_skill(self):
        """Test parsing Claude Skill."""
        with TemporaryDirectory() as tmpdir:
            skill_dir = Path(tmpdir) / "test-skill"
            skill_dir.mkdir()
            skill_file = skill_dir / "SKILL.md"
            
            content = """---
description: Test skill
---
This is the skill body.
"""
            skill_file.write_text(content)
            
            result = parse_claude_skill(skill_dir)
            self.assertIsNotNone(result)
            self.assertEqual(result['name'], 'test-skill')
            self.assertEqual(result['frontmatter']['description'], 'Test skill')
            self.assertEqual(result['body'], 'This is the skill body.')
    
    def test_parse_nonexistent_skill(self):
        """Test parsing nonexistent skill returns None."""
        with TemporaryDirectory() as tmpdir:
            skill_dir = Path(tmpdir) / "nonexistent"
            skill_dir.mkdir()
            
            result = parse_claude_skill(skill_dir)
            self.assertIsNone(result)


if __name__ == '__main__':
    unittest.main()
