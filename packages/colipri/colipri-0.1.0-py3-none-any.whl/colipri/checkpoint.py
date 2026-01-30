from pathlib import Path

from huggingface_hub import hf_hub_download
from hydra import compose
from hydra import initialize_config_dir
from omegaconf import DictConfig
from torch import Tensor

from .defaults import REPO_NAME
from .defaults import REPO_USER
from .defaults import REVISION
from .defaults import ROOT_CONFIG_FILENAME
from .defaults import WEIGHTS_FILENAME
from .defaults import get_configs_dir

TypeStateDict = dict[str, Tensor]


def download_weights(**kwargs) -> Path:
    weights_path = _download_from_hugging_face(**kwargs)
    return weights_path


def _download_from_hugging_face(
    repo_user: str = REPO_USER,
    repo_name: str = REPO_NAME,
    revision: str | None = REVISION,
    filename: str = WEIGHTS_FILENAME,
) -> Path:
    repo_id = f"{repo_user}/{repo_name}"
    try:
        weights_path = hf_hub_download(
            repo_id=repo_id,
            filename=filename,
            revision=revision,
        )
    except Exception as e:
        msg = f'Failed to download "{filename}" from Hugging Face Hub repo "{repo_id}".'
        raise RuntimeError(msg) from e
    return Path(weights_path)


def _load_config(**kwargs) -> DictConfig:
    with initialize_config_dir(str(get_configs_dir()), version_base=None):
        config = compose(ROOT_CONFIG_FILENAME, **kwargs)
    return config


def load_model_config(**kwargs) -> DictConfig:
    return _load_config(**kwargs)["model"]


def load_processor_config(**kwargs) -> DictConfig:
    return _load_config(**kwargs)["processor"]
