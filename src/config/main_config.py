import yaml
from dataclasses import dataclass
from src.config import ClassifierConfig


@dataclass
class MainConfig:
    classifier_config: ClassifierConfig
    output_dir: str
    save_md: bool = False
    save_html: bool = False
    verbose: bool = False

    @classmethod
    def from_dict(cls, config: dict):
        return cls(**config)

    @classmethod
    def from_yaml(cls, path: str):
        return cls.from_dict(config=yaml.safe_load(open(path)))
