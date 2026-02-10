from dataclasses import dataclass
from typing import List, Any

@dataclass
class BaseModel:
    page: int
    class_name: str
    confidence: float
    bbox: List[Any]

    def to_dict(self):
        return self.__dict__