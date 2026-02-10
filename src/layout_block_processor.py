from time import time

from processors import *
import fitz, os, json
from pathlib import Path
class LayoutBlockProcessor:

    def __init__(self, pdf_path: str,  output_dir : str = None):

        self._text_processor = TextProcessor()
        self._table_processor = TableProcessor()
        self._image_processor = ImageProcessor()
        self._math_processor = MathProcessor()
        self._scanned_image_processor = TextImageProcessor()

        self._process_pdf_path = pdf_path
        self._output_dir = output_dir if output_dir is not None else os.path.join(os.path.join(
            os.path.dirname(os.path.dirname(__file__)), "output"), f"{Path(pdf_path).stem}_{time():.02f}")

    def process(self, document : list[dict]):
        """
            Method that processes each block of each page of a pdf
            Generate a dictionary containing content of each block extracted from the pdf
        :param document: (list[dict]) List of pages extracted from a pdf
        :return: (dict)
        """
        doc_content = []

        doc = fitz.open(self._process_pdf_path)
        for page, page_dict in zip(doc, document):
            page_number = page_dict.get("page_number", -1)
            predicted_blocks = page_dict.get("blocks", [])

            page_content = []
            ## Process each predicted block of the page
            for block in predicted_blocks:
                class_name = block.get("class_name", "").lower()

                ## Determine the process to use within the block
                if class_name == "table":
                    dict_generated = self._table_processor.process(page, page_number, block)
                elif class_name == "math":
                    dict_generated = self._math_processor.process(page, page_number, block)
                elif class_name == "picture":
                     dict_generated = self._image_processor.process(page, page_number, block)
                elif class_name == "image_scanned":
                    dict_generated = self._scanned_image_processor.process(page, page_number, block)
                else:
                    dict_generated = self._text_processor.process(page, page_number, block)

                page_content.append(dict_generated)


            doc_content.append(page_content)

        ## Save the processed document
        with open(self._output_dir + "/extracted_content.json", "w") as f:
            json.dump(doc_content, f, indent=2)


        return doc_content










