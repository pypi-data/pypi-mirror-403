# Usage

## Installation

```bash
# Clone the repository
git clone https://github.com/riceriley59/dotfiles.git
cd dotfiles

# Install the CLI tool
pip install -e .
```

## Running

```bash
# macOS
dotfiles configs/mac.yaml

# Linux
dotfiles configs/linux.yaml
```

The tool will:
1. Copy each configuration to its destination
2. Display any warnings/notes for manual setup steps
3. List all required dependencies at the end

## YAML Configuration Format

Each config file defines which dotfiles to install:

```yaml
configs:
  <name>:
    source: ../files/<folder>
    dest: $CONFIG/<folder>
    copy_mode: directory
    backup_files:
      - .zshrc
    dependencies:
      - <package>
    notes:
      - |
        <multi-line note>
```

### Config Options

| Option | Required | Description |
|--------|----------|-------------|
| `source` | Yes | Source directory path (relative to config file) |
| `dest` | Yes | Destination path (supports `$HOME`, `$CONFIG`, `$LOCAL`) |
| `copy_mode` | No | `directory` (default) or `contents` |
| `backup_files` | No | Files to backup when using `copy_mode: contents` |
| `dependencies` | No | List of packages to install |
| `notes` | No | Post-install instructions shown as warnings |

### Path Variables

| Variable  | Expands To         |
|-----------|-------------------|
| `$HOME`   | `~`               |
| `$CONFIG` | `~/.config`       |
| `$LOCAL`  | `~/.local`        |

### Copy Modes

- **directory**: Replaces the entire destination directory with the source
- **contents**: Copies individual files from source into destination (use with `$HOME`)

## Development

```bash
# Install with dev dependencies
pip install -e ".[dev]"

# Run all checks
make check

# Individual commands
make lint       # Ruff linter
make format     # Ruff formatter
make typecheck  # Mypy type checker
make test       # Pytest
```

## Adding a New Config

1. Add your config files to `files/<name>/`
2. Add an entry to the appropriate YAML file:

```yaml
  <name>:
    source: ../files/<name>
    dest: $CONFIG/<name>
    copy_mode: directory
    dependencies:
      - <package>
```

3. Run `dotfiles configs/mac.yaml` to test
