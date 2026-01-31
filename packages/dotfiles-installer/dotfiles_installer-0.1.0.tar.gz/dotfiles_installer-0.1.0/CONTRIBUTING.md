# Contributing

Thanks for your interest in contributing!

## Guidelines

### Off-limits: `files/` directory

The `files/` directory contains my personal dotfiles and configurations. Please **do not** submit changes to anything under this directory.

### Welcome contributions

Contributions are welcome for:

- **`dotfiles/`** - The installer CLI package
- **`tests/`** - Test coverage improvements
- **`configs/`** - Config schema improvements (not personal settings)
- **Documentation** - README, docstrings, etc.
- **CI/CD** - GitHub Actions workflows
- **Bug fixes** and **new features** for the installer tool

## Development

```bash
# Clone and install
git clone https://github.com/riceriley59/dotfiles.git
cd dotfiles
pip install -e ".[dev]"

# Run checks
make check
```

## Pull Requests

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Ensure `make check` passes
5. Submit a pull request
