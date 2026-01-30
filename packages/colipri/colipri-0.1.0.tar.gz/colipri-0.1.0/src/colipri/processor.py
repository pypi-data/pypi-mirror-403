from __future__ import annotations

import torch
import torchio as tio
from hydra.utils import instantiate
from transformers import BertTokenizer
from transformers.tokenization_utils_base import BatchEncoding

from .checkpoint import load_processor_config
from .types import TypeImage
from .types import TypeImages
from .types import TypeImagesTensor
from .types import TypePath
from .types import TypeStringOrStrings
from .types import TypeTextAttentionMask
from .types import TypeTextTokenIds


def get_processor(*, image_only: bool = False, **kwargs) -> Processor:
    overrides = []
    for key, value in kwargs.items():
        overrides.append(f"{key}={value}")
    config = load_processor_config(overrides=overrides)
    if image_only:
        config.tokenizer = None
    return instantiate(config)


class Processor:
    def __init__(
        self,
        image_transform: tio.Transform,
        tokenizer: BertTokenizer,
    ):
        self._image_transform = image_transform
        self._text_tokenizer = tokenizer

    def __repr__(self) -> str:
        lines = [
            f"{self.__class__.__name__}(",
            f"  image_transform={self._image_transform},",
            f"  text_tokenizer={self._text_tokenizer},",
            ")",
        ]
        return "\n".join(lines)

    def process_images(
        self,
        inputs: TypePath | TypeImage | list[TypePath | TypeImage],
    ) -> TypeImages:
        if not isinstance(inputs, list):
            inputs = [inputs]
        images = []
        for image_or_path in inputs:
            is_image = isinstance(image_or_path, tio.ScalarImage)
            if is_image:
                image = image_or_path
            else:
                path = image_or_path
                image = tio.ScalarImage(path)
            images.append(image)
        images = [self._image_transform(image) for image in images]
        return images

    def to_images_batch(
        self,
        images: TypeImages,
    ) -> TypeImagesTensor:
        if not isinstance(images, list):
            msg = f"Expected images to be a list, got {type(images)}"
            raise TypeError(msg)
        images_tensor = torch.stack([image.data for image in images])
        return images_tensor

    def process_text(
        self,
        text: TypeStringOrStrings,
        **kwargs,
    ) -> tuple[TypeTextTokenIds, TypeTextAttentionMask]:
        encodings: BatchEncoding = self._text_tokenizer(
            text,
            max_length=512,  # TODO
            padding="max_length",
            truncation=True,
            return_tensors="pt",
            **kwargs,
        )
        token_ids: TypeTextTokenIds = encodings["input_ids"]  # type: ignore[reportAssignmentType]
        attention_mask: TypeTextAttentionMask = encodings["attention_mask"]  # type: ignore[reportAssignmentType]
        return token_ids, attention_mask
