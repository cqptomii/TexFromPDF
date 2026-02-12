import os
from pathlib import Path

import fitz
from PIL import Image
import torch
from transformers import AutoProcessor, AutoModelForImageTextToText

from src.processors import BaseProcessor
from src.datamodel import TextModel

class ScannedImageProcessor(BaseProcessor):
    def __init__(self, output_dir: Path = None, model_name: str = "PaddlePaddle/PaddleOCR-VL-1.50", device: str = "cpu", task : str = "ocr"):
        super().__init__()

        self._output_dir = output_dir if output_dir is not None else os.path.join(os.path.dirname(os.path.dirname(__file__)), "output")
        self._model_name = model_name
        self._device = device
        self._task = task # Options: 'ocr' | 'table' | 'chart' | 'formula' | 'spotting' | 'seal'

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

        orig_w, orig_h = image.size
        spotting_upscale_threshold = 1500

        if self._task == "spotting" and orig_w < spotting_upscale_threshold and orig_h < spotting_upscale_threshold:
            process_w, process_h = orig_w * 2, orig_h * 2
            try:
                resample_filter = Image.Resampling.LANCZOS
            except AttributeError:
                resample_filter = Image.LANCZOS
            image = image.resize((process_w, process_h), resample_filter)

        # Set max_pixels: use 1605632 for spotting, otherwise use default ~1M pixels
        max_pixels = 2048 * 28 * 28 if self._task == "spotting" else 1280 * 28 * 28

        # -------- Inference --------
        if self._device in ["cuda", "gpu"]:
            if not torch.cuda.is_available():
                self._device = "cpu"

        prompts = {
            "ocr": "OCR:",
            "table": "Table Recognition:",
            "formula": "Formula Recognition:",
            "chart": "Chart Recognition:",
            "spotting": "Spotting:",
            "seal": "Seal Recognition:",
        }

        model = AutoModelForImageTextToText.from_pretrained(self._model_name, torch_dtype=torch.bfloat16).to(self._device).eval()
        processor = AutoProcessor.from_pretrained(self._model_name)

        messages = [
            {
                "role": "user",
                "content": [
                    {"type": "image", "image": image},
                    {"type": "text", "text": prompts[self._task]},
                ]
            }
        ]
        inputs = processor.apply_chat_template(
            messages,
            add_generation_prompt=True,
            tokenize=True,
            return_dict=True,
            return_tensors="pt",
            images_kwargs={"size": {"shortest_edge": processor.image_processor.min_pixels, "longest_edge": max_pixels}},
        ).to(model.device)

        outputs = model.generate(**inputs, max_new_tokens=512)
        content = processor.decode(outputs[0][inputs["input_ids"].shape[-1]:-1])


        return TextModel(
            page=page_number,
            bbox=bbox,
            class_name=class_name,
            confidence=confidence,
            content=content
        )

