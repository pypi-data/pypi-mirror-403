# Contributing to python-ripgrep

Thank you for your interest in contributing to python-ripgrep!

## Development Setup

### Prerequisites

- Python 3.10 or higher
- Rust toolchain (install from https://rustup.rs/)
- maturin (`pip install maturin`)

### Building from Source

```bash
# Clone the repository
git clone https://github.com/indent-com/python-ripgrep.git
cd python-ripgrep

# Build and install in development mode
maturin develop

# Run tests
python test.py
```

### Making Changes

1. Fork the repository
2. Create a new branch for your feature/fix
3. Make your changes
4. Test your changes locally
5. Submit a pull request

### Code Style

- Rust code should follow standard Rust formatting (`cargo fmt`)
- Run clippy for linting (`cargo clippy`)
- Ensure all tests pass before submitting

## Adding New Features

To add new ripgrep options:

1. Update the `PyArgs` struct in `src/ripgrep_core.rs`
2. Modify the `pyargs_to_hiargs` function to handle the new option
3. Update the Python wrapper code if needed
4. Add tests for the new functionality
5. Update the README with the new feature

## Release Process

Releases are automated via GitHub Actions:

1. Update version in `pyproject.toml` and `Cargo.toml`
2. Create a new GitHub release
3. Wheels will be built and published to PyPI automatically

## Questions?

Feel free to open an issue for any questions or concerns!
