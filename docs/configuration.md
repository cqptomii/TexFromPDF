# Configuration

The configuration relies on two dataclasses in `src/config/`.

## `ClassifierConfig`

Settings of the classification phase.

| Field | Type | Default | Description |
|---|---|---|---|
| `model_name` | `str` | `"yolov12l-doclaynet.pt"` | Model file in `models/layout_detection/` |
| `device` | `str` | `"cpu"` | `cuda` or `cpu` (`ContentExtractor` forwards the value of `--device`) |
| `labels` | `list[str]` | see below | Classes taken into account when removing redundant blocks |
| `tolerance` | `int` | `10` | Tolerance in points (declared in the configuration, currently unused) |

Default value of `labels`:

```python
["text", "table", "picture", "caption", "section-header", "footnote", "formula",
 "table", "list-item", "page-header", "page-footer", "title", "scanned-image"]
```

## `MainConfig`

| Field | Type | Default | Description |
|---|---|---|---|
| `classifier_config` | `ClassifierConfig` | — | Classifier configuration |
| `output_dir` | `str` | — | Output folder of the document |
| `table_settings` | `dict` | see below | Parameters of `page.find_tables()` |
| `save_md` | `bool` | `False` | Writes the Markdown |
| `save_html` | `bool` | `False` | Writes the HTML |
| `verbose` | `bool` | `False` | Enables detailed logs |

### Default `table_settings`

```python
{
    "strategy": "lines",
    "snap_tolerance": 4,
    "join_tolerance": 4,
    "edge_min_length": 4,
    "intersection_tolerance": 10,
    "text_tolerance": 4,
}
```

These parameters are passed as is to PyMuPDF's [`Page.find_tables`](https://pymupdf.readthedocs.io/en/latest/page.html#Page.find_tables). For tables without borders, try `"strategy": "text"`.

## Building a configuration

### From a dictionary

```python
from src.config import MainConfig

config = MainConfig.from_dict({
    "classifier_config": {"device": "cuda", "model_name": "yolov12l-doclaynet.pt"},
    "output_dir": "output/my_doc",
    "save_md": True,
    "table_settings": {"strategy": "text"},
})
```

### From a YAML file

```yaml
classifier_config:
  device: cuda
  model_name: yolov12l-doclaynet.pt
output_dir: output/my_doc
save_md: true
save_html: false
verbose: false
```

```python
config = MainConfig.from_yaml("config.yaml")
```

## Hard-coded parameters

Some values are not configurable yet and live directly in the code:

| Parameter | Value | Location |
|---|---|---|
| Rasterization DPI | `450` | `ContentClassifier.__init__` |
| YOLO confidence threshold | `0.25` | `ContentClassifier._classify_page` |
| Block crop zoom | `2.0` | processors (`TextProcessor`, `MathProcessor`, `ImageProcessor`, `ScannedImageProcessor`) |
| bbox superimposition / containment tolerance | `10` pt | `utils/bounding_box.py` |
| Line tolerance for block sorting | `10` pt | `sort_blocks_by_position` |
| Scanned page threshold | score ≥ 5 | `utils/scanned.py` |
| Max tokens of the visual OCR | `512` | `VlmImageRecognition.recognize` |
