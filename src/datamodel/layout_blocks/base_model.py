from dataclasses import dataclass
from abc import ABC, abstractmethod
from typing import List, Any

@dataclass
class BaseModel(ABC):
    page: int
    class_name: str
    confidence: float
    bbox: List[Any]

    @abstractmethod
    def to_dict(self):
        pass
    @abstractmethod
    def to_markdown(self):
        pass
    @abstractmethod
    def to_html(self):
        pass