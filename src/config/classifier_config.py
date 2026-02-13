from dataclasses import dataclass, field
from typing import List
import yaml

@dataclass
class ClassifierConfig:
    model_name: str = "yolov12l-doclaynet.pt"
    labels : List[str] = field(default_factory=lambda: ["text","table", "picture", "caption", "section-header", "footnote", "formula", "table", "list-item", "page-header", "page-footer", "title", "scanned-image"])
    tolerance : int = 10
    device: str = "cpu"

    @classmethod
    def from_dict(cls, config: dict):
        return cls(**config)

    @classmethod
    def from_yaml(cls, path: str):
        return cls.from_dict(config=yaml.safe_load(open(path)))