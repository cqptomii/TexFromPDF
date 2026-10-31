# Known limitations and improvement ideas

This page lists the current limits of the project and the points to watch.

## Limits of the current code

- **Formula recognition on CPU**: `FormulaRecognition` (MFR) runs with ONNX Runtime without any device option. `--device` drives YOLO, formula detection (MFD) and PaddleOCR-VL.
- **`ClassifierConfig.tolerance`** is declared but not used anywhere; bbox tolerances are hard-coded in `utils/bounding_box.py`.
- **`TableProcessor`**:
  - it only processes the first table found in the area;
  - the cleanup of empty columns in the first row iterates over the list while modifying it, which can shift columns on very irregular tables;
  - the HTML `rowspan` / `colspan` merge relies on content equality: two distinct but identical adjacent cells will be merged.
- **`TableModel.to_markdown("json")`** simply returns the cell matrix serialized as JSON.
- **`TextProcessor`**: the `_use_bounding_box` mode (returns a `TextFormulaModel`) is disabled by default and little tested. The debug images in the `text/` folder display bboxes in a coordinate system that is not the one of the whole page.
- **`ScannedImageProcessor`** always uses the generic OCR task (`OCR:`), including for scanned tables.

## Functional limits

- **Reading order**: simple position-based sorting, without explicit column detection.
- **Inline formulas**: the replacement relies on the native text present in the detected bbox; it depends on the quality of the PDF text layer.
- **Tables**: only tables detectable by `PyMuPDF.find_tables` (`lines` strategy by default) are supported; tables without borders require adjusting `table_settings` (see [configuration.md](configuration.md)).
- **Visual OCR length**: PaddleOCR-VL generates at most 512 tokens per area.
- **Performance**: a large PDF rasterized at 450 DPI uses a lot of memory and disk (an A4 page gives an image of about 3,700 × 5,300 pixels).
- **Tests**: the repository does not contain automated tests.

## Development notes

- Python 3.12 minimum (f-strings with nested quotes in `content_classifier.py` and `table_processor.py`).
- All internal imports use the `src.` prefix: run the project from the root (`python src/texparser.py ...`) or install it in your environment.
- The versions in `requirements.txt` (except `transformers`, `safetensors` and `sentencepiece`, which are already pinned) are minimum bounds not verified in a complete environment.

## Fix history

| Problem | Fix |
|---|---|
| Infinite recursion `extract()` ↔ `to_markdown()` with `save_md=True` | `ContentExtractor` keeps the extracted `Document`; `to_markdown()` / `to_html()` reuse it |
| Export limited to the first page | `Document.to_markdown()` / `to_html()`: `page_number=0` exports all pages, `n >= 1` exports page `n` |
| `--save_md` / `--save_html` always true (`type=bool`) | `argparse.BooleanOptionalAction` (`--no-save_md`, `--no-save_html`) |
| Blocking OpenCV window | `show=False` in `TextProcessor` |
| Imports without the `src.` prefix | Imports unified in `content_classifier.py` and `layout_block_processor.py` |
| `--device` ignored, `cuda` hard-coded | `device` forwarded to `LayoutBlockProcessor`, `TextProcessor` and `ScannedImageProcessor`; automatic CPU fallback in `ContentExtractor` |
| Case-sensitive class comparison in `is_scanned_block` | Lowercase comparison |
| `is_empty()` with inverted meaning | Returns `True` for an empty text; caller fixed; `overlaps()` now called with the right bbox |
| Unused `tkinter` import in `ImageModel` | Removed |
| `TableModel` JSON and `TextFormulaModel.to_html()` not implemented | Implemented |
| `MainConfig.from_yaml()` failing | Double conversion removed; YAML files properly opened |
| Possible `IndexError` in `TableProcessor` (table without data rows) | Guard added, columns removed in reverse order |
| `set_pdf_path()` did not change the processed PDF | The `LayoutBlockProcessor` is updated too |
| `test.py`: outdated path | Path to `data/sample_pdfs/` |
| Incomplete `requirement.txt` | Complete `requirements.txt`, unused packages (`pandas`, `bs4`, `beautifulsoup4`) removed |
| No `.gitignore` | Added (`.conda/`, `.idea/`, `__pycache__/`, `models/`, `output/`…) |

## Improvement ideas

- Make DPI, thresholds, zoom and devices configurable (YAML files are already supported by `MainConfig.from_yaml`).
- Add a LaTeX export.
- Add unit tests (bbox geometry, scan detection, table-to-HTML conversion, page export).
- Detect columns to improve the reading order.
- Use PaddleOCR-VL in `table` mode for scanned tables.
- Provide a Docker image and a `pyproject.toml`.
