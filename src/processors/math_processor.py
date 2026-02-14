from PIL import Image
from pathlib import Path
import fitz, os

from src.processors import BaseProcessor
from src.datamodel import TextModel
from src.ocr import FormulaRecognition

class MathProcessor(BaseProcessor):
    def __init__(self, output_dir: Path = None, model_name: str = "breezedeus/pix2text-mfr-1.5"):
        super().__init__()
        self._output_dir = output_dir if output_dir is not None else os.path.join(os.path.dirname(os.path.dirname(__file__)), "output")
        ## Load the ocr model
        self._model = FormulaRecognition(model_name=model_name)
    def process(self, page, page_number: int, block: dict) -> TextModel:

        bbox = block.get("bbox_pdf", [])
        confidence = block.get("confidence", 0)
        class_name = block.get("class_name", "Math")
        rect = fitz.Rect(bbox[0], bbox[1], bbox[2], bbox[3])


        ## Extract the image from the page
        mat = fitz.Matrix(2.0, 2.0)
        pix = page.get_pixmap(clip=rect, matrix=mat)
        img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)

        img_dir = os.path.join(self._output_dir, "predictions", f"page_{page_number:04d}", "formula")
        os.makedirs(img_dir, exist_ok=True)

        print(f"Saving Formula image to {img_dir}")
        img.save(os.path.join(img_dir, f"page_{page_number:04d}_{block.get('id',-1)}.png"))

        ## Process the image using the ocr model
        generated_text = self._model.recognize(img)

        return TextModel(
            page=page_number,
            bbox=bbox,
            class_name=class_name,
            confidence=confidence,
            content=generated_text[0]
        )