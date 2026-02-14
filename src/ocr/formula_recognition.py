from transformers import TrOCRProcessor
from optimum.onnxruntime import ORTModelForVision2Seq

class FormulaRecognition:

    def __init__(self, model_name: str = "breezedeus/pix2text-mfr-1.5", verbose : bool = False):
        self._ocr_model_name = model_name
        self._verbose = verbose

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

    def recognize(self, img):
        pixel_values = self._processor(images=img, return_tensors="pt").pixel_values
        generated_ids = self._model.generate(pixel_values)
        generated_text = self._processor.batch_decode(generated_ids, skip_special_tokens=True)

        if self._verbose:
            print(f'generated_ids: {generated_ids}, \ngenerated text: {generated_text}')

        return generated_text