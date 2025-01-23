"""Utility for splitting and saving HTML content."""
import re
from pathlib import Path
from typing import List
from datetime import datetime
from bs4 import BeautifulSoup

class HtmlSplitter:
    """Split HTML content and save to files."""
    
    def __init__(self, output_dir: Path):
        """Initialize splitter with output directory.
        
        Args:
            output_dir: Base output directory
        """
        self.output_dir = output_dir
        self.html_dir = output_dir / 'html'
        self.html_dir.mkdir(parents=True, exist_ok=True)
        
    def split_and_save(self, html: str) -> List[Path]:
        """Split HTML by H1 tags and save to files.
        
        Args:
            html: HTML content to split
            
        Returns:
            List[Path]: Paths to saved HTML files
        """
        soup = BeautifulSoup(html, 'html.parser')
        h1_tags = soup.find_all('h1')
        file_paths = []
        
        for i, h1 in enumerate(h1_tags):
            # Get section content
            section = []
            next_element = h1
            while next_element:
                section.append(str(next_element))
                next_element = next_element.find_next_sibling()
                if next_element and next_element.name == 'h1':
                    break
                    
            # Create filename
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            title = re.sub(r'[^\w\-_]', '_', h1.text.strip())[:50]
            filename = f"{i+1:02d}_{title}_{timestamp}.html"
            file_path = self.html_dir / filename
            
            # Save HTML
            with open(file_path, 'w') as f:
                f.write('\n'.join(section))
            file_paths.append(file_path)
            
        return file_paths