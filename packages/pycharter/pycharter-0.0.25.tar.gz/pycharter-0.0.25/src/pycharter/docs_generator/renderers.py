"""
Documentation Renderers - Output format implementations.

Provides Protocol definition and concrete implementations for
rendering documentation in various formats.
"""

from typing import Any, Dict, List, Optional, Protocol


class DocsRenderer(Protocol):
    """Protocol for documentation renderers."""

    def render_header(self, title: str, version: Optional[str] = None) -> str:
        """Render document header with title and optional version."""
        ...

    def render_section(self, title: str, content: str) -> str:
        """Render a section with title and content."""
        ...

    def render_table(
        self, headers: List[str], rows: List[List[str]], caption: Optional[str] = None
    ) -> str:
        """Render a table with headers and rows."""
        ...

    def render_code_block(self, code: str, language: str = "") -> str:
        """Render a code block."""
        ...

    def render_list(self, items: List[str], ordered: bool = False) -> str:
        """Render a list of items."""
        ...

    def render_description(self, text: str) -> str:
        """Render description/paragraph text."""
        ...

    def render_badge(self, label: str, value: str) -> str:
        """Render a badge/tag (e.g., required, optional)."""
        ...


class MarkdownRenderer:
    """Render documentation as Markdown."""

    def render_header(self, title: str, version: Optional[str] = None) -> str:
        """Render document header with title and optional version."""
        header = f"# {title}\n\n"
        if version:
            header += f"**Version:** `{version}`\n\n"
        return header

    def render_section(self, title: str, content: str) -> str:
        """Render a section with title and content."""
        return f"## {title}\n\n{content}\n\n"

    def render_subsection(self, title: str, content: str) -> str:
        """Render a subsection with title and content."""
        return f"### {title}\n\n{content}\n\n"

    def render_table(
        self, headers: List[str], rows: List[List[str]], caption: Optional[str] = None
    ) -> str:
        """Render a Markdown table."""
        if not headers or not rows:
            return ""

        lines = []
        if caption:
            lines.append(f"*{caption}*\n")

        # Header row
        lines.append("| " + " | ".join(headers) + " |")
        # Separator
        lines.append("| " + " | ".join(["---"] * len(headers)) + " |")
        # Data rows
        for row in rows:
            # Ensure row has same length as headers
            padded_row = row + [""] * (len(headers) - len(row))
            lines.append("| " + " | ".join(padded_row[: len(headers)]) + " |")

        return "\n".join(lines) + "\n"

    def render_code_block(self, code: str, language: str = "") -> str:
        """Render a fenced code block."""
        return f"```{language}\n{code}\n```\n"

    def render_list(self, items: List[str], ordered: bool = False) -> str:
        """Render a list of items."""
        if not items:
            return ""
        if ordered:
            return "\n".join(f"{i+1}. {item}" for i, item in enumerate(items)) + "\n"
        return "\n".join(f"- {item}" for item in items) + "\n"

    def render_description(self, text: str) -> str:
        """Render description/paragraph text."""
        return f"{text}\n\n"

    def render_badge(self, label: str, value: str) -> str:
        """Render a badge as inline code."""
        return f"`{label}: {value}`"

    def render_key_value(self, key: str, value: Any) -> str:
        """Render a key-value pair."""
        if isinstance(value, (dict, list)):
            return f"**{key}:**\n{self.render_code_block(str(value), 'json')}"
        return f"**{key}:** {value}\n"


class HTMLRenderer:
    """Render documentation as HTML."""

    def __init__(self, include_styles: bool = True):
        """
        Initialize HTML renderer.

        Args:
            include_styles: If True, include inline CSS styles
        """
        self.include_styles = include_styles

    def _get_styles(self) -> str:
        """Get CSS styles for HTML output."""
        return """
<style>
    body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; 
           line-height: 1.6; max-width: 900px; margin: 0 auto; padding: 20px; }
    h1 { border-bottom: 2px solid #333; padding-bottom: 10px; }
    h2 { border-bottom: 1px solid #ddd; padding-bottom: 5px; margin-top: 30px; }
    table { border-collapse: collapse; width: 100%; margin: 15px 0; }
    th, td { border: 1px solid #ddd; padding: 10px; text-align: left; }
    th { background: #f5f5f5; font-weight: 600; }
    tr:nth-child(even) { background: #fafafa; }
    code { background: #f4f4f4; padding: 2px 6px; border-radius: 3px; font-size: 0.9em; }
    pre { background: #f4f4f4; padding: 15px; border-radius: 5px; overflow-x: auto; }
    pre code { background: none; padding: 0; }
    .badge { display: inline-block; padding: 2px 8px; border-radius: 3px; 
             font-size: 0.8em; font-weight: 500; }
    .badge-required { background: #fee2e2; color: #991b1b; }
    .badge-optional { background: #e0f2fe; color: #0369a1; }
    .version { color: #666; font-size: 0.9em; }
</style>
"""

    def render_header(self, title: str, version: Optional[str] = None) -> str:
        """Render document header with title and optional version."""
        styles = self._get_styles() if self.include_styles else ""
        version_html = (
            f'<p class="version">Version: <code>{version}</code></p>'
            if version
            else ""
        )
        return f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>{title}</title>
    {styles}
</head>
<body>
<h1>{title}</h1>
{version_html}
"""

    def render_footer(self) -> str:
        """Render document footer."""
        return "</body>\n</html>"

    def render_section(self, title: str, content: str) -> str:
        """Render a section with title and content."""
        return f"<h2>{title}</h2>\n{content}\n"

    def render_subsection(self, title: str, content: str) -> str:
        """Render a subsection with title and content."""
        return f"<h3>{title}</h3>\n{content}\n"

    def render_table(
        self, headers: List[str], rows: List[List[str]], caption: Optional[str] = None
    ) -> str:
        """Render an HTML table."""
        if not headers or not rows:
            return ""

        lines = ["<table>"]
        if caption:
            lines.append(f"<caption>{caption}</caption>")

        # Header
        lines.append("<thead><tr>")
        for h in headers:
            lines.append(f"<th>{h}</th>")
        lines.append("</tr></thead>")

        # Body
        lines.append("<tbody>")
        for row in rows:
            lines.append("<tr>")
            for i, cell in enumerate(row):
                if i < len(headers):
                    lines.append(f"<td>{cell}</td>")
            # Pad if needed
            for _ in range(len(headers) - len(row)):
                lines.append("<td></td>")
            lines.append("</tr>")
        lines.append("</tbody>")
        lines.append("</table>")

        return "\n".join(lines) + "\n"

    def render_code_block(self, code: str, language: str = "") -> str:
        """Render a code block."""
        return f"<pre><code>{self._escape_html(code)}</code></pre>\n"

    def render_list(self, items: List[str], ordered: bool = False) -> str:
        """Render a list of items."""
        if not items:
            return ""
        tag = "ol" if ordered else "ul"
        items_html = "\n".join(f"<li>{item}</li>" for item in items)
        return f"<{tag}>\n{items_html}\n</{tag}>\n"

    def render_description(self, text: str) -> str:
        """Render description/paragraph text."""
        return f"<p>{text}</p>\n"

    def render_badge(self, label: str, value: str) -> str:
        """Render a badge span."""
        css_class = "badge-required" if value.lower() == "required" else "badge-optional"
        return f'<span class="badge {css_class}">{label}: {value}</span>'

    def render_key_value(self, key: str, value: Any) -> str:
        """Render a key-value pair."""
        if isinstance(value, (dict, list)):
            return f"<p><strong>{key}:</strong></p>\n{self.render_code_block(str(value), 'json')}"
        return f"<p><strong>{key}:</strong> {value}</p>\n"

    def _escape_html(self, text: str) -> str:
        """Escape HTML special characters."""
        return (
            text.replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
            .replace('"', "&quot;")
        )
