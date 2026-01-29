"""Vue Single File Component parser."""

import re
from pathlib import Path

from .base import BaseParser, ImportInfo
from .js_parser import JsParser


class VueParser(BaseParser):
    """Parser for Vue SFC files."""

    supported_extensions = [".vue"]

    def __init__(self):
        self._js_parser = JsParser()

    def parse(self, content: str, file_path: Path) -> list[ImportInfo]:
        """Parse Vue SFC and extract imports from script block."""
        imports: list[ImportInfo] = []

        # Extract all script blocks (including setup scripts)
        script_blocks = self._extract_script_blocks(content)

        for script_content, lang, start_line in script_blocks:
            if not script_content.strip():
                continue

            # Create a temporary path with appropriate extension
            if lang in ("ts", "typescript"):
                temp_path = file_path.with_suffix(".ts")
            else:
                temp_path = file_path.with_suffix(".js")

            # Parse using JS/TS parser
            block_imports = self._js_parser.parse(script_content, temp_path)

            # Adjust line numbers based on script block position
            for imp in block_imports:
                imp.line += start_line
                imports.append(imp)

        return imports

    def _extract_script_blocks(
        self, content: str
    ) -> list[tuple[str, str, int]]:
        """
        Extract script blocks from Vue SFC.

        Returns:
            List of (script_content, language, start_line) tuples
        """
        blocks: list[tuple[str, str, int]] = []

        # Pattern to match <script> tags with optional lang and setup attributes
        # Handles: <script>, <script setup>, <script lang="ts">, <script setup lang="ts">
        pattern = re.compile(
            r'<script\s*'
            r'(?:setup\s*)?'
            r'(?:lang=["\']?(ts|typescript|js|javascript)["\']?\s*)?'
            r'(?:setup\s*)?'
            r'[^>]*>'
            r'(.*?)'
            r'</script>',
            re.DOTALL | re.IGNORECASE
        )

        for match in pattern.finditer(content):
            lang_match = match.group(1)
            script_content = match.group(2)

            # Determine language
            if lang_match and lang_match.lower() in ("ts", "typescript"):
                lang = "typescript"
            else:
                lang = "javascript"

            # Calculate start line of script content
            start_pos = match.start(2)
            start_line = content[:start_pos].count("\n")

            blocks.append((script_content, lang, start_line))

        return blocks
