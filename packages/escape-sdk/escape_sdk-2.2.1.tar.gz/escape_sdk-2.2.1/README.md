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
git clone https://github.com/OSEscape/escape_sdk.git
cd escape_sdk
uv sync --all-extras
pre-commit install
```

```bash
make test      # Run all checks (ruff, basedpyright, skylos, pytest)
make format    # Auto-format and fix linting issues
```

## Contributing

We use [Conventional Commits](https://www.conventionalcommits.org/) for automated versioning and changelog.

| Type | Bump | Example |
|------|------|---------|
| `feat` | Minor | `feat(bank): add deposit-all` |
| `fix` | Patch | `fix: resolve crash on empty inventory` |
| `feat!` | Major | `feat!: redesign API` |
| `docs`, `refactor`, `test`, `chore` | — | `chore: update deps` |

Push to `main` triggers automatic release to PyPI.

## License

MIT
