import os, json
from pathlib import Path
from time import time
from src.content_classifier import ContentClassifier
from src.config import MainConfig, ClassifierConfig
from src.layout_block_processor import LayoutBlockProcessor
from src.utils.numpy_encoder import NumpyJSONEncoder

class ContentExtractor:

    def __init__(self, pdf_path: str, output_dir: str, device: str = "cpu", model_name: str = "yolov12l-doclaynet.pt",  verbose : bool = False, **kwargs):
        self._pdf_path = Path(pdf_path)
        base_dir = output_dir if output_dir is not None else os.path.join(os.path.dirname(os.path.dirname(__file__)), "output")

        classifier_config = ClassifierConfig(
            device=device,
            model_name=model_name
        )

        ## Store configuration
        self._config = MainConfig.from_dict(
            {
                "classifier_config": classifier_config,
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
            table_settings=self._config.table_settings
        )

    def set_pdf_path(self, pdf_path: str):
        if not os.path.exists(pdf_path):
            raise FileNotFoundError(f"PDF file not found at {pdf_path}")

        self._pdf_path = Path(pdf_path)
    def extract(self):

        ## Classify the PDF
        classification_dict = self._classifier.classify(
            pdf_path=self._pdf_path
        )

        ## Extract the layout blocks
        extracted_content = self._processor.process(classification_dict)

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

    def to_markdown(self, page_number : int = 0):
        """
            Method that returns the markdown representation of the extracted content
            If page_number is specified, returns the markdown representation of the corresponding page
            Else returns the concatenation of the markdown representation of all pages
        :param page_number: (int) Page number to return
        :return: None
        """
        markdown_content = self.extract().to_markdown(
            page_number=page_number
        )

        ## Save the extracted content to a file
        file_name = f"{self._pdf_path.stem}.md" if page_number == 0 else f"{self._pdf_path.stem}_{page_number}.md"
        with open(os.path.join(self._config.output_dir, file_name), "w", encoding="utf-8") as f:
            f.write(markdown_content)
    def to_html(self, page_number : int = 0):
        """
            Method that returns the html representation of the extracted content
            If page_number is specified, returns the html representation of the corresponding page
            Else returns the concatenation of the html representation of all pages
        :param page_number: (int) Page number to return
        :return: None
        """
        html_content = self.extract().to_html(
            page_number=page_number
        )

        ## Save the extracted content to a file
        file_name = f"{self._pdf_path.stem}.html" if page_number == 0 else f"{self._pdf_path.stem}_{page_number}.html"
        with open(os.path.join(self._config.output_dir, file_name), "w", encoding="utf-8") as f:
            f.write(html_content)


if __name__ == "__main__":
    extractor = ContentExtractor(
        pdf_path="D:/apprentissage/TexFromPDF/data/sample_pdfs/page_010.pdf",
        output_dir="D:/apprentissage/TexFromPDF/output"
    )

    extractor.to_markdown()