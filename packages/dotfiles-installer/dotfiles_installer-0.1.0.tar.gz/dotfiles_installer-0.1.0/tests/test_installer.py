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

"""Tests for the Installer class."""

from pathlib import Path

import pytest
from dotfiles.installer import Installer


@pytest.fixture
def setup_dirs(tmp_path: Path) -> tuple[Path, Path]:
    """Create source and home directories for testing."""
    base_dir = tmp_path / "dotfiles"
    home_dir = tmp_path / "home"
    base_dir.mkdir()
    home_dir.mkdir()
    return base_dir, home_dir


class TestBackup:
    def test_backs_up_existing_file(self, setup_dirs: tuple[Path, Path]) -> None:
        base_dir, home_dir = setup_dirs
        installer = Installer(base_dir, home_dir)

        test_file = home_dir / "test.txt"
        test_file.write_text("original content")

        backup_path = installer.backup(test_file)

        assert backup_path == home_dir / "test.txt.bak"
        assert backup_path.exists()
        assert backup_path.read_text() == "original content"
        assert not test_file.exists()

    def test_backs_up_existing_directory(self, setup_dirs: tuple[Path, Path]) -> None:
        base_dir, home_dir = setup_dirs
        installer = Installer(base_dir, home_dir)

        test_dir = home_dir / "testdir"
        test_dir.mkdir()
        (test_dir / "file.txt").write_text("content")

        backup_path = installer.backup(test_dir)

        assert backup_path == home_dir / "testdir.bak"
        assert backup_path.is_dir()
        assert (backup_path / "file.txt").read_text() == "content"

    def test_returns_none_for_nonexistent(self, setup_dirs: tuple[Path, Path]) -> None:
        base_dir, home_dir = setup_dirs
        installer = Installer(base_dir, home_dir)

        result = installer.backup(home_dir / "nonexistent")
        assert result is None

    def test_overwrites_existing_backup(self, setup_dirs: tuple[Path, Path]) -> None:
        base_dir, home_dir = setup_dirs
        installer = Installer(base_dir, home_dir)

        test_file = home_dir / "test.txt"
        backup_file = home_dir / "test.txt.bak"

        # Create old backup
        backup_file.write_text("old backup")

        # Create new file to backup
        test_file.write_text("new content")

        installer.backup(test_file)

        assert backup_file.read_text() == "new content"


class TestCopyDirectory:
    def test_copies_directory(self, setup_dirs: tuple[Path, Path]) -> None:
        base_dir, home_dir = setup_dirs
        installer = Installer(base_dir, home_dir)

        # Create source directory
        src = base_dir / "config"
        src.mkdir()
        (src / "file1.txt").write_text("content1")
        (src / "subdir").mkdir()
        (src / "subdir" / "file2.txt").write_text("content2")

        dst = home_dir / ".config" / "app"
        installer.copy_directory(src, dst)

        assert dst.is_dir()
        assert (dst / "file1.txt").read_text() == "content1"
        assert (dst / "subdir" / "file2.txt").read_text() == "content2"

    def test_replaces_existing_directory(self, setup_dirs: tuple[Path, Path]) -> None:
        base_dir, home_dir = setup_dirs
        installer = Installer(base_dir, home_dir)

        # Create existing destination
        dst = home_dir / "existing"
        dst.mkdir()
        (dst / "old.txt").write_text("old")

        # Create source
        src = base_dir / "new"
        src.mkdir()
        (src / "new.txt").write_text("new")

        installer.copy_directory(src, dst)

        assert (dst / "new.txt").read_text() == "new"
        assert not (dst / "old.txt").exists()


class TestCopyContents:
    def test_copies_contents_into_directory(
        self, setup_dirs: tuple[Path, Path]
    ) -> None:
        base_dir, home_dir = setup_dirs
        installer = Installer(base_dir, home_dir)

        # Create source with files
        src = base_dir / "zsh"
        src.mkdir()
        (src / ".zshrc").write_text("zshrc content")
        (src / ".zsh_profile").write_text("profile content")

        installer.copy_contents(src, home_dir)

        assert (home_dir / ".zshrc").read_text() == "zshrc content"
        assert (home_dir / ".zsh_profile").read_text() == "profile content"


class TestInstall:
    def test_installs_directory_mode(self, setup_dirs: tuple[Path, Path]) -> None:
        base_dir, home_dir = setup_dirs
        installer = Installer(base_dir, home_dir)

        # Create source
        src = base_dir / "config" / "nvim"
        src.mkdir(parents=True)
        (src / "init.lua").write_text("vim config")

        config = {
            "source": "config/nvim",
            "dest": "$CONFIG/nvim",
            "copy_mode": "directory",
            "dependencies": ["neovim"],
        }

        result = installer.install("nvim", config)

        assert result is not None
        assert (home_dir / ".config" / "nvim" / "init.lua").read_text() == "vim config"
        assert "neovim" in installer.dependencies

    def test_installs_contents_mode(self, setup_dirs: tuple[Path, Path]) -> None:
        base_dir, home_dir = setup_dirs
        installer = Installer(base_dir, home_dir)

        # Create source
        src = base_dir / "zsh"
        src.mkdir()
        (src / ".zshrc").write_text("zsh config")

        config = {
            "source": "zsh",
            "dest": "$HOME",
            "copy_mode": "contents",
            "dependencies": ["zsh"],
        }

        result = installer.install("zsh", config)

        assert result is not None
        assert (home_dir / ".zshrc").read_text() == "zsh config"
        assert "zsh" in installer.dependencies

    def test_returns_none_for_missing_source(
        self, setup_dirs: tuple[Path, Path]
    ) -> None:
        base_dir, home_dir = setup_dirs
        installer = Installer(base_dir, home_dir)

        config = {
            "source": "nonexistent",
            "dest": "$HOME",
        }

        result = installer.install("test", config)
        assert result is None

    def test_returns_notes(self, setup_dirs: tuple[Path, Path]) -> None:
        base_dir, home_dir = setup_dirs
        installer = Installer(base_dir, home_dir)

        # Create source
        src = base_dir / "test"
        src.mkdir()
        (src / "file").write_text("content")

        config = {
            "source": "test",
            "dest": "$HOME/test",
            "notes": ["Install dependency X", "Run post-install script"],
        }

        notes = installer.install("test", config)

        assert notes is not None
        assert len(notes) == 2
        assert "Install dependency X" in notes


class TestInstallAll:
    def test_installs_multiple_configs(self, setup_dirs: tuple[Path, Path]) -> None:
        base_dir, home_dir = setup_dirs
        installer = Installer(base_dir, home_dir)

        # Create sources
        (base_dir / "zsh").mkdir()
        (base_dir / "zsh" / ".zshrc").write_text("zsh")

        (base_dir / "config" / "nvim").mkdir(parents=True)
        (base_dir / "config" / "nvim" / "init.lua").write_text("nvim")

        configs = {
            "zsh": {
                "source": "zsh",
                "dest": "$HOME",
                "copy_mode": "contents",
            },
            "nvim": {
                "source": "config/nvim",
                "dest": "$CONFIG/nvim",
                "copy_mode": "directory",
            },
        }

        results = installer.install_all(configs)

        assert results["zsh"] is not None
        assert results["nvim"] is not None
        assert (home_dir / ".zshrc").exists()
        assert (home_dir / ".config" / "nvim" / "init.lua").exists()
