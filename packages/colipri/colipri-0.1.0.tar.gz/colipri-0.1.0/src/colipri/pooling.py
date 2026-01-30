import torch
from einops import rearrange
from torch import nn

from .types import TypePooledEmbeddings
from .types import TypeSequenceEmbeddings


class AttentionPool1D(nn.Module):
    def __init__(self, embed_dim: int, num_heads: int):
        super().__init__()
        self.attn = nn.MultiheadAttention(embed_dim, num_heads, batch_first=True)

    def forward(self, x: TypeSequenceEmbeddings) -> TypePooledEmbeddings:
        query = x.mean(dim=1, keepdim=True)
        key = value = x
        pooled, _ = self.attn(query, key, value)
        return rearrange(pooled, "batch 1 embed_dim -> batch embed_dim")

    def to_dense(self):
        v_proj_in_weight_qkv = self.get_parameter("attn.in_proj_weight")
        v_proj_in_bias_qkv = self.get_parameter("attn.in_proj_bias")
        v_proj_out_weight = self.get_parameter("attn.out_proj.weight")
        v_proj_out_bias = self.get_parameter("attn.out_proj.bias")
        dim = v_proj_in_weight_qkv.shape[0] // 3
        v_proj_in_weight_v = v_proj_in_weight_qkv[2 * dim :]
        v_proj_in_bias_v = v_proj_in_bias_qkv[2 * dim :]

        value_projection = nn.Conv3d(
            in_channels=dim,
            out_channels=dim,
            kernel_size=1,
        )
        value_projection.weight.data = rearrange(
            v_proj_in_weight_v,
            "c_out c_in -> c_out c_in 1 1 1",
        )
        assert value_projection.bias is not None
        value_projection.bias.data = v_proj_in_bias_v

        out_projection = nn.Conv3d(
            in_channels=dim,
            out_channels=dim,
            kernel_size=1,
        )
        out_projection.weight.data = rearrange(
            v_proj_out_weight,
            "c_out c_in -> c_out c_in 1 1 1",
        )
        assert out_projection.bias is not None
        out_projection.bias.data = v_proj_out_bias

        return nn.Sequential(
            value_projection,
            out_projection,
        )


class MultiLearnedQueryAttentionPool1D(AttentionPool1D):
    def __init__(self, embed_dim: int, num_heads: int):
        super().__init__(embed_dim, num_heads)
        # 4 Queries instead of 1
        self.query = nn.Parameter(torch.randn(1, 4, embed_dim) / embed_dim**0.5)

    def forward(self, x: TypeSequenceEmbeddings) -> TypePooledEmbeddings:
        """
        x: [B, T, D] — sequence of token embeddings
        returns: [B, D] — pooled representation
        """
        B, T, D = x.shape
        query = self.query.expand(B, -1, -1)  # [B, 4, D]
        pooled, _ = self.attn(query, x, x)  # [B, 4, D]
        # pooled: [4, B, D_out], want [B, D_out] by pooling over queries (mean)
        return pooled.mean(dim=1)  # [B, D]
