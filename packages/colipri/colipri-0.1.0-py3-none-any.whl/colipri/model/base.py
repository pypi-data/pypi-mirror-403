import torch


class ModelMixin:
    @property
    def device(self) -> torch.device:
        one_parameter = next(self.parameters())
        return one_parameter.device
