from dataclasses import dataclass
from .base_model import BaseModel

@dataclass
class ImageModel(BaseModel):
    image_base64: str


    def to_dict(self):
        return self.__dict__
