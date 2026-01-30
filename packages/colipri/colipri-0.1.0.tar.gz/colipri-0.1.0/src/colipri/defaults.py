import importlib.resources
from pathlib import Path

package_name = __package__
assert isinstance(package_name, str)

REPO_USER = "microsoft"
REPO_NAME = package_name
REVISION = None
WEIGHTS_FILENAME = "model.safetensors"
ROOT_CONFIG_FILENAME = "config.yaml"


def get_configs_dir(pkg: str | None = None) -> Path:
    package_dir = importlib.resources.files(package_name)
    return Path(package_dir / "configs")


__all__ = [
    "get_configs_dir",
]
