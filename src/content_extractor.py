import os, json
from pathlib import Path
from time import time

import torch

from src.content_classifier import ContentClassifier
from src.config import MainConfig
from src.datamodel import Document
from src.layout_block_processor import LayoutBlockProcessor
from src.utils.numpy_encoder import NumpyJSONEncoder


class ContentExtractor:

    def __init__(self, pdf_path: str, output_dir: str, device: str = "cpu", model_name: str = "yolov12l-doclaynet.pt",  verbose : bool = False, **kwargs):
        self._pdf_path = Path(pdf_path)
        base_dir = output_dir if output_dir is not None else os.path.join(os.path.dirname(os.path.dirname(__file__)), "output")

        ## Fallback on CPU if CUDA is requested but not available
        if device in ["cuda", "gpu"] and not torch.cuda.is_available():
            print("CUDA is not available, using CPU instead.")
            device = "cpu"

        ## Store configuration
        self._config = MainConfig.from_dict(
            {
                "classifier_config": {"device": device, "model_name": model_name},
                "output_dir": os.path.join(base_dir, f"{self._pdf_path.stem}_{time():.02f}"),
                "verbose": verbose,
                **kwargs
            }
        )

        self._classifier = ContentClassifier(
            config=self._config
        )
        self._processor = LayoutBlockProcessor(
            pdf_path=self._pdf_path,
            output_dir=self._config.output_dir,
            table_settings=self._config.table_settings,
            device=device
        )

        ## Last extracted document (avoid running the pipeline several times)
        self._document: Document | None = None

    def set_pdf_path(self, pdf_path: str):
        if not os.path.exists(pdf_path):
            raise FileNotFoundError(f"PDF file not found at {pdf_path}")

        self._pdf_path = Path(pdf_path)
        self._processor.set_pdf_path(self._pdf_path)
        self._document = None

    def extract(self) -> Document:
        """
            Method that runs the complete pipeline (classification + extraction) on the pdf
            The result is saved into a JSON file and optionally exported to MD and HTML formats
        :return: (Document) Extracted content
        """
        ## Classify the PDF
        classification_dict = self._classifier.classify(
            pdf_path=self._pdf_path
        )

        ## Extract the layout blocks
        extracted_content = self._processor.process(classification_dict)
        self._document = extracted_content

        ## Save the extracted content to a JSON file
        with open(os.path.join(self._config.output_dir, "extracted_content.json"), "w", encoding="utf-8") as f:
            json.dump(extracted_content.to_dict(), f, indent=2, cls=NumpyJSONEncoder, ensure_ascii=False)

        ## Convert the extracted content to MD and HTML format and save them to a file
        if self._config.save_md:
            print("Saving extracted content to MD format...")
            self.to_markdown()

        if self._config.save_html:
            print("Saving extracted content to HTML format...")
            self.to_html()

        ## Return the extracted content
        return extracted_content

    def _get_document(self) -> Document:
        """
            Method that returns the last extracted document, runs the extraction if there is none
        """
        if self._document is None:
            self.extract()

        return self._document

    def to_markdown(self, page_number : int = 0):
        """
            Method that saves the markdown representation of the extracted content
            If page_number (starting at 1) is specified, only the corresponding page is saved
            Else the concatenation of all pages is saved
        :param page_number: (int) Page number to save, 0 for all pages
        :return: (str) Markdown content
        """
        markdown_content = self._get_document().to_markdown(
            page_number=page_number
        )

        ## Save the extracted content to a file
        file_name = f"{self._pdf_path.stem}.md" if page_number == 0 else f"{self._pdf_path.stem}_{page_number}.md"
        with open(os.path.join(self._config.output_dir, file_name), "w", encoding="utf-8") as f:
            f.write(markdown_content)

        return markdown_content

    def to_html(self, page_number : int = 0):
        """
            Method that saves the html representation of the extracted content
            If page_number (starting at 1) is specified, only the corresponding page is saved
            Else the concatenation of all pages is saved
        :param page_number: (int) Page number to save, 0 for all pages
        :return: (str) Html content
        """
        html_content = self._get_document().to_html(
            page_number=page_number
        )

        ## Save the extracted content to a file
        file_name = f"{self._pdf_path.stem}.html" if page_number == 0 else f"{self._pdf_path.stem}_{page_number}.html"
        with open(os.path.join(self._config.output_dir, file_name), "w", encoding="utf-8") as f:
            f.write(html_content)

        return html_content
