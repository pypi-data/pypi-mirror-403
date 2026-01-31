### Leaflet-to-Zoommap Converter

This repository contains a Python CLI tool to parse Obsidian Vaults and convert Leaflet codeblocks to Zoommap ([TTRPG Tools: Maps](https://github.com/Jareika/zoom-map)) format, supporting map scales, icons and shapes.

## Overview

ZoomMap Converter is designed to facilitate the migration from the Obsidian Leaflet plugin to the ZoomMap plugin. It handles the conversion of map notes, markers, and configurations while maintaining compatibility with Obsidian vault structures.

## Features

- **Note Conversion**: Converts Leaflet-formatted codeblocks to ZoomMap format.
- **Icon Processing**: Transforms custom SVG icons with color and size normalisation over to Zoommap.
- **Error Handling**: Validation and logging for troubleshooting.
- **Path Management**: Handles Obsidian vault file paths and structures.

## Installation

### Prerequisites

- Python 3.12+
- Obsidian vault with Leaflet plugin notes
- Leaflet Plug-In installed and enabled.
- Zoommap Plug-In installed and enabled.

### Setup

1. Download the CLI tool using `pip`.

```bash
pip install zoommap-converter
```

2. Once installed, you can test the install was successful using:

```bash
zoommap-converter --version
```


3. Configure the vault path in `settings.yaml` or via environment variables

## Usage

### Basic Conversion

```bash
python -m zoommap_converter --vault-path /path/to/obsidian/vault
```

### Advanced Options

```bash
python -m zoommap_converter \
    --vault-path /path/to/vault \
    --output-dir ./converted \
    --verbose
```

### Configuration

Create a `.zoommap/config.json` file in your vault for custom settings:

```json
{
    "defaultIconKey": "pinRed",
    "defaultWidth": "100%",
    "defaultHeight": "480px",
    "icons": [
        {
            "key": "customIcon",
            "pathOrDataUrl": "data:image/svg+xml;...",
            "size": 24
        }
    ]
}
```

## Development

### Project Structure

```
├── src
│   └── zoommap_converter
│       ├── __init__.py
│       ├── __main__.py
│       ├── app.py
│       ├── cli.py          # Command-line interface
│       ├── logs.py
│       ├── bootstrap/      # Initialisation and setup
│       ├── conf/           # Settings Config
│       ├── converter/      # Core conversion logic
│       └── models/         # Data models and schemas
tests/
```

### Developer Setup

1. Clone the repository:
   ```bash
   git clone https://codeberg.org/paddyd/zoommap-converter.git
   cd zoommap-converter
   ```

2. Install dependencies using `uv`:
   ```bash
   uv install
   ```

3. Configure the vault path in `settings.yaml` or via environment variables

### Running Tests

```bash
pytest tests
```

### Building

```bash
python -m build
```

## Contributing

Contributions are welcome. Please follow these guidelines:

1. Fork the repository
2. Create a feature branch
3. Submit a pull request with clear documentation
4. Include tests for new functionality

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For issues or questions, please open a GitHub issue.

## Acknowledgements

- Obsidian community for plugin development
- Font Awesome for icon assets
- Pydantic for data validation
