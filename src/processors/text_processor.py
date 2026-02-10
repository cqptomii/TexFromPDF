from src.processors import BaseProcessor
from src.processors.datamodel import TextModel

class TextProcessor(BaseProcessor):
    def __init__(self):
        super().__init__()

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
        text = page.get_textbox(rect=rect)

        text = text.strip() if text else ""

        # Retourner le résultat selon le format attendu
        return TextModel(
            page=page_number,
            bbox=rect,
            class_name=block.get("class_name", "text"),
            confidence=block.get("confidence", 0),
            content=text
        )

