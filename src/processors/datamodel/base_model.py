from dataclasses import dataclass

@dataclass
class BaseModel:
    page: int
    class_name: str
    confidence: float
    bbox: list