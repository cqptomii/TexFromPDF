from dataclasses import dataclass
from .base_model import BaseModel

@dataclass
class TableModel(BaseModel):
    structured_content: list

    def to_dict(self):
        return self.__dict__