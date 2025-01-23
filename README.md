# url2md

Convert webpage content to well-structured Markdown files. Supports dynamic content, multi-file generation, and modern web technologies.

## Features

- **Multi-file Generation**
  - Automatically split content into separate files based on H1 headings
  - Smart filename generation from headings
  - Maintains content hierarchy

- **Modern Web Support**
  - Handles JavaScript-rendered content (SPA, Next.js, React, Vue)
  - Supports HTML5 semantic elements and ARIA roles
  - Processes dynamic loading and lazy content

- **Advanced Formatting**
  - Preserves code blocks with language detection
  - Handles complex tables and nested lists
  - Downloads and processes images

- **Output Management**
  - Organized storage in date-based folders
  - Auto-generated table of contents
  - Content integrity verification via checksums

## Installation

```bash
pip install url2md
```

For development installation:

```bash
git clone https://github.com/yourusername/url2md.git
cd url2md
pip install -e ".[dev]"
```

## Usage

### Basic Usage

Convert a single URL:

```bash
url2md https://example.com
```

Convert multiple URLs:

```bash
url2md https://example.com https://another-site.com
```

### Advanced Options

Specify output directory:

```bash
url2md -o ./my-docs https://example.com
```

Use custom configuration:

```bash
url2md -c my-config.yml https://example.com
```

Enable verbose output:

```bash
url2md -v https://example.com
```

### Configuration

url2md can be configured via YAML file. Create `.url2mdrc` in your project directory:

```yaml
output_directory: ./docs
verbose: false

html:
  js_render:
    enabled: true
    timeout: 20
  content:
    remove_selectors:
      - .advertisement
      - .cookie-notice
```

See [.url2mdrc](.url2mdrc) for full configuration options.

## Examples

Convert API documentation:

```bash
url2md https://api.example.com/docs
```

Output:
```
docs/
├── 2024-01-23/
│   ├── introduction.md
│   ├── authentication.md
│   ├── endpoints.md
│   └── README.md
```

## Development

### Setup Development Environment

1. Create virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # Linux/Mac
   venv\Scripts\activate     # Windows
   ```

2. Install development dependencies:
   ```bash
   pip install -r requirements/dev.txt
   ```

3. Install pre-commit hooks:
   ```bash
   pre-commit install
   ```

### Running Tests

```bash
pytest
pytest --cov=url2md
```

### Code Style

This project uses:
- Black for code formatting
- isort for import sorting
- flake8 for linting
- mypy for type checking

Run all checks:

```bash
black src/
isort src/
flake8 src/
mypy src/
```

## Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Run tests and style checks
4. Commit your changes (`git commit -m 'Add amazing feature'`)
5. Push to the branch (`git push origin feature/amazing-feature`)
6. Open a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- [BeautifulSoup4](https://www.crummy.com/software/BeautifulSoup/) for HTML parsing
- [Requests-HTML](https://github.com/psf/requests-html) for JavaScript rendering
- [Rich](https://github.com/Textualize/rich) for beautiful terminal output
- [Typer](https://typer.tiangolo.com/) for CLI interface