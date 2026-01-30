# SlideGen

AI-powered slide generation library for PowerPoint. Generate professional presentations from YAML/JSON schemas using LLMs.

## Installation

### From PyPI (Recommended)

```bash
pip install slidegen-pptx
```

### From Source

```bash
git clone https://github.com/nicolairobles/slidegen.git
cd slidegen
pip install -e .
```

## Quick Start

### 1. Create a Presentation Schema

Create a YAML file describing your presentation:

```yaml
presentation:
  title: "My Presentation"
  slides:
    - layout: title
      title: "Welcome"
      subtitle: "Introduction"
    
    - layout: bullet_list
      title: "Key Points"
      bullets:
        - "Point 1"
        - "Point 2"
```

### 2. Validate the Schema

```bash
slidegen validate presentation.yaml
```

### 3. Generate PowerPoint

```bash
slidegen build presentation.yaml -o output.pptx
```

## Features

- 🎨 **10 Layout Types**: Title, bullet lists, two-column, comparison, charts, tables, images, quotes, section headers, and blank slides
- 🤖 **AI-Powered**: Generate schemas from natural language using LLMs (OpenAI, DeepSeek)
- ✅ **Schema Validation**: Comprehensive validation with helpful error messages
- 🎨 **Theming**: Support for custom themes and styling
- 📊 **Data Binding**: Connect charts and tables to CSV/JSON data sources
- 🚀 **CLI Tool**: Simple command-line interface for quick generation

## Documentation

Full documentation is available at: https://nicolairobles.github.io/slidegen/

## Example Schemas

See the `examples/` directory for complete examples:
- Corporate quarterly results
- Client proposals
- Product roadmaps
- Technical analysis
- Educational content

## Development

```bash
# Install with dev dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Run type checking
mypy slidegen/

# Run linting
ruff check slidegen/
```

## Contributing

Contributions are welcome! Please see our [Contributing Guide](https://nicolairobles.github.io/slidegen/contributing/guide/) for details.

## License

MIT License - see [LICENSE](LICENSE) file for details.

## Links

- **Documentation**: https://nicolairobles.github.io/slidegen/
- **GitHub**: https://github.com/nicolairobles/slidegen
- **Issues**: https://github.com/nicolairobles/slidegen/issues

