import torch
from transformers import AutoModel, AutoProcessor
from PIL import Image

class VlmImageRecognition:


    def __init__(self, model_name: str = "PaddlePaddle/PaddleOCR-VL-1.5", device: str = "cpu", task : str = "ocr"):

        self._model_name = model_name
        self._device = device
        self._task = task

        if self._device in ["cuda", "gpu"]:
            if not torch.cuda.is_available():
                self._device = "cpu"
                print(f"CUDA is not available. Using CPU instead for VLM model : {model_name}")

        self._prompts = {
            "ocr": "OCR:",
            "table": "Table Recognition:",
            "formula": "Formula Recognition:",
            "chart": "Chart Recognition:",
            "spotting": "Spotting:",
            "seal": "Seal Recognition:",
        }

        ## Load the model
        self._load_model()

    def _load_model(self):
        self._model = AutoModel.from_pretrained(
            self._model_name,
            dtype=torch.bfloat16 if self._device == "cuda" else torch.float32,
            trust_remote_code=True
        ).to(self._device).eval()
        self._processor = AutoProcessor.from_pretrained(
            self._model_name,
            use_fast=True,
            trust_remote_code=True
        )


    def recognize(self, img):

        orig_w, orig_h = img.size
        spotting_upscale_threshold = 1500

        process_img = img
        if self._task == "spotting" and orig_w < spotting_upscale_threshold and orig_h < spotting_upscale_threshold:
            process_w, process_h = orig_w * 2, orig_h * 2
            try:
                resample_filter = Image.Resampling.LANCZOS
            except AttributeError:
                resample_filter = Image.LANCZOS
            process_img = img.resize((process_w, process_h), resample_filter)

        # Set max_pixels: use 1605632 for spotting, otherwise use default ~1M pixels
        max_pixels = 2048 * 28 * 28 if self._task == "spotting" else 1280 * 28 * 28

        messages = [
            {
                "role": "user",
                "content": [
                    {"type": "image", "image": process_img},
                    {"type": "text", "text": self._prompts[self._task]},
                ]
            }
        ]

        inputs = self._processor.apply_chat_template(
            messages,
            add_generation_prompt=True,
            tokenize=True,
            return_dict=True,
            return_tensors="pt",
            images_kwargs={"size": {"shortest_edge": self._processor.image_processor.min_pixels, "longest_edge": max_pixels}},
        ).to(self._model.device)

        outputs = self._model.generate(**inputs, max_new_tokens=512)
        content = self._processor.decode(outputs[0][inputs["input_ids"].shape[-1]:-1])

        return content

