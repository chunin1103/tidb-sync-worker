"""
Markdown Parser with Mermaid Support

Parses markdown files from the wiki and converts them to HTML while:
- Preserving Mermaid diagrams (extract before parsing, restore after)
- Converting relative links to absolute /wiki paths
- Adding section IDs to headings for linking
- Generating table of contents
- Extracting preview text for tooltips
"""

import re
import os
import markdown
from markdown.extensions import fenced_code, tables, toc


class WikiMarkdownParser:
    """Parse markdown with Mermaid support and link conversion"""

    def __init__(self, wiki_root_path):
        """
        Initialize parser with wiki root directory

        Args:
            wiki_root_path: Absolute path to Production/wiki folder
        """
        self.wiki_root = wiki_root_path
        self.md = markdown.Markdown(extensions=[
            'fenced_code',
            'tables',
            'toc',
            'attr_list',  # For {#id} syntax
        ])

    def parse(self, content, current_file_path):
        """
        Parse markdown to HTML with Mermaid preservation and link conversion

        Args:
            content: Raw markdown content
            current_file_path: Relative path to current file (e.g., "03_Decision_Workflows/file.md")

        Returns:
            dict with keys:
                - html: Converted HTML
                - toc: Table of contents HTML
                - diagram_count: Number of Mermaid diagrams found
        """
        # Step 1: Extract Mermaid blocks (preserve as-is)
        mermaid_blocks = []

        def extract_mermaid(match):
            index = len(mermaid_blocks)
            mermaid_blocks.append(match.group(0))
            return f"MERMAID_PLACEHOLDER_{index}"

        content = re.sub(
            r'```mermaid\n(.*?)```',
            extract_mermaid,
            content,
            flags=re.DOTALL
        )

        # Step 2: Convert markdown to HTML
        html = self.md.convert(content)

        # Step 3: Restore Mermaid blocks with wrapper div
        for i, block in enumerate(mermaid_blocks):
            placeholder = f"MERMAID_PLACEHOLDER_{i}"
            # Extract Mermaid content (without backticks)
            mermaid_content = re.search(r'```mermaid\n(.*?)```', block, re.DOTALL).group(1)
            diagram_id = f"diagram_{i}"
            mermaid_html = f'<div class="mermaid" data-diagram-id="{diagram_id}">\n{mermaid_content}\n</div>'
            html = html.replace(placeholder, mermaid_html)

        # Step 4: Convert relative links to absolute /wiki/ paths
        html = self._convert_links(html, current_file_path)

        # Step 5: Add section IDs to headings for linking
        html = self._add_section_ids(html)

        # Reset markdown instance for next parse (clears TOC)
        toc_html = self.md.toc
        self.md.reset()

        return {
            'html': html,
            'toc': toc_html,
            'diagram_count': len(mermaid_blocks)
        }

    def _convert_links(self, html, current_path):
        """
        Convert relative markdown links to absolute /wiki/ paths

        Args:
            html: HTML content with links
            current_path: Current file's relative path

        Returns:
            HTML with converted links
        """
        def replace_link(match):
            original_href = match.group(1)

            # Skip external links (http/https)
            if original_href.startswith(('http://', 'https://')):
                return match.group(0)

            # Skip anchors (#section)
            if original_href.startswith('#'):
                return match.group(0)

            # Resolve relative path
            current_dir = os.path.dirname(current_path)
            absolute_path = os.path.normpath(os.path.join(current_dir, original_href))

            # Convert Windows backslashes to forward slashes for URLs
            absolute_path = absolute_path.replace('\\', '/')

            # Remove .md extension for cleaner URLs
            if absolute_path.endswith('.md'):
                absolute_path = absolute_path[:-3]

            return f'href="/wiki/view/{absolute_path}"'

        return re.sub(r'href="([^"]+)"', replace_link, html)

    def _add_section_ids(self, html):
        """
        Add IDs to headings for section linking

        Converts:
            <h2>Step 1: Load & Snapshot</h2>
        To:
            <h2 id="step-1-load-snapshot" data-section-id="step-1-load-snapshot">Step 1: Load & Snapshot</h2>

        Args:
            html: HTML content with headings

        Returns:
            HTML with heading IDs added
        """
        def add_id(match):
            level = match.group(1)
            title = match.group(2)

            # Generate ID from title (lowercase, replace non-alphanumeric with dashes)
            section_id = re.sub(r'[^a-z0-9]+', '-', title.lower()).strip('-')

            return f'<h{level} id="{section_id}" data-section-id="{section_id}">{title}</h{level}>'

        return re.sub(r'<h(\d)>(.*?)</h\1>', add_id, html)

    def extract_section_text(self, content, section_id, max_length=200):
        """
        Extract preview text for a section (for tooltips)

        Args:
            content: Raw markdown content
            section_id: Section ID to find (e.g., "step-1-load-snapshot")
            max_length: Maximum preview length in characters

        Returns:
            Preview text string, or None if section not found
        """
        # Parse markdown first
        result = self.parse(content, "")
        html = result['html']

        # Find section heading and extract next content
        pattern = f'<h\\d id="{section_id}"[^>]*>(.*?)</h\\d>(.*?)(?=<h\\d|$)'
        section_match = re.search(pattern, html, flags=re.DOTALL)

        if not section_match:
            return None

        # Extract text from next element (strip HTML tags)
        next_content = section_match.group(2)
        text = re.sub(r'<[^>]+>', '', next_content)

        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text).strip()

        # Truncate to max_length
        if len(text) > max_length:
            text = text[:max_length].rsplit(' ', 1)[0] + '...'

        return text
