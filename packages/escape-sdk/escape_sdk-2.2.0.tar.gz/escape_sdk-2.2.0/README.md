# Escape SDK

Python SDK for OSRS bot development via RuneLite bridge.

## Requirements

- Python 3.12+
- Linux with inotify support
- RuneLite with Escape plugin

## Installation

```bash
pip install escape-sdk
```

## Development

```bash
# Clone and install
git clone https://github.com/OSEscape/escape_sdk.git
cd escape_sdk
uv sync --all-extras

# Commands
make test      # Run all checks (ruff, basedpyright, skylos, pytest)
make format    # Auto-format and fix linting issues
make clean     # Remove caches and build artifacts
make build     # Build distribution packages
```

## License

MIT
