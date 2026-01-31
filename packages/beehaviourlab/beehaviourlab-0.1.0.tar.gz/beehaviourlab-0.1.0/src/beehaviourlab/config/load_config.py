import logging
import sys
from pathlib import Path
from types import SimpleNamespace
from typing import Union

import yaml

from enum import Enum


class ConfigFiles(Enum):
    TRACKING = Path("src/beehaviourlab/config/tracking_config.yaml")


def get_config(data: Union[ConfigFiles, Path, dict, None]) -> SimpleNamespace:
    """Given a path to a YAML file, a dictionary object or an ConfigFiles enum
    member, returns a simple namespace object holding config data.
    If the data is None, an empty namespace is returned.
    """
    if data is None:
        return SimpleNamespace()
    elif isinstance(data, ConfigFiles):
        return get_config(data.value)
    elif isinstance(data, Path):
        logging.info(f"Loading config from {data}")
        if data.exists():
            with open(data, "r") as stream:
                config_dict = yaml.safe_load(stream)
            config_dict = _resolve_paths(config_dict, data.parent)
            return SimpleNamespace(**config_dict)
        else:
            logging.error("Couldn't find config file... Exiting!")
            sys.exit(1)
    elif isinstance(data, dict):
        return SimpleNamespace(**data)


def _resolve_paths(config_dict: dict, base_dir: Path) -> dict:
    """Resolve known path entries relative to the config file location."""
    if not isinstance(config_dict, dict):
        return config_dict
    resolved = dict(config_dict)
    path_keys = {"ultralytics_config"}
    for key, value in config_dict.items():
        if isinstance(value, str) and (key.endswith("_path") or key in path_keys):
            path = Path(value)
            if not path.is_absolute():
                candidate = base_dir / path
                if candidate.exists():
                    resolved[key] = str(candidate)
                else:
                    resolved[key] = str(base_dir.parent / path)
    return resolved
