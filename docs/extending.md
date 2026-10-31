# Extending the project

## Adding a new block type

Example: process `Caption` blocks separately from text.

### 1. Create the data model

In `src/datamodel/layout_blocks/`, inherit from `BaseModel` and implement the three abstract methods:

```python
from dataclasses import dataclass
from src.datamodel.layout_blocks.base_model import BaseModel

@dataclass
class CaptionModel(BaseModel):
    content: str

    def to_dict(self):
        return self.__dict__

    def to_markdown(self):
        return f"*{self.content}*\n"

    def to_html(self):
        return f"<figcaption>{self.content}</figcaption>"
```

Export it in `src/datamodel/layout_blocks/__init__.py` and `src/datamodel/__init__.py`.

### 2. Create the processor

In `src/processors/`, inherit from `BaseProcessor`:

```python
from src.processors import BaseProcessor
from src.datamodel import CaptionModel

class CaptionProcessor(BaseProcessor):
    def process(self, page, page_number: int, block: dict) -> CaptionModel:
        bbox = block["bbox_pdf"]
        return CaptionModel(
            page=page_number,
            class_name=block.get("class_name", "caption"),
            confidence=block.get("confidence", 0),
            bbox=bbox,
            content=page.get_textbox(bbox).strip(),
        )
```

Add it to `src/processors/__init__.py`.

### 3. Wire the routing

In `LayoutBlockProcessor.__init__`, instantiate the processor; in `process()`, add a branch:

```python
elif class_name == "caption":
    dict_generated = self._caption_processor.process(page, page_number, block)
```

## Adding an export format

Exports rely on polymorphism: each block implements `to_<format>()`, `Page` concatenates the blocks and `Document` concatenates the pages.

1. Add `to_latex()` (for example) to `BaseModel` and to each block model.
2. Add `to_latex()` to `Page` and `Document`.
3. Add a method and an option (`save_latex`) to `ContentExtractor` and `MainConfig`.

## Using another layout model

1. Place the `.pt` file (YOLO, DocLayNet classes) in `models/layout_detection/`.
2. Pass `model_name="my_model.pt"` to `ContentExtractor`.

If the class set differs, adapt `ClassifierConfig.labels` and the routing in `LayoutBlockProcessor`.

## Using PaddleOCR-VL for other tasks

`VlmImageRecognition` already accepts the `table`, `formula`, `chart`, `spotting` and `seal` tasks. To recognize a scanned table instead of running a generic OCR, create a processor that instantiates `VlmImageRecognition(task="table")`.

## Code conventions

- One processor per block type, knowing only `page`, `page_number` and the block dictionary.
- Coordinates handled by processors are **PDF points** (`bbox_pdf`).
- Block models always expose `to_dict()`, `to_markdown()` and `to_html()`.
- Debug images are written under `predictions/page_XXXX/<type>/`.
- Internal imports use the `src.` prefix.
