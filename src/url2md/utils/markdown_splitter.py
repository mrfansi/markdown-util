"""Markdown content splitting utilities."""

import re
import os
from typing import List, Dict
from pathlib import Path
from urllib.parse import quote

from .sanitizer import FilenameNormalizer

class MarkdownSplitter:
    """Split Markdown content into multiple files based on H1 headings."""
    
    H1_PATTERN = re.compile(r'^#\s+(.+)$', re.MULTILINE)
    
    @classmethod
    def split_markdown(cls, content: str, output_dir: str) -> Dict[str, str]:
        """
        Split Markdown content into separate files based on H1 headings.
        
        Args:
            content: Markdown content to split
            output_dir: Directory to write split files
            
        Returns:
            Dictionary mapping filenames to their content
            
        Raises:
            ValueError: If no H1 headings found or invalid Markdown
        """
        if not content.strip():
            raise ValueError("Empty Markdown content")
            
        h1_matches = list(cls.H1_PATTERN.finditer(content))
        if not h1_matches:
            raise ValueError("No H1 headings found in Markdown content")
            
        split_files = {}
        start_idx = 0
        
        for i, match in enumerate(h1_matches):
            heading = match.group(1).strip()
            sanitized_name = FilenameNormalizer.normalize_filename(heading)
            filename = f"{sanitized_name}.md"
            
            # Get content between current and next heading
            end_idx = h1_matches[i+1].start() if i+1 < len(h1_matches) else len(content)
            file_content = content[match.start():end_idx].strip()
            
            # Write to output directory
            output_path = Path(output_dir) / filename
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(file_content)
                
            split_files[filename] = file_content
            
        return split_files