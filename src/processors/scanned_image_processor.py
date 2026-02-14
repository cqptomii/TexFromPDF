import os
from pathlib import Path

import fitz
from PIL import Image
from src.ocr import VlmImageRecognition
from src.processors import BaseProcessor
from src.datamodel import TextModel

class ScannedImageProcessor(BaseProcessor):
    def __init__(self, output_dir: Path = None, model_name: str = "PaddlePaddle/PaddleOCR-VL-1.5", device: str = "cpu", task : str = "ocr"):
        super().__init__()

        self._output_dir = output_dir if output_dir is not None else os.path.join(os.path.dirname(os.path.dirname(__file__)), "output")
        self._model = VlmImageRecognition(model_name=model_name, device=device, task=task)

    def process(self, page, page_number: int, block: dict) -> TextModel:
        bbox = block.get("bbox_pdf", [])
        confidence = block.get("confidence", 0)
        class_name = block.get("class_name", "image_scanned")
        rect = fitz.Rect(bbox[0], bbox[1], bbox[2], bbox[3])

        ## Extract the image from the page
        mat = fitz.Matrix(2.0, 2.0)
        pix = page.get_pixmap(matrix=mat, clip=rect)
        image = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)

        image_dir = os.path.join(self._output_dir, f"predictions/page_{page_number:04d}/scanned_image")
        os.makedirs(image_dir, exist_ok=True)
        image.save(os.path.join(image_dir,  f"image_{block['id']}_{page_number:04d}.png"))

        generated_content = self._model.recognize(image)

        return TextModel(
            page=page_number,
            bbox=bbox,
            class_name=class_name,
            confidence=confidence,
            content=generated_content
        )

