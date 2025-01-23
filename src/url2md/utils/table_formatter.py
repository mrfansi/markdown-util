"""Improved table formatting utilities."""
import re
from typing import List

class TableFormatter:
    """Format HTML tables into clean Markdown tables."""
    
    def format_table(self, headers: List[str], rows: List[List[str]]) -> str:
        """Convert table data to formatted Markdown lists.
        
        Args:
            headers: List of header strings
            rows: List of row data (list of strings)
            
        Returns:
            str: Formatted Markdown lists
        """
        formatted_content = []
        
        # Convert each row to a list item
        for row in rows:
            item = []
            for i, cell in enumerate(row):
                header = headers[i] if i < len(headers) else f"Field {i+1}"
                cleaned_cell = self._clean_text(cell)
                item.append(f"- **{header}**: {cleaned_cell}")
            formatted_content.append("\n".join(item) + "\n")
            
        return "\n".join(formatted_content) + "\n"
        
    def _clean_text(self, text: str) -> str:
        """Clean and format table cell content.
        
        Args:
            text: Raw cell content
            
        Returns:
            str: Cleaned and formatted text
        """
        # Remove extra formatting
        text = re.sub(r'\*\*+', '', text)
        text = re.sub(r'\*+', '', text)
        
        # Handle required/optional
        if 'required' in text.lower():
            text = f'**{text.replace("required", "").strip()}** required'
        elif 'optional' in text.lower():
            text = f'*{text.replace("optional", "").strip()}* optional'
            
        # Normalize spacing and line breaks
        text = ' '.join(text.split())
        
        # Preserve code formatting
        text = re.sub(r'`([^`]+)`', r'`\1`', text)
        
        return text