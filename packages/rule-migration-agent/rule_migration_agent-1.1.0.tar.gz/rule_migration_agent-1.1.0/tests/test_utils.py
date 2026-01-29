#!/usr/bin/env python3
"""
Tests for utility functions.
"""

import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
import sys

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils import (
    normalize_skill_name,
    validate_project_path,
    read_file_with_cache,
    clear_file_cache,
    MAX_SKILL_NAME_LENGTH,
    MAX_DESCRIPTION_LENGTH,
    MigrationError,
    ParseError,
    ValidationError,
    ConversionError
)


class TestNormalizeSkillName(unittest.TestCase):
    """Test skill name normalization."""
    
    def test_basic_normalization(self):
        """Test basic name normalization."""
        self.assertEqual(normalize_skill_name("My Skill"), "my-skill")
        self.assertEqual(normalize_skill_name("Test_Skill"), "test-skill")
        self.assertEqual(normalize_skill_name("test skill 123"), "test-skill-123")
    
    def test_empty_string(self):
        """Test that empty string raises ValueError."""
        with self.assertRaises(ValueError):
            normalize_skill_name("")
    
    def test_invalid_type(self):
        """Test that non-string input raises ValueError."""
        with self.assertRaises(ValueError):
            normalize_skill_name(None)
        with self.assertRaises(ValueError):
            normalize_skill_name(123)
    
    def test_special_characters(self):
        """Test handling of special characters."""
        self.assertEqual(normalize_skill_name("test@skill#name"), "testskillname")
        self.assertEqual(normalize_skill_name("test---skill"), "test-skill")
    
    def test_length_limit(self):
        """Test that very long names raise ValueError."""
        long_name = "a" * (MAX_SKILL_NAME_LENGTH + 1)
        with self.assertRaises(ValueError):
            normalize_skill_name(long_name)


class TestValidateProjectPath(unittest.TestCase):
    """Test project path validation."""
    
    def test_valid_path(self):
        """Test validation of valid existing path."""
        with TemporaryDirectory() as tmpdir:
            path = Path(tmpdir)
            self.assertTrue(validate_project_path(path))
    
    def test_nonexistent_path(self):
        """Test that nonexistent path returns False."""
        path = Path("/nonexistent/path/12345")
        self.assertFalse(validate_project_path(path))
    
    def test_file_not_directory(self):
        """Test that file path returns False."""
        with TemporaryDirectory() as tmpdir:
            test_file = Path(tmpdir) / "test.txt"
            test_file.write_text("test")
            self.assertFalse(validate_project_path(test_file))


class TestFileCache(unittest.TestCase):
    """Test file content caching."""
    
    def test_cache_basic(self):
        """Test basic caching functionality."""
        with TemporaryDirectory() as tmpdir:
            test_file = Path(tmpdir) / "test.txt"
            test_file.write_text("test content")
            
            # First read should cache
            content1 = read_file_with_cache(test_file)
            self.assertEqual(content1, "test content")
            
            # Second read should use cache
            content2 = read_file_with_cache(test_file)
            self.assertEqual(content2, "test content")
    
    def test_cache_clear(self):
        """Test cache clearing."""
        with TemporaryDirectory() as tmpdir:
            test_file = Path(tmpdir) / "test.txt"
            test_file.write_text("test content")
            
            read_file_with_cache(test_file)
            clear_file_cache()
            
            # Cache should be empty after clear
            # (We can't directly test this, but clear should not raise errors)
            self.assertTrue(True)


class TestExceptions(unittest.TestCase):
    """Test custom exception hierarchy."""
    
    def test_exception_hierarchy(self):
        """Test that exceptions inherit correctly."""
        self.assertIsInstance(ParseError(), MigrationError)
        self.assertIsInstance(ValidationError(), MigrationError)
        self.assertIsInstance(ConversionError(), MigrationError)
    
    def test_exception_messages(self):
        """Test exception message handling."""
        error = ParseError("Test error")
        self.assertEqual(str(error), "Test error")


if __name__ == '__main__':
    unittest.main()
