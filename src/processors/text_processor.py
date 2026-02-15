import fitz, cv2, os, re,  numpy as np
from PIL import Image
from pathlib import Path
from src.processors import BaseProcessor
from src.datamodel import TextModel
from src.ocr import FormulaDetection, FormulaRecognition

class TextProcessor(BaseProcessor):
    def __init__(self, output_dir : Path):
        super().__init__()

        self._formula_detector = FormulaDetection()
        self._formula_recognizer = FormulaRecognition()
        self._output_dir = output_dir

    def _show_debug(self, image, bbox_list, block_id: int, show : bool = False, save : bool = True):
        if not isinstance(image, np.ndarray):
            image = np.array(image)
            image = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)

        debug_img = image.copy()

        for bbox in bbox_list:
            if not bbox or len(bbox) != 4:
                continue

            x1, y1, x2, y2 = bbox

            x1, x2 = int(min(x1, x2)), int(max(x1, x2))
            y1, y2 = int(min(y1, y2)), int(max(y1, y2))

            cv2.rectangle(
                debug_img,
                (x1, y1),
                (x2, y2),
                (0, 0, 255),  # rouge
                2  # épaisseur
            )

        if show:
            cv2.imshow("DEBUG BBOX", debug_img)
            cv2.waitKey(0)
            cv2.destroyAllWindows()

        if save:
            dir = self._output_dir / "text"
            os.makedirs(dir, exist_ok=True)

            cv2.imwrite(str(dir / f"image_{block_id}.jpg"), debug_img)


    def process(self, page, page_number: int, block: dict) -> TextModel:
        """
            Method that processes a text block
            Extract all the text from the bbox in the given page
        :param page: ('fitz.Page') Page to process
        :param page_number: (int) Page number
        :param block: (dict) Block to process
        :return: (dict) Dictionary containing the text and its classification
        """
        rect = block.get("bbox_pdf", [])
        class_name = block.get("class_name", "")


        ## Extract the image associated to the zone
        scale = 2.0
        img = page.get_pixmap(matrix=fitz.Matrix(2.0, 2.0), clip=rect)
        img = Image.frombytes("RGB", [img.width, img.height], img.samples)

        ## Extract the text with PyMuPDF
        initial_ocr_text : str = page.get_textbox(rect=rect)

        ## Check if there is any formulas in the text
        formula_detected = self._formula_detector.detect(img)

        bbox_list = []
        for formula_detection in formula_detected:
            bbox_list.append(formula_detection["bbox"])

        self._show_debug(
            image=img,
            bbox_list=bbox_list,
            block_id=block["id"]
        )

        if not formula_detected or class_name.lower() in ["page-header", "page-footer"]:
            print(f"No formulas detected, using simple OCR text")
            return TextModel(
                page=page_number,
                bbox=rect,
                class_name=block.get("class_name", "text"),
                confidence=block.get("confidence", 0),
                content=initial_ocr_text.strip()
            )

        print(f"Detected {len(formula_detected)} formula(s) in the text block")
        ## Replace text content from the global text with the math recognition prediction
        for formula in formula_detected:
            bbox_img = formula["bbox"]

            x1 = rect[0] + bbox_img[0] / scale - 1
            y1 = rect[1] + bbox_img[1] / scale - 1
            x2 = rect[0] + bbox_img[2] / scale - 1
            y2 = rect[1] + bbox_img[3] / scale - 1

            formula_rect_pdf = [x1, y1, x2, y2]

            naive_content_extracted : str = page.get_textbox(rect=formula_rect_pdf)
            normalized_content  = naive_content_extracted.replace(" ", "")
            print(f"Naive content extracted: {naive_content_extracted}")
            if len(normalized_content) == 1:
                print(f"Skip formula {normalized_content}")
                continue

            ## Recognize the formula in the given bbox
            img_formula = img.crop(bbox_img)
            formula_text = self._formula_recognizer.recognize(img_formula)
            print(f"Formula text: {formula_text}")
            initial_ocr_text = initial_ocr_text.replace(naive_content_extracted, f" ${formula_text[0]}$ ")


        ## Replace \n by spaces
        initial_ocr_text = initial_ocr_text.replace("\n", " ")
        # Retourner le résultat selon le format attendu
        return TextModel(
            page=page_number,
            bbox=rect,
            class_name=block.get("class_name", "text"),
            confidence=block.get("confidence", 0),
            content=initial_ocr_text.strip()
        )

