from .model.multimodal import get_model
from .pipelines import ZeroShotImageClassificationPipeline
from .processor import get_processor
from .sample_data import load_sample_ct

__all__ = [
    "get_model",
    "get_processor",
    "load_sample_ct",
    "ZeroShotImageClassificationPipeline",
]

__version__ = "0.1.0"

