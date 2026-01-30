from __future__ import annotations

import logging
from pathlib import Path

import torch
from accelerate import init_empty_weights
from accelerate import load_checkpoint_and_dispatch
from einops import rearrange
from hydra.utils import instantiate
from safetensors.torch import load_model
from safetensors.torch import save_model
from torch import nn
from transformers.utils.logging import get_verbosity
from transformers.utils.logging import set_verbosity
from transformers.utils.logging import set_verbosity_error

from ..checkpoint import download_weights
from ..checkpoint import load_model_config
from ..types import TypeImageEmbeddings
from ..types import TypeImagesTensor
from ..types import TypeIntOrTripletInt
from ..types import TypePatchEmbeddings
from ..types import TypePatchLogits
from ..types import TypePatchProbabilities
from ..types import TypePath
from ..types import TypePooledEmbeddings
from ..types import TypePooledLogits
from ..types import TypePooledProbabilities
from ..types import TypeTextAttentionMask
from ..types import TypeTextEmbeddings
from ..types import TypeTextTokenIds
from .base import ModelMixin
from .image import ImageEncoder
from .text import TextEncoder


def get_model(
    checkpoint_path: TypePath | None = None,
    *,
    pretrained: bool = True,
    image_only: bool = False,
    **kwargs,
) -> Model:
    if pretrained and checkpoint_path is None:
        checkpoint_path = download_weights()

    overrides = []
    for key, value in kwargs.items():
        overrides.append(f"{key}={value}")
    config = load_model_config(overrides=overrides)

    if image_only:
        config.text_encoder = None

    transformers_verbosity = get_verbosity()
    set_verbosity_error()
    if checkpoint_path is None:
        model = instantiate(config)
    else:
        with init_empty_weights():
            model = instantiate(config)
        accelerate_logger = logging.getLogger("accelerate.utils.modeling")
        old_level = accelerate_logger.getEffectiveLevel()
        accelerate_logger.setLevel(logging.ERROR)
        model = load_checkpoint_and_dispatch(model, str(checkpoint_path))
        accelerate_logger.setLevel(old_level)
    set_verbosity(transformers_verbosity)

    assert isinstance(model, Model)
    return model.eval()


class Model(nn.Module, ModelMixin):
    def __init__(
        self,
        image_encoder: ImageEncoder,
        text_encoder: TextEncoder,
        temperature: float = 1,
    ):
        super().__init__()
        self.image_encoder = image_encoder
        self.text_encoder = text_encoder
        self.register_buffer("softmax_temperature", torch.tensor(temperature))

    @property
    def patch_size(self) -> tuple[int, int, int]:
        return self.image_encoder.patch_size

    def encode_image(
        self,
        images: TypeImagesTensor,
        *,
        pool: bool = False,
        project: bool = False,
        normalize: bool = False,
        window_size: TypeIntOrTripletInt | None = None,
    ) -> TypeImageEmbeddings:
        return self.image_encoder(
            images,
            project=project,
            pool=pool,
            normalize=normalize,
            window_size=window_size,
        )

    def encode_text(
        self,
        token_ids: TypeTextTokenIds,
        attention_mask: TypeTextAttentionMask | None = None,
        *,
        pool: bool = True,
        normalize: bool = True,
    ) -> TypeTextEmbeddings:
        return self.text_encoder(
            token_ids,
            attention_mask,
            pool=pool,
            normalize=normalize,
        )

    def compute_similarities(
        self,
        image_embeddings: TypePooledEmbeddings | TypePatchEmbeddings,
        text_embeddings: TypePooledEmbeddings,
    ) -> TypePatchLogits | TypePooledLogits:
        text_embeddings = rearrange(text_embeddings, "num_prompts c -> c num_prompts")
        is_grid = image_embeddings.ndim == 5
        if is_grid:
            num_images, _, x, y, z = image_embeddings.shape
            image_embeddings = rearrange(
                image_embeddings,
                "num_images c x y z -> (num_images x y z) c",
            )
            similarities_flat = image_embeddings @ text_embeddings
            similarities = rearrange(
                similarities_flat,
                "(num_images x y z) num_prompts -> num_images num_prompts x y z",
                num_images=num_images,
                x=x,
                y=y,
                z=z,
            )
        else:
            similarities = image_embeddings @ text_embeddings
        return similarities

    def classify(
        self,
        images: TypePooledEmbeddings | TypePatchEmbeddings,
        text: TypePooledEmbeddings,
    ) -> TypePooledProbabilities | TypePatchProbabilities:
        logits = self.compute_similarities(images, text)
        assert isinstance(self.softmax_temperature, torch.Tensor)
        probabilities = (logits / self.softmax_temperature).softmax(dim=-1)
        return probabilities

    def save_weights(self, path: TypePath) -> None:
        path = Path(path)
        if path.suffix == ".safetensors":
            save_model(self, str(path))
        else:
            weights = self.state_dict()
            torch.save(weights, path)

    def load_weights(
        self,
        path: TypePath,
        device: torch.device | str | None = None,
    ) -> None:
        path = Path(path)
        if not path.exists():
            raise FileNotFoundError(f"Checkpoint file {path} does not exist.")
        if device is None:
            device = torch.device("cpu")
        if path.suffix == ".safetensors":
            if device is not None:
                device = str(device)
            missing, unexpected = load_model(self, path, device=device)
            if missing or unexpected:
                raise RuntimeError("TODO")
        else:
            weights = torch.load(path, map_location=device)
            self.load_state_dict(weights, strict=False)
