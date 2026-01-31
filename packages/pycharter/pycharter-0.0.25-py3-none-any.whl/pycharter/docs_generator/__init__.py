"""
Documentation Generator - Generate documentation from data contracts.

This module provides tools to generate human-readable documentation
from ContractMetadata objects, supporting multiple output formats.

Primary Interface:
    - DocsGenerator: Main class for generating documentation
    - generate_docs: Convenience function for quick documentation generation

Renderers:
    - MarkdownRenderer: Render documentation as Markdown
    - HTMLRenderer: Render documentation as HTML

Example:
    >>> from pycharter import parse_contract_file
    >>> from pycharter.docs_generator import generate_docs, DocsGenerator
    >>>
    >>> # Quick generation
    >>> contract = parse_contract_file("contract.yaml")
    >>> markdown = generate_docs(contract)
    >>>
    >>> # Custom configuration
    >>> generator = DocsGenerator(renderer=HTMLRenderer())
    >>> html = generator.generate(contract)
"""

from pycharter.docs_generator.generator import DocsGenerator, generate_docs
from pycharter.docs_generator.renderers import (
    DocsRenderer,
    HTMLRenderer,
    MarkdownRenderer,
)

__all__ = [
    # Primary interface
    "DocsGenerator",
    "generate_docs",
    # Renderers
    "DocsRenderer",
    "MarkdownRenderer",
    "HTMLRenderer",
]
