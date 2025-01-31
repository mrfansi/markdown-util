"""HTML content handler implementation."""
import asyncio
import re
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import aiohttp
from requests_html import AsyncHTMLSession

from bs4 import BeautifulSoup, Tag
from markdownify import MarkdownConverter
from requests_html import HTML

from url2md.handlers.base_handler import BaseHandler

class CustomMarkdownConverter(MarkdownConverter):
    """Custom markdown converter with enhanced formatting."""

    def convert_img(self, el: Tag, text: str, convert_as_inline: bool) -> str:
        """Convert img tags with alt text and title.

        Args:
            el: HTML image element
            text: Image text
            convert_as_inline: Whether to convert as inline element

        Returns:
            str: Markdown formatted image
        """
        alt = el.get('alt', '')
        title = el.get('title', '')
        src = el.get('src', '')

        if title:
            return f'![{alt}]({src} "{title}")'
        return f'![{alt}]({src})'

    def convert_table(self, el: Tag, text: str, convert_as_inline: bool) -> str:
        """Convert HTML tables to properly formatted Markdown tables.
        
        Args:
            el: HTML table element
            text: Table text
            convert_as_inline: Whether to convert as inline element
            
        Returns:
            str: Markdown formatted table
        """
        # Get table headers
        headers = []
        header_row = el.find('thead')
        if header_row:
            headers = [th.get_text().strip() for th in header_row.find_all('th')]
        else:
            # If no thead, use first row as headers
            first_row = el.find('tr')
            if first_row:
                headers = [th.get_text().strip() for th in first_row.find_all(['th', 'td'])]
        
        # Get table rows
        rows = []
        for row in el.find_all('tr'):
            cells = []
            for cell in row.find_all('td'):
                # Convert code elements
                for code in cell.find_all('code'):
                    code.string = f'`{code.get_text()}`'
                
                # Convert headers to bold
                for h in cell.find_all(['h4', 'h5', 'h6']):
                    h.string = f'**{h.get_text()}**'
                
                # Convert notes and important text
                for strong in cell.find_all('strong'):
                    strong.string = f'**{strong.get_text()}**'
                for em in cell.find_all('em'):
                    em.string = f'*{em.get_text()}*'
                
                # Convert lists first
                lists = []
                for ul in cell.find_all('ul'):
                    list_items = []
                    for li in ul.find_all('li'):
                        # Convert any nested code elements
                        for code in li.find_all('code'):
                            code.string = f'`{code.get_text()}`'
                        list_items.append(f"- {li.get_text().strip()}")
                    lists.append('\n'.join(list_items))
                    ul.decompose()  # Remove processed lists
                
                # Convert any remaining code elements
                for code in cell.find_all('code'):
                    code.string = f'`{code.get_text()}`'
                
                # Get base content
                content = cell.get_text().strip()
                
                # Add lists back with proper spacing
                if lists:
                    content = "{}\n\n{}".format(content, '\n\n'.join(lists))
                
                # Normalize checkmarks
                content = re.sub(r'[✔✓]', '✅', content)  # Convert checkmarks
                content = re.sub(r'[✗×]', '❌', content)  # Convert cross marks
                
                # Clean up formatting and convert to parameter table format
                # Handle header parameters with proper markdown
                content = re.sub(
                    r'-\s*\*\*(Header|Parameter|Body Parameter)\*\*:\s*\*?([^*]+)\*?\s*(`+)?(required|optional)',
                    r'- **\1:** `\4` - \2',
                    content
                )
                
                # Convert parameter lists to table rows
                content = re.sub(
                    r'-\s+\*\*(.+?)\*\*:\s*`(.+?)`\s+-\s+(.+?)(?=\n-|\n\n|$)',
                    r'|\1|\2|\3|',
                    content
                )
                content = ' '.join(content.split())
                
                cells.append(content)
            if cells:
                rows.append(cells)
        
        # If no headers, create generic ones
        if not headers:
            headers = [f'Column {i+1}' for i in range(len(rows[0]))]
        
        # Create markdown table
        table = []
        
        # Add headers
        table.append('| ' + ' | '.join(headers) + ' |')
        
        # Add separator with proper alignment
        alignments = []
        for header in headers:
            alignments.append('---:')  # Right align all columns by default
        table.append('| ' + ' | '.join(alignments) + ' |')
        
        # Use new table formatter
        from url2md.utils.table_formatter import TableFormatter
        formatter = TableFormatter()
        return formatter.format_table(headers, rows)
        
        # Clean up table formatting and spacing
        formatted_table = '\n'.join(table)
        formatted_table = formatted_table.replace('****', '')
        formatted_table = formatted_table.replace('**', '')
        formatted_table = formatted_table.replace('*', '')
        formatted_table = '\n\n'.join([line.strip() for line in formatted_table.split('\n')])
        return formatted_table + '\n\n'

    def convert_pre(self, el: Tag, text: str, convert_as_inline: bool) -> str:
        """Convert pre tags maintaining code blocks.

        Args:
            el: HTML pre element
            text: Code text
            convert_as_inline: Whether to convert as inline element

        Returns:
            str: Markdown formatted code block
        """
        code = el.find('code')
        lang = None
        
        if code:
            # Try to detect language from class or content
            classes = code.get('class', [])
            for cls in classes:
                if cls.startswith(('language-', 'lang-')):
                    lang = cls.replace('language-', '').replace('lang-', '')
                    break
                    
            # Detect language from code content
            if not lang and 'curl' in text:
                lang = 'curl'
            elif not lang and any(s in text for s in ['{', '}', 'JSON']):
                lang = 'json'

        # Format with proper code fences and language
        # Clean excessive backticks and normalize code formatting
        code_content = re.sub(r'`{3,}', '```', text.strip())  # Normalize 3+ backticks to triple
        code_content = re.sub(r'^[\-> ]+`', '`', code_content)  # Fix example header markers
        code_content = code_content.strip('`')  # Remove wrapping backticks
        return f'```{lang or ""}\n{code_content}\n```\n'

class HtmlHandler(BaseHandler):
    """Handler for converting HTML content to Markdown."""

    def __init__(
        self,
        url: str,
        output_dir: Path,
        config: Optional[Dict] = None,
        timeout: int = 30,
        wait: int = 0
    ) -> None:
        """Initialize HTML handler.

        Args:
            url: Source URL
            output_dir: Output directory
            config: Handler configuration
            timeout: Timeout in seconds for page rendering
            wait: Time in seconds to wait after page load
        """
        super().__init__(url, output_dir, config, timeout, wait)
        self.markdown_converter = CustomMarkdownConverter(
            heading_style="atx",
            bullets="-",
            code_language=""  # Let convert_pre handle language detection
        )

    async def fetch_content(self) -> None:
        """Fetch and render HTML content from URL."""
        timeout = aiohttp.ClientTimeout(total=self.timeout)
        # Create async session and fetch content
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.get(self.url) as response:
                html = await response.text()
                
                # Configure render options
                render_opts = self.config.get('js_render', {})
                scroll = render_opts.get('scroll', False)
                
                # Use BeautifulSoup to parse HTML
                soup = BeautifulSoup(html, 'html.parser')
                
                # Handle JavaScript rendering if needed
                if render_opts.get('render_js', False):
                    from pyppeteer import launch
                    browser = await launch(headless=True)
                    page = await browser.newPage()
                    await page.goto(self.url, {
                        'waitUntil': 'networkidle2',
                        'timeout': self.timeout * 1000
                    })
                    if scroll:
                        await page.evaluate('window.scrollTo(0, document.body.scrollHeight)')
                    self.content = await page.content()
                    await browser.close()
                else:
                    self.content = str(soup)

    async def convert(self) -> List[Path]:
        """Convert HTML content to Markdown files.

        Returns:
            List[Path]: Generated markdown files
        """
        if not self.content:
            raise ValueError("No content to convert. Call fetch_content() first.")

        # Parse HTML
        soup = BeautifulSoup(self.content, 'html.parser')
        
        # Remove unwanted elements based on config
        remove_selectors = self.config.get('content', {}).get('remove_selectors', [])
        for selector in remove_selectors:
            for element in soup.select(selector):
                element.decompose()

        # Split content by H1 headings
        sections = self._split_by_h1(soup)
        
        # Convert and save each section
        output_files = []
        for title, content in sections:
            # Convert section to markdown
            markdown = self.markdown_converter.convert(str(content))
            
            # Clean up markdown
            markdown = self._clean_markdown(markdown)
            
            # Save to file
            filename = self._sanitize_filename(title)
            output_file = self.output_dir / f"{filename}.md"
            output_file.write_text(markdown)
            output_files.append(output_file)

        return output_files

    def _split_by_h1(self, soup: BeautifulSoup) -> List[Tuple[str, Tag]]:
        """Split content by H1 headings.

        Args:
            soup: BeautifulSoup parsed HTML

        Returns:
            List[Tuple[str, Tag]]: List of (title, content) tuples
        """
        # If no body tag exists, wrap content in one
        if not soup.body:
            body = soup.new_tag('body')
            for element in list(soup.children):
                body.append(element)
            soup.append(body)
            soup = BeautifulSoup(str(soup), 'html.parser')

        sections = []
        current_title = "index"
        current_content = Tag(name="div")

        for element in soup.body.children:
            if isinstance(element, Tag):
                if element.name == 'h1':
                    # Save current section if it has content
                    if current_content.contents:
                        sections.append((current_title, current_content))
                    # Start new section
                    current_title = element.get_text().strip()
                    current_content = Tag(name="div")
                    current_content.append(element)
                else:
                    current_content.append(element)

        # Add last section
        if current_content.contents:
            sections.append((current_title, current_content))
        
        # If no sections were created, use whole body as one section
        if not sections:
            sections = [("index", soup.body)]

        return sections

    def _clean_markdown(self, markdown: str) -> str:
        """Clean up converted markdown content.

        Args:
            markdown: Raw markdown content

        Returns:
            str: Cleaned markdown content
        """
        # Ensure proper spacing around headings
        markdown = re.sub(r'(\n#+\s.*?)(\n(?!\n))', r'\1\n\n\2', markdown)
        
        # Ensure proper list spacing
        markdown = re.sub(r'(\n-\s.*?)(\n(?!\n))', r'\1\n\n\2', markdown)
        
        # Ensure proper code block spacing
        markdown = re.sub(r'(```.*?\n.*?```)', lambda m: f"\n\n{m.group(1)}\n\n", markdown, flags=re.DOTALL)
        
        # Fix bold and italic formatting
        markdown = re.sub(r'<strong>([^<]+)</strong>', r'**\1**', markdown)  # Convert strong to bold
        markdown = re.sub(r'<em>([^<]+)</em>', r'*\1*', markdown)  # Convert em to italic using asterisks
        
        # Add extra newline after headings, lists and code blocks
        markdown = re.sub(r'(#+\s.*?\n)', r'\1\n\n', markdown)
        markdown = re.sub(r'(-\s.*?\n)', r'\1\n\n', markdown)
        markdown = re.sub(r'(```.*?```\n)', r'\1\n\n\n', markdown, flags=re.DOTALL)
        
        # Add extra newlines after headings and code blocks
        markdown = re.sub(r'(#+\s.*?\n)', r'\1\n\n', markdown)
        markdown = re.sub(r'(```.*?```\n)', r'\1\n\n', markdown, flags=re.DOTALL)
        
        # Remove excessive blank lines but maintain structure
        markdown = re.sub(r'\n{4,}', '\n\n', markdown)
        
        return markdown.strip()
