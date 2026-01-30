# CDL Language Server

A Language Server Protocol (LSP) implementation for the Crystal Description Language (CDL).

Part of the [Gemmology Project](https://gemmology.dev).

## Features

- **Diagnostics**: Real-time error detection and warnings
- **Completion**: Context-aware autocomplete for systems, point groups, forms, and modifications
- **Hover**: Documentation on hover for CDL elements
- **Go to Definition**: Navigate to symbol definitions
- **Formatting**: Automatic CDL formatting
- **Code Actions**: Quick fixes for common errors
- **Document Symbols**: Outline view of CDL documents
- **Signature Help**: Parameter hints for modifications

## Installation

```bash
pip install cdl-lsp
```

### Dependencies

The package requires:
- `cdl-parser>=1.0.0` - CDL parsing library
- `pygls>=1.0.0` - Python language server framework
- `lsprotocol>=2023.0.0` - LSP type definitions

## Usage

### From Command Line

```bash
# Standard I/O mode (default)
cdl-lsp

# TCP mode
cdl-lsp --tcp --host 127.0.0.1 --port 2087

# With logging
cdl-lsp --log-file /tmp/cdl-lsp.log --log-level DEBUG
```

### From Python

```python
from cdl_lsp import create_server

server = create_server()
server.start_io()  # or server.start_tcp(host, port)
```

## Editor Integration

### VS Code

Install the CDL extension from the VS Code marketplace, or configure manually:

```json
{
  "cdl.server.path": "cdl-lsp"
}
```

### Neovim (nvim-lspconfig)

```lua
require('lspconfig').cdl_lsp.setup{
  cmd = {'cdl-lsp'},
  filetypes = {'cdl'},
}
```

### Sublime Text (LSP)

Add to LSP settings:

```json
{
  "clients": {
    "cdl": {
      "command": ["cdl-lsp"],
      "selector": "source.cdl"
    }
  }
}
```

## CDL Syntax Overview

The Crystal Description Language describes crystal morphologies:

```
# Basic forms
cubic[m3m]:{111}                     # Octahedron
cubic[m3m]:{100}                     # Cube

# Combined forms
cubic[m3m]:{111}@1.0 + {100}@1.3     # Truncated octahedron

# Named forms
cubic[m3m]:octahedron                # Same as {111}

# Modifications
cubic[m3m]:{111}|elongate(c:1.5)     # Elongated
cubic[m3m]:{111}|twin(spinel)        # Twinned

# Different crystal systems
hexagonal[6/mmm]:{10-10}@1.0 + {0001}@0.5   # Hexagonal prism
trigonal[-3m]:{10-11}                       # Rhombohedron
```

## API Reference

### Constants

```python
from cdl_lsp.constants import (
    CRYSTAL_SYSTEMS,      # Set of crystal system names
    POINT_GROUPS,         # Dict mapping system to point groups
    ALL_POINT_GROUPS,     # Set of all 32 point groups
    TWIN_LAWS,            # Set of twin law names
    NAMED_FORMS,          # Dict mapping form names to Miller indices
    MODIFICATIONS,        # Set of modification names
)
```

### Server

The LSP server handles all features internally. Use the server module to start the language server:

```python
from cdl_lsp import create_server, SERVER_NAME, SERVER_VERSION

server = create_server()
print(f"Running {SERVER_NAME} v{SERVER_VERSION}")
server.start_io()  # or server.start_tcp(host, port)
```

## Development

### Setup

```bash
git clone https://github.com/gemmology-dev/cdl-lsp
cd cdl-lsp
pip install -e ".[dev]"
```

### Testing

```bash
pytest tests/ -v
```

### Linting

```bash
ruff check src/
mypy src/
```

## License

MIT License - see [LICENSE](LICENSE) for details.

## Links

- [Documentation](https://cdl-lsp.gemmology.dev/docs)
- [CDL Specification](https://gemmology.dev/cdl)
- [GitHub Repository](https://github.com/gemmology-dev/cdl-lsp)
- [Issue Tracker](https://github.com/gemmology-dev/cdl-lsp/issues)
