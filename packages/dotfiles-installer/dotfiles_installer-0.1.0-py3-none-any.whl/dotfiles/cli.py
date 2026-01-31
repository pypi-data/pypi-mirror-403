# Copyright 2026 Riley Rice
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Command-line interface for dotfiles installer."""

import argparse
import sys
from pathlib import Path

from dotfiles.config import expand_path, load_config
from dotfiles.installer import Installer


def print_green(msg: str) -> None:
    print(f"\033[32m{msg}\033[0m")


def print_red(msg: str) -> None:
    print(f"\033[31m{msg}\033[0m")


def print_yellow(msg: str) -> None:
    print(f"\033[33m{msg}\033[0m")


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="dotfiles",
        description="Install dotfiles configurations from a YAML file",
    )
    parser.add_argument(
        "config",
        type=Path,
        help="Path to YAML config file (e.g., mac.yaml, linux.yaml)",
    )

    args = parser.parse_args()

    # Resolve config path
    config_file = args.config.resolve()

    if not config_file.exists():
        print_red(f"Error: Configuration file not found: {config_file}")
        sys.exit(1)

    print_green(f"Using: {config_file.name}")
    print()

    # Load configuration
    try:
        config_data = load_config(config_file)
    except Exception as e:
        print_red(f"Error loading config: {e}")
        sys.exit(1)

    configs = config_data.get("configs", {})

    if not configs:
        print_yellow("No configurations found in config file.")
        sys.exit(0)

    # Install from the directory containing the config file
    base_dir = config_file.parent
    installer = Installer(base_dir)

    # Install each configuration
    for name, config in configs.items():
        print_green(f"Installing {name}...")

        notes = installer.install(name, config)
        if notes is not None:
            source = (base_dir / config["source"]).resolve()
            dest = expand_path(config["dest"])
            print(f"  {source} -> {dest}")

            # Print warnings for this config
            if notes:
                print()
                print_yellow("  Warnings:")
                print()
                for i, note in enumerate(notes):
                    for line in note.strip().split("\n"):
                        print_yellow(f"  {line}")
                    if i < len(notes) - 1:
                        print()
        else:
            print_red("  Error: Source not found")

        print()

    # Print summary
    print_green("Installation complete!")
    print()

    if installer.dependencies:
        print_yellow("Dependencies (install using your package manager):")
        for dep in sorted(installer.dependencies):
            print(f"  - {dep}")
        print()

    print_yellow(
        "Note: You may need to restart your terminal for changes to take effect"
    )


if __name__ == "__main__":
    main()
