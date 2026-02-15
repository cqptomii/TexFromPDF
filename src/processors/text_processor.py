import fitz
from PIL import Image
from pathlib import Path
from src.utils.bounding_box import sort_blocks_by_position
from src.processors import BaseProcessor
from src.datamodel import TextModel
from src.ocr import FormulaDetection, FormulaRecognition

class TextProcessor(BaseProcessor):
    def __init__(self, output_dir : Path):
        super().__init__()

        self._formula_detector = FormulaDetection()
        self._formula_recognizer = FormulaRecognition()
        self._output_dir = output_dir

    def _identified_bbox_mask(self, image_bbox, blocks_list: list):
        ix1, iy1, ix2, iy2 = image_bbox

        blocks = []
        for bbox in blocks_list:
            if not bbox or len(bbox) != 4:
                continue

            x1, y1, x2, y2 = bbox
            x1, x2 = min(x1, x2), max(x1, x2)
            y1, y2 = min(y1, y2), max(y1, y2)

            if x2 > ix1 and x1 < ix2:
                blocks.append((x1, y1, x2, y2))

        blocks.sort(key=lambda b: b[0])

        result = []

        current_x = ix1

        for x1, y1, x2, y2 in blocks:
            if x1 > current_x:
                result.append((current_x, iy1, x1, iy2))

            current_x = max(current_x, x2)

        if current_x < ix2:
            result.append((current_x, iy1, ix2, iy2))

        return result
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
        img = page.get_pixmap(matrix=fitz.Matrix(2.0, 2.0), clip=rect)
        img = Image.frombytes("RGB", [img.width, img.height], img.samples)

        ## Extract the text with PyMuPDF
        initial_ocr_text = page.get_textbox(rect=rect)

        ## Check if there is any formulas in the text
        formula_detected = self._formula_detector.detect(img)

        print(f"Detected {len(formula_detected)} formula(s) in the text block")

        if not formula_detected or class_name.lower() in ["page-header", "page-footer"]:
            print(f"No formulas detected, using simple OCR text")
            return TextModel(
                page=page_number,
                bbox=rect,
                class_name=block.get("class_name", "text"),
                confidence=block.get("confidence", 0),
                content=initial_ocr_text.strip()
            )

        ## Identified zones that are not covered by the defined bbox
        zones = self._identified_bbox_mask(
            image_bbox=rect,
            blocks_list=formula_detected
        )

        print(f"Image bbox : {rect}")
        for i, zone in enumerate(zones):
            print(f"Zone {i} : {zone}")

        mixed_blocks = []
        ## Extract the content of each zone uncovered by the formulas
        for zone in zones:
            content = page.get_textbox(rect=fitz.Rect(zone[0],zone[1], zone[2], zone[3]))

            mixed_blocks.append(
                {
                    "class_name": "text",
                    "content": content,
                    "bbox_pdf": zone
                }
            )

        for i, formula_block in enumerate(formula_detected):
            bbox = formula_block["bbox"]

            img_formula = img.crop(bbox)
            formula_text = self._formula_recognizer.recognize(img_formula)

            if formula_text and len(formula_text) > 0:
                formula_latex = formula_text[0]
                print(f"Formula {i + 1}: {formula_latex}")

                mixed_blocks.append({
                    "class_name": "formula",
                    "content": formula_latex,
                    "bbox_pdf": bbox
                })

        ## Sort blocks
        sorted_blocks = sort_blocks_by_position(mixed_blocks)

        ocr_text : str = ""
        ## Merge content line by line
        for block in sorted_blocks:
            if block["class_name"] == "formula":
                ocr_text += f" $${block['content']}$$"
            else:
                ocr_text += f" {block['content']}"

        # Retourner le résultat selon le format attendu
        return TextModel(
            page=page_number,
            bbox=rect,
            class_name=block.get("class_name", "text"),
            confidence=block.get("confidence", 0),
            content=ocr_text
        )

