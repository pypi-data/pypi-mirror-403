# chimpy-me

Library bot framework with traditional modules and MCP services for institutions.

Part of the [CHIMPY](https://github.com/chimpy-me) organization: "Library tools, together strong"

## Installation

```bash
pip install chimpy-me
```

## Development

This project uses [UV](https://docs.astral.sh/uv/) for dependency management.

```bash
# Clone the repository
git clone https://github.com/chimpy-me/chimpy-me.git
cd chimpy-me

# Install dependencies
uv sync

# Install with dev dependencies
uv sync --extra dev

# Run tests
uv run pytest

# Run linting
uv run ruff check .
```

## License

MIT License - see [LICENSE](LICENSE) for details.
