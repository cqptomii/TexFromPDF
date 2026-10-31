# Usage

## Command line

The entry point is `src/texparser.py`. It scans a folder **recursively**, finds all `*.pdf` files and runs the extraction on each of them.

```bash
python src/texparser.py --pdf_dir ./data/sample_pdfs --output_dir ./output --device cuda
```

> Run the command from the project root. The script adds the root to `sys.path` itself, which enables the `from src...` imports used throughout the code.

### Options

| Option | Type | Default | Description |
|---|---|---|---|
| `--pdf_dir` | `str` | **required** | Folder containing the PDFs to process (searched recursively) |
| `--output_dir` | `str` | **required** | Root folder for the outputs |
| `--device` | `str` | `cuda` | Inference device: `cuda` or `cpu` (automatic fallback to CPU if CUDA is unavailable) |
| `--verbose` | flag | disabled | Prints detailed information (orientation, blocks, bboxes…) |
| `--save_md` / `--no-save_md` | flag | enabled | Enables / disables the Markdown export |
| `--save_html` / `--no-save_html` | flag | disabled | Enables / disables the HTML export |

Example without Markdown export, with HTML export:

```bash
python src/texparser.py --pdf_dir ./data --output_dir ./output --no-save_md --save_html
```

## Python API

```python
from src.content_extractor import ContentExtractor

extractor = ContentExtractor(
    pdf_path="data/sample_pdfs/page_010.pdf",
    output_dir="output",
    device="cuda",                       # or "cpu"
    model_name="yolov12l-doclaynet.pt",  # model located in models/layout_detection/
    verbose=False,
    save_md=True,
    save_html=False,
)

document = extractor.extract()   # returns a Document object (the pipeline runs only once)

extractor.to_markdown()          # writes <name>.md with all pages
extractor.to_markdown(2)         # writes <name>_2.md with page 2 only (1-based numbering)
extractor.to_html()              # writes <name>.html
```

`to_markdown()` and `to_html()` reuse the last extracted `Document`; they only call `extract()` if no extraction has been done yet.

Additional parameters passed through `**kwargs` feed `MainConfig` (for example `save_md`, `save_html`, `table_settings`). See [configuration.md](configuration.md).

## Output folder

For each PDF, a sub-folder is created: `<output_dir>/<pdf_name>_<timestamp>/`.

```
output/page_004_1772395646.52/
├── classifications.json          # blocks detected by YOLO, page by page
├── extracted_content.json        # extracted content (structured format)
├── page_004.md                   # Markdown export (if save_md)
├── page_004.html                 # HTML export (if save_html)
├── rasterized_pages/
│   └── page_0001/
│       ├── page_0001.png         # rasterized page (450 DPI)
│       └── page_0001.json        # page metadata
├── predictions/
│   └── page_0001/
│       ├── page_0001.jpg         # annotated YOLO predictions (saved by ultralytics)
│       ├── debug/page_0001_annotated.png   # PDF page with drawn blocks
│       ├── table/                # table debug images
│       ├── formula/              # cropped formula images
│       └── scanned_image/        # scanned-area images sent to the OCR
└── text/                         # TextProcessor debug images
```

### `classifications.json`

List of pages, each with its blocks sorted in reading order:

```json
{
  "page_index": 0,
  "page_number": 1,
  "image_path": "./output/.../page_0001.png",
  "image_dimensions": {"width": 5262, "height": 3721},
  "pdf_dimensions": {"width": 841.92, "height": 595.32},
  "page_rotation": 0,
  "blocks": [
    {
      "id": 0,
      "class_id": 8,
      "class_name": "Table",
      "confidence": 0.76,
      "bbox_image": [315.0, 220.0, 3509.0, 612.0],
      "bbox_pdf": [50.3, 35.3, 561.5, 97.9]
    }
  ],
  "removed_blocks": []
}
```

### `extracted_content.json`

See [datamodel.md](datamodel.md) for details. Real excerpt (table):

```json
{
  "id": "37937cde681a45109a4b60507831b5b2",
  "pages": [
    {
      "page_number": 1,
      "blocks_extracted": [
        {
          "page": 1,
          "class_name": "Table",
          "confidence": 0.765,
          "bbox": [50.3, 35.3, 561.5, 97.9],
          "structured_content": [["", "OPERATIONS\nINSTRUCTION", "..."]]
        }
      ]
    }
  ]
}
```

### Markdown export

Example of the produced output (tables as HTML inside the Markdown, titles as `##`):

```markdown
<table><tr><td>...</td></tr></table>

## 0.  ASPECTS PARTICULIERS DE SURETE, SECURITE,  ENVIRONNEMENT

• Respect des consignes d'accès aux locaux électriques.
```
