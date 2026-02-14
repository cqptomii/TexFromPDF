import fitz, os
from PIL import Image, ImageDraw, ImageFont
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


        img = page.get_pixmap(matrix=fitz.Matrix(2.0, 2.0), clip=rect)
        img = Image.frombytes("RGB", [img.width, img.height], img.samples)

        initial_ocr_text = page.get_textbox(rect=rect)
        complex_ocr_text = ""

        ## Check if there is any formulas in the text
        blocks = self._formula_detector.detect(img)

        ## For each block, use the FormulaRecognition model to extract the formula
        for block in blocks:

            img_block = img.crop(block["bbox"])

            text = self._formula_recognizer.recognize(img_block)

            print(f"Text: {text}")
            complex_ocr_text += text[0] + " "


        ocr_text = complex_ocr_text.strip() if complex_ocr_text else initial_ocr_text.strip()


        print(f"Naive OCR: {initial_ocr_text}")
        print(f"Complex OCR: {complex_ocr_text}")
        self._show_predictions(
            page=page,
            zone=rect,
            zone_id=block.get("id", -1),
            page_number=page_number,
            blocks=blocks
        )

        # Retourner le résultat selon le format attendu
        return TextModel(
            page=page_number,
            bbox=rect,
            class_name=block.get("class_name", "text"),
            confidence=block.get("confidence", 0),
            content=ocr_text
        )

