# dotfiles

[![PyPI version](https://badge.fury.io/py/dotfiles-installer.svg)](https://pypi.org/project/dotfiles-installer/)
[![CI](https://github.com/riceriley59/dotfiles/actions/workflows/ci.yaml/badge.svg)](https://github.com/riceriley59/dotfiles/actions/workflows/ci.yaml)
[![Coverage Status](https://coveralls.io/repos/github/riceriley59/dotfiles/badge.svg?branch=main)](https://coveralls.io/github/riceriley59/dotfiles?branch=main)
[![License](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)

A CLI tool to install dotfiles configurations from YAML. Includes personal configs for Neovim, Tmux, Zsh, Ghostty, Kitty, i3, and Polybar.

## Installation

### From PyPI

```bash
pip install dotfiles-installer

# macOS
dotfiles configs/mac.yaml

# Linux
dotfiles configs/linux.yaml
```

### From Source

```bash
git clone https://github.com/riceriley59/dotfiles.git
cd dotfiles
pip install -e .

# macOS
dotfiles configs/mac.yaml

# Linux
dotfiles configs/linux.yaml
```

## Structure

```
├── configs/          # YAML configs (mac.yaml, linux.yaml)
├── dotfiles/         # Installer CLI package
├── files/            # Dotfiles to install
│   ├── config/       # ~/.config/* (nvim, ghostty, kitty, i3, polybar)
│   ├── zsh/          # ~/.zshrc, ~/.zsh_profile
│   ├── tmux/         # ~/.tmux.conf
│   └── bin/          # ~/.local/scripts
└── tests/            # Test suite
```

## What Gets Installed

| Config   | Destination | Notes |
|----------|-------------|-------|
| zsh      | `$HOME` | Requires [oh-my-zsh](https://ohmyz.sh/) |
| tmux     | `$HOME` | Requires [TPM](https://github.com/tmux-plugins/tpm) |
| nvim     | `~/.config/nvim` | Requires ripgrep |
| ghostty  | `~/.config/ghostty` | |
| kitty    | `~/.config/kitty` | |
| scripts  | `~/.local/scripts` | Requires fzf |
| i3       | `~/.config/i3` | Linux only |
| polybar  | `~/.config/polybar` | Linux only |

## Development

```bash
pip install -e ".[dev]"
pytest
```
