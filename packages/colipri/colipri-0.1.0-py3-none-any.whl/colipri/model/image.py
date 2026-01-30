from __future__ import annotations

import torch
import torch.nn.functional as F
import torchio as tio
from dynamic_network_architectures.architectures.primus import Primus
from einops import rearrange
from torch import nn
from tqdm.auto import tqdm

from ..pooling import AttentionPool1D
from ..types import TypeImageEmbeddings
from ..types import TypeImagesTensor
from ..types import TypeIntOrTripletInt
from .base import ModelMixin


class ImageEncoder(nn.Module, ModelMixin):
    def __init__(
        self,
        backbone: Primus,
        projector: nn.Conv3d,
        pooler: AttentionPool1D,
    ):
        super().__init__()
        self.backbone = self._remove_decoder(backbone)
        self.projector = projector
        self.pooler = pooler

    def _remove_decoder(self, backbone: Primus) -> Primus:
        if hasattr(backbone, "up_projection"):
            backbone.up_projection = nn.Identity()  # type: ignore
        return backbone

    @property
    def patch_size(self) -> tuple[int, int, int]:
        patch_embedder: nn.Conv3d = self.backbone.down_projection.proj  # type: ignore[reportAssignmentType]
        patch_size: tuple[int, int, int] = patch_embedder.stride  # type: ignore[reportAssignmentType]
        return patch_size

    def encode(
        self,
        images: TypeImagesTensor,
    ) -> TypeImageEmbeddings:
        images = images.to(self.device)
        embeddings: TypeImageEmbeddings = self.backbone(images)
        return embeddings

    def encode_sliding_window(
        self,
        images: TypeImagesTensor,
        window_size: TypeIntOrTripletInt,
        overlap: int = 0,
    ) -> TypeImageEmbeddings:
        if len(set(self.patch_size)) > 1:
            msg = (
                "Sliding window encoding is only supported for models with cubic"
                " patch sizes for now."
            )
            raise NotImplementedError(msg)
        else:
            patch_size = self.patch_size[0]
        image_key = "image"  # could be anything
        embeddings = []
        for image in images:
            grid_sampler = tio.inference.GridSampler(
                tio.Subject(**{image_key: tio.ScalarImage(tensor=image)}),
                window_size,
                overlap,
            )
            patch_loader = tio.SubjectsLoader(grid_sampler)  # type: ignore[reportArgumentType]
            aggregator = tio.data.GridAggregator(
                grid_sampler,
                downsampling_factor=patch_size,
            )
            for patches_batch in tqdm(patch_loader):
                input_tensor = patches_batch[image_key][tio.DATA].to(self.device)
                locations = patches_batch[tio.LOCATION]
                outputs = self.backbone(input_tensor)
                aggregator.add_batch(outputs, locations)
            embeddings.append(aggregator.get_output_tensor())
        return torch.stack(embeddings).to(self.device)

    def forward(
        self,
        images: TypeImagesTensor,
        *,
        project: bool,
        pool: bool,
        normalize: bool,
        window_size: TypeIntOrTripletInt | None = None,
    ) -> TypeImageEmbeddings:
        if pool and not project:
            msg = "Pooling requires projection to be enabled. Set project=True."
            raise NotImplementedError(msg)
        if window_size is None:
            embeddings = self.encode(images)
        else:
            embeddings = self.encode_sliding_window(images, window_size)
        if project:
            embeddings = self.projector(embeddings)
            if pool:
                sequence = rearrange(embeddings, "b c x y z -> b (x y z) c")
                embeddings = self.pooler(sequence)
            else:
                embeddings = self.pooler.to_dense()(embeddings)
        if normalize:
            embeddings = F.normalize(embeddings, dim=1)
        return embeddings
