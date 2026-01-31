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

"""Configuration loading and path expansion."""

from pathlib import Path
from typing import Any

import yaml


def expand_path(path_str: str, home: Path | None = None) -> Path:
    """Expand path variables like $HOME, $CONFIG, $LOCAL.

    Args:
        path_str: Path string with variables to expand.
        home: Home directory path. Defaults to Path.home().

    Returns:
        Expanded Path object.
    """
    if home is None:
        home = Path.home()

    config_path = home / ".config"
    local_path = home / ".local"

    path_str = path_str.replace("$HOME", str(home))
    path_str = path_str.replace("$CONFIG", str(config_path))
    path_str = path_str.replace("$LOCAL", str(local_path))
    return Path(path_str)


def load_config(config_file: Path) -> dict[str, Any]:
    """Load YAML configuration file.

    Args:
        config_file: Path to the YAML config file.

    Returns:
        Parsed configuration dictionary.

    Raises:
        FileNotFoundError: If the config file doesn't exist.
        yaml.YAMLError: If the YAML is invalid.
    """
    if not config_file.exists():
        raise FileNotFoundError(f"Configuration file not found: {config_file}")

    with open(config_file) as f:
        result: dict[str, Any] = yaml.safe_load(f)
        return result
