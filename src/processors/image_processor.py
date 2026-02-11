import fitz, base64, io
from PIL import Image
from src.processors import BaseProcessor
from src.processors.datamodel import ImageModel

class ImageProcessor(BaseProcessor):

    def __init__(self):
        super().__init__()

    def process(self, page, page_number: int, block: dict) -> ImageModel:
        """
            Method that processes an image block
            The image is extracted from the bbox in the given page and converted into bas64 format
        :param page: ('fitz.Page') Page to process
        :param page_number: (int) Page number
        :param block: (dict) Block to process
        :return: (ImageModel) dataclass containing the image and its classification
        """
        bbox = block.get("bbox_pdf", [])
        confidence = block.get("confidence", 0)
        class_name = block.get("class_name", "Picture")

        rect = fitz.Rect(float(bbox[0]), float(bbox[1]), float(bbox[2]), float(bbox[3]))

        ## Extract the image from the page
        mat = fitz.Matrix(2.0, 2.0)
        pix = page.get_pixmap(matrix=mat, clip=rect)

        img_data = pix.tobytes("png")
        image = Image.open(io.BytesIO(img_data))

        ## Convert the image into base64 format
        img_bytes = io.BytesIO()
        image.save(img_bytes, format="PNG")
        img_str = base64.b64encode(img_bytes.getvalue()).decode("utf-8")

        return ImageModel(
            page=page_number,
            class_name=class_name,
            confidence=confidence,
            bbox=bbox,
            image_base64=img_str
        )

