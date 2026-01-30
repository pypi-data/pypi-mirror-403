import os
from typing import TypeAlias

import torchio as tio
from jaxtyping import Float
from jaxtyping import Int64
from torch import Tensor

TypePath: TypeAlias = str | os.PathLike[str]
TypePaths: TypeAlias = list[TypePath]

# Raw inputs
TypeImage: TypeAlias = tio.ScalarImage
TypeImages: TypeAlias = list[tio.ScalarImage]
TypeImageOrImages: TypeAlias = TypeImage | TypeImages

TypeString: TypeAlias = str
TypeStrings: TypeAlias = list[str]
TypeStringOrStrings: TypeAlias = TypeString | TypeStrings

TypeIntOrTripletInt: TypeAlias = int | tuple[int, int, int]

# Processed inputs
TypeImagesTensor: TypeAlias = Float[Tensor, "batch 1 x_in y_in z_in"]

TypeTextTokenIds: TypeAlias = Int64[Tensor, "batch text_length"]
TypeTextAttentionMask: TypeAlias = Int64[Tensor, "batch text_length"]

# Outputs
TypeSequenceEmbeddings: TypeAlias = Float[Tensor, "batch sequence_length embed_dim"]
TypePooledEmbeddings: TypeAlias = Float[Tensor, "batch embed_dim"]

TypePatchEmbeddings: TypeAlias = Float[Tensor, "batch embed_dim x_out y_out z_out"]
TypeImageEmbeddings: TypeAlias = TypePatchEmbeddings | TypePooledEmbeddings

TypeTextEmbeddings: TypeAlias = TypeSequenceEmbeddings | TypePooledEmbeddings

TypePatchLogits: TypeAlias = Float[Tensor, "num_images num_prompts x_out y_out z_out"]
TypePooledLogits: TypeAlias = Float[Tensor, "num_images num_prompts"]
TypePatchProbabilities: TypeAlias = TypePatchLogits
TypePooledProbabilities: TypeAlias = TypePooledLogits
TypeScores: TypeAlias = list[dict[str, float | str]]
