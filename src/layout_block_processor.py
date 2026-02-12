from time import time
import fitz, os, json
from pathlib import Path

import hashlib
from processors import *
from src.utils.numpy_encoder import NumpyJSONEncoder
from src.datamodel import Page, Document

class LayoutBlockProcessor:

    def __init__(self, pdf_path: Path,  output_dir : str = None, table_settings : dict = None):

        self._text_processor = TextProcessor()
        self._table_processor = TableProcessor(
            output_dir=Path(output_dir),
            table_settings=table_settings
        )
        self._image_processor = ImageProcessor()
        self._math_processor = MathProcessor(
            output_dir=Path(output_dir)
        )
        self._scanned_image_processor = ScannedImageProcessor(
            output_dir=Path(output_dir),
            device="cuda"
        )

        self._process_pdf_path = pdf_path
        self._output_dir = output_dir if output_dir is not None else os.path.join(os.path.join(
            os.path.dirname(os.path.dirname(__file__)), "output"), f"{self._process_pdf_path.stem}_{time():.02f}")

    def process(self, document : list[dict]):
        """
            Method that processes each block of each page of a pdf
            Generate a dictionary containing content of each block extracted from the pdf
        :param document: (list[dict]) List of pages extracted from a pdf
        :return: (dict)
        """
        doc = fitz.open(self._process_pdf_path)
        doc_content = Document(
            id= hashlib.md5(self._process_pdf_path.read_bytes()).hexdigest(),
            pages=[]
        )

        for page, page_dict in zip(doc, document):
            print("=" * 30)
            print(f"Processing page {page_dict.get('page_number', -1)}")
            print("=" * 30)
            page_number = page_dict.get("page_number", -1)
            predicted_blocks = page_dict.get("blocks", [])

            page_content = Page(
                page_number=page_number,
                content_blocks=[]
            )

            ## Process each predicted block of the page
            for i, block in enumerate(predicted_blocks):
                print(f"Processing block  {i} :{block.get('class_name', '')}")
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

                print(f"Generated dictionary: {dict_generated}")

                ## Convert Datamodel Class to Dictionary
                if dict_generated:
                    page_content.content_blocks.append(dict_generated)


            doc_content.pages.append(page_content)

        print("=" * 30)
        print("Generated content:", doc_content)
        print("=" * 30)
        ## Save the processed document to JSON file
        with open(self._output_dir + "/extracted_content.json", "w", encoding="utf-8") as f:
            json.dump(doc_content.to_dict(), f, indent=2, cls=NumpyJSONEncoder, ensure_ascii=False)


        return doc_content










