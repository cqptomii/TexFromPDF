from dataclasses import dataclass
import yaml

@dataclass
class ClassifierConfig:
    model_name: str = "yolov12l-doclaynet.pt"
    device: str = "cpu"

    @classmethod
    def from_dict(cls, config: dict):
        return cls(**config)

    @classmethod
    def from_yaml(cls, path: str):
        return cls.from_dict(config=yaml.safe_load(open(path)))