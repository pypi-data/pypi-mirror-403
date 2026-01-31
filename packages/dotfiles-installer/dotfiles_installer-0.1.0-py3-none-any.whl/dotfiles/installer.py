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

"""Core installation logic."""

import shutil
from pathlib import Path
from typing import Any

from dotfiles.config import expand_path


class Installer:
    """Handles dotfiles installation based on YAML configuration."""

    def __init__(self, base_dir: Path, home: Path | None = None):
        """Initialize the installer.

        Args:
            base_dir: Base directory where source configs are located.
            home: Home directory for installations. Defaults to Path.home().
        """
        self.base_dir = base_dir
        self.home = home or Path.home()
        self.dependencies: set[str] = set()

    def backup(self, path: Path) -> Path | None:
        """Backup a file or directory if it exists.

        Args:
            path: Path to backup.

        Returns:
            Path to the backup file, or None if nothing was backed up.
        """
        if not path.exists():
            return None

        backup_path = path.with_suffix(path.suffix + ".bak")

        if backup_path.exists():
            if backup_path.is_dir():
                shutil.rmtree(backup_path)
            else:
                backup_path.unlink()

        shutil.move(path, backup_path)
        return backup_path

    def copy_directory(self, src: Path, dst: Path) -> None:
        """Copy a directory tree, replacing the destination.

        Args:
            src: Source directory.
            dst: Destination directory.
        """
        if dst.exists():
            shutil.rmtree(dst)
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copytree(src, dst)

    def copy_contents(self, src: Path, dst: Path) -> None:
        """Copy contents of src directory into dst directory.

        Args:
            src: Source directory.
            dst: Destination directory.
        """
        dst.mkdir(parents=True, exist_ok=True)
        for item in src.iterdir():
            dest_item = dst / item.name
            if item.is_dir():
                self.copy_directory(item, dest_item)
            else:
                shutil.copy2(item, dest_item)

    def install(self, name: str, config: dict[str, Any]) -> list[str] | None:
        """Install a single configuration based on YAML spec.

        Args:
            name: Name of the configuration.
            config: Configuration dictionary with source, dest, etc.

        Returns:
            List of notes for this config if successful, None if failed.
        """
        source = self.base_dir / config["source"]
        dest = expand_path(config["dest"], self.home)
        copy_mode = config.get("copy_mode", "directory")

        if not source.exists():
            return None

        # Handle backups
        if copy_mode == "contents":
            backup_files = config.get("backup_files", [])
            for backup_file_name in backup_files:
                self.backup(dest / backup_file_name)
        else:
            self.backup(dest)

        # Copy files
        if copy_mode == "contents":
            self.copy_contents(source, dest)
            # Remove backup files after successful copy
            for backup_file_name in config.get("backup_files", []):
                backup_path = (dest / backup_file_name).with_suffix(
                    (dest / backup_file_name).suffix + ".bak"
                )
                if backup_path.exists():
                    backup_path.unlink()
        else:
            self.copy_directory(source, dest)
            # Remove backup directory after successful copy
            backup_path = dest.with_suffix(dest.suffix + ".bak")
            if backup_path.exists():
                shutil.rmtree(backup_path)

        # Track dependencies
        for dep in config.get("dependencies", []):
            self.dependencies.add(dep)

        # Return notes for this config
        notes: list[str] = config.get("notes", [])
        return notes

    def install_all(
        self, configs: dict[str, dict[str, Any]]
    ) -> dict[str, list[str] | None]:
        """Install all configurations.

        Args:
            configs: Dictionary of config name to config spec.

        Returns:
            Dictionary of config name to notes (or None if failed).
        """
        results = {}
        for name, config in configs.items():
            results[name] = self.install(name, config)
        return results
