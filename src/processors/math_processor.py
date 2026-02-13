from PIL import Image
from pathlib import Path
from transformers import TrOCRProcessor
from optimum.onnxruntime import ORTModelForVision2Seq
import fitz, os

from src.processors import BaseProcessor
from src.datamodel import TextModel

class MathProcessor(BaseProcessor):
    def __init__(self, output_dir: Path = None, model_name: str = "breezedeus/pix2text-mfr-1.5"):
        super().__init__()
        self._output_dir = output_dir if output_dir is not None else os.path.join(os.path.dirname(os.path.dirname(__file__)), "output")
        self._ocr_model_name = model_name

        ## Load the ocr model
        self._load_model()
    def _load_model(self):
        self._processor = TrOCRProcessor.from_pretrained(self._ocr_model_name, use_fast=True)
        self._model = ORTModelForVision2Seq.from_pretrained(
            self._ocr_model_name,
            use_cache=False,
            decoder_file_name="decoder_model.onnx",
            encoder_file_name="encoder_model.onnx"
        )
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
        pixel_values = self._processor(images=img, return_tensors="pt").pixel_values
        generated_ids = self._model.generate(pixel_values)
        generated_text = self._processor.batch_decode(generated_ids, skip_special_tokens=True)

        print(f'generated_ids: {generated_ids}, \ngenerated text: {generated_text}')

        return TextModel(
            page=page_number,
            bbox=bbox,
            class_name=class_name,
            confidence=confidence,
            content=generated_text[0]
        )