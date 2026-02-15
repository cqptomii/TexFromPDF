import torch, os
from cnstd.yolo_detector import YoloDetector
from pathlib import Path
from typing import Optional, Union, Tuple

class FormulaDetector(YoloDetector):
    def __init__(
            self,
            *,
            model_path: Path = None,
            device: Optional[str] = None,
            static_resized_shape: Optional[Union[int, Tuple[int, int]]] = None,
            **kwargs,
    ):
        super().__init__(
            model_path=model_path,
            device=device,
            static_resized_shape=static_resized_shape,
            **kwargs,
        )
class FormulaDetection:

    def __init__(self, model_name: str = "pix2text-mfd-1.5.onnx", device: str = "cuda", verbose : bool = False):

        self._model_name = model_name
        self._verbose = verbose
        self._device = device

        if self._device in ["cuda", "gpu"]:
            if not torch.cuda.is_available():
                self._device = "cpu"
                print("CUDA is not available, using CPU instead.")

        model_path = Path(os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "models/formula", model_name))
        self._mfd = FormulaDetector(
            model_path=model_path,
            device=self._device
        )
    def detect(self,  img, **kwargs):
        img0 = img.convert('RGB')

        ## Extract blocks recognized
        blocks = []

        boxes = self._mfd(img0.copy())
        for box_info in boxes:
            box = box_info['box']
            xmin, ymin, xmax, ymax = (
                box[0][0],
                box[0][1],
                box[2][0],
                box[2][1],
            )
            box_info.pop('box')

            block = {
                "class_name": box_info['type'],
                "confidence": box_info['score'],
                "bbox": [xmin, ymin, xmax, ymax]
            }

            blocks.append(block)

        return blocks
