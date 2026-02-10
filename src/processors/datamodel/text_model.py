from dataclasses import dataclass

from .base_model import BaseModel


@dataclass
class TextModel(BaseModel):
    content: str

    def to_dict(self):
        return self.__dict__

