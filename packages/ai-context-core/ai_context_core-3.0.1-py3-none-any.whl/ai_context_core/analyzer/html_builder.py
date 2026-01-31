"""HTML generation utilities for ai-context-core reporting."""

import string
import time
from typing import List


class HTMLBuilder:
    """Helper class for building HTML documents using string.Template."""

    CSS = """
    body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif; line-height: 1.6; color: #333; max-width: 900px; margin: 0 auto; padding: 20px; background: #f4f6f9; }
    h1 { color: #2c3e50; border-bottom: 2px solid #3498db; padding-bottom: 10px; }
    h2 { color: #2c3e50; margin-top: 30px; border-left: 4px solid #3498db; padding-left: 10px; }
    h3 { color: #34495e; }
    .card { background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); margin-bottom: 20px; }
    .metric { display: inline-block; margin-right: 20px; font-weight: bold; }
    .metric-value { color: #2980b9; }
    ul { list-style-type: none; padding: 0; }
    li { padding: 5px 0; border-bottom: 1px solid #eee; }
    li:last-child { border-bottom: none; }
    .mermaid { text-align: center; overflow-x: auto; background: white; padding: 20px; }
    """

    TEMPLATE = string.Template(
        "<!DOCTYPE html><html><head><meta charset='UTF-8'><meta name='viewport' content='width=device-width, initial-scale=1.0'>"
        "<title>$title</title><style>$css</style><script type='module'>"
        "import mermaid from 'https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.esm.min.mjs';"
        "mermaid.initialize({ startOnLoad: true });"
        "</script></head><body><h1>$title</h1><div class='card'><p><strong>Date:</strong> $date</p>"
        "<p><strong>Version:</strong> 2.0 (Ai-Context-Core)</p></div>$content</body></html>"
    )

    def __init__(self, title: str):
        """Initialize the builder.

        Args:
            title: The title of the HTML document.
        """
        self.title = title
        self.content_parts = []

    def add_section(self, title: str, content: str):
        """Adds a section to the HTML document.

        Args:
            title: Section title.
            content: HTML content for the section.
        """
        self.content_parts.append(f'<div class="card"><h2>{title}</h2>{content}</div>')

    def build_list(self, items: List[str]) -> str:
        """Constructs an HTML unordered list from a list of strings.

        Args:
            items: List of strings to format.

        Returns:
            HTML string representing the list.
        """
        if not items:
            return ""
        return "<ul>" + "".join(f"<li>{i}</li>" for i in items) + "</ul>"

    def render(self) -> str:
        """Renders the HTML document.

        Returns:
            Complete HTML string.
        """
        return self.TEMPLATE.substitute(
            title=self.title,
            css=self.CSS,
            date=time.strftime("%Y-%m-%d %H:%M:%S"),
            content="\n".join(self.content_parts),
        )
