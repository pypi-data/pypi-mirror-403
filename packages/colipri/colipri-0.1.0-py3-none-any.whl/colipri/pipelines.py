import torch

from .model.multimodal import Model
from .processor import Processor
from .types import TypeImage
from .types import TypePath
from .types import TypeScores


class ZeroShotImageClassificationPipeline:
    def __init__(
        self,
        model: Model,
        processor: Processor,
        batch_size: int = 1,  # TODO
        num_workers: int = 0,  # TODO
    ):
        self._model = model.eval()
        self._processor = processor

    @property
    def device(self) -> torch.device:
        return self._model.device

    # TODO: add support for multiple prompts per class
    @torch.no_grad()
    def __call__(
        self,
        images: TypePath | TypeImage | list[TypePath | TypeImage],
        prompts: str | list[str],
    ) -> TypeScores | list[TypeScores]:
        preprocessed_images = self._processor.process_images(images)
        images_batch = self._processor.to_images_batch(preprocessed_images)

        text_token_ids, text_attention_mask = self._processor.process_text(prompts)

        image_embeddings_batch = self._model.encode_image(
            images_batch,
            project=True,
            pool=True,
            normalize=True,
        )
        text_embeddings_batch = self._model.encode_text(
            text_token_ids,
            text_attention_mask,
        )

        probabilities = self._model.classify(
            image_embeddings_batch,
            text_embeddings_batch,
        )

        if not isinstance(prompts, list):
            prompts = [prompts]

        all_results = []
        for image_probabilities in probabilities:
            image_results = []
            for prompt, score in zip(prompts, image_probabilities, strict=True):
                image_results.append({"score": score.item(), "label": prompt})
            all_results.append(image_results)

        if len(images_batch) == 1 and not isinstance(images, list):
            all_results = all_results[0]
        return all_results
