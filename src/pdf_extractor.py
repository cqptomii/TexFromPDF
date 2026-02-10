import os, json
from pathlib import Path
from time import time
from src.pdf_classifier import PdfClassifier
from src.config import MainConfig, ClassifierConfig
from src.layout_block_processor import LayoutBlockProcessor
from src.utils.numpy_encoder import NumpyJSONEncoder

class PdfExtractor:

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

        self._classifier = PdfClassifier(
            config=self._config
        )
        self._processor = LayoutBlockProcessor(
            pdf_path=self._pdf_path,
            output_dir=self._config.output_dir
        )

    def extract(self):

        ## Classify the pdf
        classification_dict = self._classifier.classify(
            pdf_path=self._pdf_path
        )

        ## Extract the layout blocks
        extracted_content = self._processor.process(classification_dict)

        ## Save the extracted content to a JSON file
        with open(os.path.join(self._config.output_dir, "extracted_content.json"), "w", encoding="utf-8") as f:
            json.dump(extracted_content, f, indent=2, cls=NumpyJSONEncoder, ensure_ascii=False)

        ## Convert the extracted content to MD and HTML format and save them to a file
        if self._config.save_md:
            print("Saving extracted content to MD format...")

        if self._config.save_html:
            print("Saving extracted content to HTML format...")


        ## Return the extracted content
        return extracted_content



if __name__ == "__main__":
    extractor = PdfExtractor(
        pdf_path="D:/apprentissage/TexFromPDF/data/sample_pdfs/page_004.pdf",
        output_dir="D:/apprentissage/TexFromPDF/output"
    )

    content = extractor.extract()