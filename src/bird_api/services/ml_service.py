from __future__ import annotations

from typing import Any

from PIL import ImageFile
from transformers import pipeline


class BirdClassifier:
    def __init__(self) -> None:
        self.classifier = pipeline(
            "image-classification", model="chriamue/bird-species-classifier"
        )

    def predict(self, image: ImageFile.ImageFile) -> list[dict[str, Any]]:
        return self.classifier(image)
