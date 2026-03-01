import yaml
from dataclasses import dataclass, field
from src.config import ClassifierConfig

@dataclass
class MainConfig:
    classifier_config: ClassifierConfig
    output_dir: str
    table_settings: dict = field(default_factory=lambda:{
                "strategy": "lines",
                "snap_tolerance": 4,
                "join_tolerance": 4,
                "edge_min_length": 4,
                "intersection_tolerance": 10,
                "text_tolerance": 4
    })
    save_md: bool = False
    save_html: bool = False
    verbose: bool = False

    @classmethod
    def from_dict(cls, config: dict):
        if "classifier_config" in config:
            config["classifier_config"] = ClassifierConfig.from_dict(config["classifier_config"])
        return cls(**config)

    @classmethod
    def from_yaml(cls, path: str):
        config = yaml.safe_load(open(path))
        if "classifier_config" in config:
            config["classifier_config"] = ClassifierConfig.from_dict(config["classifier_config"])
        return cls.from_dict(config=config)
