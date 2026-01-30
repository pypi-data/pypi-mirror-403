"""
Pytest fixtures for Qodacode tests.
"""

import pytest
import tree_sitter_python
import tree_sitter_javascript
import tree_sitter_typescript
import tree_sitter


@pytest.fixture
def python_parser():
    """Create a Python Tree-sitter parser."""
    language = tree_sitter.Language(tree_sitter_python.language())
    parser = tree_sitter.Parser(language)
    return parser


@pytest.fixture
def javascript_parser():
    """Create a JavaScript Tree-sitter parser."""
    language = tree_sitter.Language(tree_sitter_javascript.language())
    parser = tree_sitter.Parser(language)
    return parser


@pytest.fixture
def typescript_parser():
    """Create a TypeScript Tree-sitter parser."""
    language = tree_sitter.Language(tree_sitter_typescript.language_typescript())
    parser = tree_sitter.Parser(language)
    return parser


def parse_python(parser, code: str):
    """Parse Python code and return tree + source bytes."""
    source = code.encode("utf-8")
    tree = parser.parse(source)
    return tree, source


def parse_javascript(parser, code: str):
    """Parse JavaScript code and return tree + source bytes."""
    source = code.encode("utf-8")
    tree = parser.parse(source)
    return tree, source
