#!/usr/bin/env python3
"""
Tests for validation functions.
"""

import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
import sys

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    from validation import validate_cursor_rule, validate_claude_skill
    VALIDATION_AVAILABLE = True
except ImportError:
    VALIDATION_AVAILABLE = False


@unittest.skipIf(not VALIDATION_AVAILABLE, "Validation module not available")
class TestValidation(unittest.TestCase):
    """Test validation functions."""
    
    def test_validate_cursor_rule(self):
        """Test Cursor rule validation."""
        with TemporaryDirectory() as tmpdir:
            rule_file = Path(tmpdir) / "test.mdc"
            rule_file.write_text("""---
description: Test rule
---
Test content.
""")
            
            result = validate_cursor_rule(rule_file)
            self.assertIsNotNone(result)
            # Should be valid
            self.assertTrue(result.valid)
    
    def test_validate_claude_skill(self):
        """Test Claude Skill validation."""
        with TemporaryDirectory() as tmpdir:
            skill_dir = Path(tmpdir) / "test-skill"
            skill_dir.mkdir()
            skill_file = skill_dir / "SKILL.md"
            skill_file.write_text("""---
description: Test skill
---
Test content.
""")
            
            result = validate_claude_skill(skill_dir)
            self.assertIsNotNone(result)
            # Should be valid
            self.assertTrue(result.valid)


if __name__ == '__main__':
    unittest.main()
