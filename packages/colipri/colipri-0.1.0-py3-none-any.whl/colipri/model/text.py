from __future__ import annotations

import torch.nn.functional as F
from torch import nn
from transformers import BertModel

from ..types import TypeTextAttentionMask
from ..types import TypeTextEmbeddings
from ..types import TypeTextTokenIds
from .base import ModelMixin


class TextEncoder(nn.Module, ModelMixin):
    def __init__(self, backbone: nn.Module, pooler: nn.Module):
        super().__init__()
        if hasattr(backbone, "bert"):
            bert = backbone.bert
            assert isinstance(bert, BertModel)
            bert.pooler = None  # we use our own pooler
            backbone = bert
        self.backbone = backbone
        self.pooler = pooler

    def forward(
        self,
        token_ids: TypeTextTokenIds,
        attention_mask: TypeTextAttentionMask | None = None,
        *,
        pool: bool = True,
        normalize: bool = True,
    ) -> TypeTextEmbeddings:
        token_ids = token_ids.to(self.device)
        if attention_mask is not None:
            attention_mask = attention_mask.to(self.device)
        # We didn't use a projector during pre-training
        output = self.backbone(token_ids, attention_mask=attention_mask)
        embeddings = output["last_hidden_state"]
        if pool:
            embeddings = self.pooler(embeddings)
        if normalize:
            embeddings = F.normalize(embeddings, dim=1)
        return embeddings
