#!/usr/bin/env python3
"""
Utility functions for rule-migration-agent

Helper functions for normalization, diffs, backups, etc.
"""

import re
import difflib
import shutil
from pathlib import Path
from datetime import datetime
from typing import Optional, TypedDict, List as ListType, Dict, Tuple
from urllib.request import urlopen
from urllib.error import URLError

try:
    import requests
    from requests.adapters import HTTPAdapter
    from urllib3.util.retry import Retry
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False

try:
    from bs4 import BeautifulSoup
    BS4_AVAILABLE = True
except ImportError:
    BS4_AVAILABLE = False

try:
    from rich.console import Console
    from rich.panel import Panel
    from rich.syntax import Syntax
    console = Console()
    RICH_AVAILABLE = True
except ImportError:
    console = None
    RICH_AVAILABLE = False

try:
    from memory import DocumentationCache
    MEMORY_AVAILABLE = True
except ImportError:
    MEMORY_AVAILABLE = False
    class DocumentationCache:
        def __init__(self, *args, **kwargs): pass
        def get_cached_doc(self, *args, **kwargs): return None
        def cache_doc(self, *args, **kwargs): pass

# Cache for fetched documentation
DOCS_CACHE = {}

# Constants
MAX_DESCRIPTION_LENGTH = 1024
MAX_SKILL_NAME_LENGTH = 100


# Custom exceptions for standardized error handling
class MigrationError(Exception):
    """Base exception for migration errors."""
    pass


class ParseError(MigrationError):
    """Error parsing a rule or skill file."""
    pass


class ValidationError(MigrationError):
    """Error validating a rule or skill."""
    pass


class ConversionError(MigrationError):
    """Error during conversion."""
    pass


# TypedDict definitions for better type safety
class ConversionResult(TypedDict):
    """Result of a conversion operation."""
    converted: ListType[str]
    errors: ListType[str]
    warnings: ListType[str]


class ProjectResult(TypedDict):
    """Result of processing a project."""
    project: str
    converted_to_claude: int
    converted_to_cursor: int
    errors: int
    warnings: int
    duration_ms: int


# File content cache for processing
_FILE_CONTENT_CACHE: Dict[str, Tuple[str, float]] = {}  # path -> (content, timestamp)


def get_cached_file_content(file_path: Path, max_age_seconds: float = 60.0) -> Optional[str]:
    """Get file content from cache if available and fresh."""
    cache_key = str(file_path.resolve())
    if cache_key in _FILE_CONTENT_CACHE:
        content, timestamp = _FILE_CONTENT_CACHE[cache_key]
        import time
        if time.time() - timestamp < max_age_seconds:
            return content
        # Cache expired, remove it
        del _FILE_CONTENT_CACHE[cache_key]
    return None


def cache_file_content(file_path: Path, content: str) -> None:
    """Cache file content for faster subsequent reads."""
    import time
    cache_key = str(file_path.resolve())
    _FILE_CONTENT_CACHE[cache_key] = (content, time.time())


def read_file_with_cache(file_path: Path, encoding: str = 'utf-8') -> str:
    """Read file with caching support."""
    # Try cache first
    cached = get_cached_file_content(file_path)
    if cached is not None:
        return cached
    
    # Read from disk
    content = file_path.read_text(encoding=encoding)
    cache_file_content(file_path, content)
    return content


def clear_file_cache() -> None:
    """Clear the file content cache."""
    _FILE_CONTENT_CACHE.clear()


# Output utility functions to reduce duplication
def print_info(message: str) -> None:
    """Print an info message."""
    if console:
        console.print(f"[cyan]{message}[/cyan]")
    else:
        print(message)


def print_success(message: str) -> None:
    """Print a success message."""
    if console:
        console.print(f"[green]✅ {message}[/green]")
    else:
        print(f"✅ {message}")


def print_warning(message: str) -> None:
    """Print a warning message."""
    if console:
        console.print(f"[yellow]⚠️  {message}[/yellow]")
    else:
        print(f"⚠️  {message}")


def print_error(message: str) -> None:
    """Print an error message."""
    if console:
        console.print(f"[red]❌ {message}[/red]")
    else:
        print(f"❌ {message}")


def print_dim(message: str) -> None:
    """Print a dimmed message."""
    if console:
        console.print(f"[dim]{message}[/dim]")
    else:
        print(message)


def validate_project_path(project_path: Path) -> bool:
    """Validate that project path is safe and exists."""
    if not project_path.exists():
        return False
    
    # Resolve to absolute path to prevent path traversal
    resolved = project_path.resolve()
    
    # Ensure it's a directory
    if not resolved.is_dir():
        return False
    
    # Basic validation - ensure path doesn't contain dangerous patterns
    path_str = str(resolved)
    if '..' in path_str or path_str.startswith('/dev') or path_str.startswith('/proc'):
        return False
    
    return True


def normalize_skill_name(name: str) -> str:
    """Normalize name to Claude Skill requirements: lowercase, hyphens."""
    if not name or not isinstance(name, str):
        raise ValueError("Skill name must be a non-empty string")
    
    # Remove extension if present
    name = name.replace('.mdc', '').replace('.md', '')
    
    # Convert to lowercase
    name = name.lower()
    
    # Replace spaces and underscores with hyphens
    name = re.sub(r'[\s_]+', '-', name)
    
    # Remove invalid characters (keep only alphanumeric and hyphens)
    name = re.sub(r'[^a-z0-9-]', '', name)
    
    # Remove multiple consecutive hyphens
    name = re.sub(r'-+', '-', name)
    
    # Remove leading/trailing hyphens
    name = name.strip('-')
    
    # Validate result
    if not name:
        raise ValueError(f"Normalized skill name is empty (original: {name})")
    
    if len(name) > MAX_SKILL_NAME_LENGTH:
        raise ValueError(f"Normalized skill name too long: {len(name)} chars (max: {MAX_SKILL_NAME_LENGTH})")
    
    return name


def show_diff(existing_content: str, new_content: str, file_path: Path) -> None:
    """Show unified diff between existing and new content."""
    existing_lines = existing_content.splitlines(keepends=True)
    new_lines = new_content.splitlines(keepends=True)
    
    diff = list(difflib.unified_diff(
        existing_lines,
        new_lines,
        fromfile=str(file_path),
        tofile=str(file_path) + " (new)",
        lineterm=''
    ))
    
    if diff:
        if console:
            console.print(Panel(
                Syntax(''.join(diff), "diff", theme="monokai"),
                title=f"Diff for {file_path.name}",
                border_style="yellow"
            ))
        else:
            print("\n" + "="*80)
            print(f"Diff for {file_path}:")
            print("="*80)
            print(''.join(diff))
            print("="*80 + "\n")
    else:
        print_success(f"No changes detected for {file_path.name}")


def create_backup(file_path: Path) -> Path:
    """Create timestamped backup of existing file."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = file_path.parent / f"{file_path.name}.backup.{timestamp}"
    
    try:
        shutil.copy2(file_path, backup_path)
        print_success(f"Created backup: {backup_path.name}")
        return backup_path
    except Exception as e:
        print_error(f"Failed to create backup: {e}")
        return file_path


def generate_agents_md(project_path: Path) -> str:
    """Generate AGENTS.md content when both folders exist."""
    # Check if commands exist
    cursor_commands = project_path / '.cursor' / 'commands'
    claude_commands = project_path / '.claude' / 'commands'
    has_commands = cursor_commands.exists() or claude_commands.exists()
    
    commands_section = ""
    if has_commands:
        commands_section = """
## Shared Commands

**Commands are shared between both agents** - they use the same format (markdown files) and are available in both:
- `.cursor/commands/` - For Cursor
- `.claude/commands/` - For Claude Code

**Note:** When both `.cursor` and `.claude` folders are present, commands are automatically synced to both locations to ensure consistency.
"""
    
    return f"""# AGENTS

## Cursor Agent

- **Rules:** `.cursor/rules/` - Folder-based format with `RULE.md` files
- **Commands:** `.cursor/commands/` - Slash command definitions (`.md` files)
- Format: Rules use YAML frontmatter with `description`, `globs`, `alwaysApply`
- Used by Cursor for context attachments based on file patterns, manual invocations, etc.

## Claude Agent

- **Skills:** `.claude/skills/` - Each Skill is a folder with `SKILL.md` file
- **Commands:** `.claude/commands/` - Slash command definitions (`.md` files)
- Required fields: `name`, `description` (in SKILL.md frontmatter)
- Optional fields: `allowed-tools`, `model`, etc.
- Description is used to trigger skill usage; instructions in markdown content
{commands_section}
## Shared Guidelines

- Ensure rule/skill names are consistent and descriptive
- Keep Skill frontmatter descriptions aligned with Cursor rule descriptions
- Examples should be preserved across formats where relevant
- Where behavior differs (e.g. automatic vs explicit invocation), clarify in instructions
- Commands are shared between both agents - keep them in sync

## Migration

To migrate between formats, use the rule-migration-agent:
- Cursor → Claude: Converts `.cursor/rules/*/RULE.md` to `.claude/skills/*/SKILL.md`
- Claude → Cursor: Converts `.claude/skills/*/SKILL.md` to `.cursor/rules/*/RULE.md`
- Commands: Automatically synced to both `.cursor/commands/` and `.claude/commands/` when both agents are present
"""


def fetch_documentation(url: str, cache_key: str, use_cache: bool = True, doc_cache: Optional[DocumentationCache] = None) -> Optional[str]:
    """Fetch documentation from URL with improved error handling and caching."""
    # Check persistent cache first if available
    if use_cache and doc_cache and MEMORY_AVAILABLE:
            cached_content = doc_cache.get_cached_doc(cache_key, ttl_hours=24)
            if cached_content:
                DOCS_CACHE[cache_key] = cached_content
                print_success(f"Using cached documentation for {cache_key}")
                return cached_content
    
    # Check in-memory cache
    if use_cache and cache_key in DOCS_CACHE:
        return DOCS_CACHE[cache_key]
    
    # Try using requests library if available (better SSL handling)
    if REQUESTS_AVAILABLE:
        try:
            print_info(f"📥 Fetching latest documentation from {url}...")
            
            # Create session with retry strategy
            session = requests.Session()
            retry_strategy = Retry(
                total=3,
                backoff_factor=1,
                status_forcelist=[429, 500, 502, 503, 504],
            )
            adapter = HTTPAdapter(max_retries=retry_strategy)
            session.mount("http://", adapter)
            session.mount("https://", adapter)
            
            response = session.get(url, timeout=10, verify=True)
            response.raise_for_status()
            content = response.text
            
            # Try to parse HTML if BeautifulSoup is available
            if BS4_AVAILABLE:
                soup = BeautifulSoup(content, 'html.parser')
                # Extract main content (simplified - can be enhanced)
                main_content = soup.find('main') or soup.find('article') or soup
                if main_content:
                    content = main_content.get_text(separator='\n', strip=True)
            
            DOCS_CACHE[cache_key] = content
            if doc_cache and MEMORY_AVAILABLE:
                doc_cache.cache_doc(cache_key, content, ttl_hours=24, url=url)
            print_success("Fetched documentation successfully")
            return content
            
        except requests.exceptions.SSLError as e:
            print_warning(f"SSL error: {e}")
            print_warning("   ⚠️  SSL verification failed. Continuing without verification is insecure.")
            
            # Ask for user consent (non-interactive mode will fail)
            try:
                if console:
                    response = console.input("[yellow]Continue without SSL verification? (yes/no): [/yellow]")
                else:
                    response = input("Continue without SSL verification? (yes/no): ")
                
                if response.lower() not in ['yes', 'y']:
                    print_error("SSL verification required. Aborting.")
                    return None
            except (EOFError, KeyboardInterrupt):
                print_error("SSL verification required. Aborting.")
                return None
            
            try:
                print_warning("   Proceeding without SSL verification (insecure)...")
                response = requests.get(url, timeout=10, verify=False)
                response.raise_for_status()
                content = response.text
                DOCS_CACHE[cache_key] = content
                if doc_cache and MEMORY_AVAILABLE:
                    doc_cache.cache_doc(cache_key, content, ttl_hours=24, url=url)
                print_success("Fetched documentation (without SSL verification)")
                return content
            except Exception as e2:
                print_error(f"Failed to fetch: {e2}")
                return None
                
        except requests.exceptions.RequestException as e:
            print_warning(f"Could not fetch documentation: {e}")
            return None
    
    # Fallback to urllib
    try:
        print_info(f"📥 Fetching latest documentation from {url}...")
        with urlopen(url, timeout=10) as response:
            content = response.read().decode('utf-8')
            DOCS_CACHE[cache_key] = content
            if doc_cache and MEMORY_AVAILABLE:
                doc_cache.cache_doc(cache_key, content, ttl_hours=24, url=url)
            print_success("Fetched documentation successfully")
            return content
    except URLError as e:
        print_warning(f"Could not fetch documentation from {url}: {e}")
        print_warning("   Continuing with known format specifications...")
        return None
    except Exception as e:
        print_warning(f"Error fetching documentation: {e}")
        return None
