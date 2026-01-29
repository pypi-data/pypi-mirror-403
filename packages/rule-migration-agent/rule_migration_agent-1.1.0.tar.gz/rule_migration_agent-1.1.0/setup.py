"""
Setup script for rule-migration-agent PyPI package.
"""

from setuptools import setup, find_packages
from pathlib import Path

# Read the README file
readme_file = Path(__file__).parent / "README.md"
long_description = readme_file.read_text(encoding="utf-8") if readme_file.exists() else ""

# Read requirements
requirements_file = Path(__file__).parent / "requirements.txt"
requirements = []
if requirements_file.exists():
    requirements = [
        line.strip()
        for line in requirements_file.read_text(encoding="utf-8").splitlines()
        if line.strip() and not line.startswith("#")
    ]

setup(
    name="rule-migration-agent",
    version="1.0.0",
    description="Bidirectional conversion tool for migrating between Cursor rules and Claude Skills",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="patrikmichi",
    author_email="",  # Add your email if desired
    url="https://github.com/patrikmichi/rule-migration-agent",
    license="MIT",
    python_requires=">=3.8",
    install_requires=requirements,
    packages=find_packages(exclude=["tests", "tests.*", "docs", "docs.*"]),
    py_modules=[
        "migrate",
        "converters",
        "parsers",
        "validation",
        "utils",
        "memory",
        "memory_commands",
        "config",
    ],
    entry_points={
        "console_scripts": [
            "rule-migration=migrate:main",
            "migrate-rules=migrate:main",
        ],
    },
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: Software Development :: Version Control",
        "Topic :: Text Processing :: Markup",
    ],
    keywords="cursor claude rules skills migration conversion ai agent",
    project_urls={
        "Bug Reports": "https://github.com/patrikmichi/rule-migration-agent/issues",
        "Source": "https://github.com/patrikmichi/rule-migration-agent",
        "Documentation": "https://github.com/patrikmichi/rule-migration-agent#readme",
    },
)
