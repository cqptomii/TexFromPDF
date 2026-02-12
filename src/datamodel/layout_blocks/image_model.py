from dataclasses import dataclass
from tkinter.messagebox import RETRY

from src.datamodel.layout_blocks.base_model import BaseModel

@dataclass
class ImageModel(BaseModel):
    image_base64: str

    def to_dict(self):
        return self.__dict__
    def to_markdown(self):
        markdown_image = f"![{self.class_name}](data:image/png;base64,{self.image_base64})"

        return markdown_image
    def to_html(self):
        html_image = f"<img src='data:image/png;base64,{self.image_base64}' alt='{self.class_name}' />"

        return html_image
