# Module reference

Description of the main modules and classes in `src/`.

## `src/texparser.py`

### `texparser()`

CLI entry point. Parses the arguments, lists the PDFs with `Path.rglob("*.pdf")`, then creates one `ContentExtractor` per file and calls `extract()`.

## `src/content_extractor.py`

### `ContentExtractor(pdf_path, output_dir, device="cpu", model_name="yolov12l-doclaynet.pt", verbose=False, **kwargs)`

Main orchestrator.

| Method | Description |
|---|---|
| `extract()` | Classifies the PDF, extracts the blocks, writes `extracted_content.json`, triggers the MD/HTML exports according to the configuration and returns the `Document` |
| `to_markdown(page_number=0)` | Writes `<name>.md` (all pages) or `<name>_<n>.md` (page `n`, 1-based) and returns the content. Reuses the already extracted `Document` |
| `to_html(page_number=0)` | Writes `<name>.html` or `<name>_<n>.html` and returns the content |
| `set_pdf_path(pdf_path)` | Changes the target PDF (raises `FileNotFoundError` if missing) and invalidates the extracted document |

If `device` is `cuda` but CUDA is unavailable, `ContentExtractor` automatically falls back to `cpu`.

The effective output folder is `<output_dir>/<pdf_name>_<timestamp>`.

## `src/content_classifier.py`

### `ContentClassifier(config: MainConfig)`

Loads the YOLO model from `models/layout_detection/<model_name>`.

| Method | Description |
|---|---|
| `classify(pdf_path)` | Full pipeline: rotation → rasterization → detection; writes `classifications.json`; returns the list of pages |
| `_correct_page_rotation(page)` | Determines and applies the rotation (text, then projection) |
| `_detect_page_orientation(page)` | Orientation based on the direction of the text lines |
| `_detect_page_orientation_by_projection(page)` | Orientation based on pixel projections |
| `_page_rasterization(doc, dpi)` | Renders each page as PNG and writes its metadata |
| `_classify_page(page, page_metadata)` | YOLO inference, coordinate conversion, reclassification to `scanned-image`, cleanup, sorting |
| `_show_predictions(prediction_dict, page)` | Draws the blocks colored by class and saves the debug image |

## `src/layout_block_processor.py`

### `LayoutBlockProcessor(pdf_path, output_dir=None, table_settings=None, device="cpu")`

Instantiates all the processors and dispatches each block.

| Method | Description |
|---|---|
| `process(document: list[dict]) -> Document` | Walks through pages and blocks, calls the right processor, builds and saves the `Document` |
| `set_pdf_path(pdf_path)` | Changes the processed PDF |

## `src/config/`

| Class | Description |
|---|---|
| `ClassifierConfig` | Layout model configuration (`from_dict`, `from_yaml`) |
| `MainConfig` | Global configuration (`from_dict`, `from_yaml`) |

See [configuration.md](configuration.md).

## `src/processors/`

All inherit from `BaseProcessor` and implement `process(page, page_number, block)`.

| Class | Constructor | Returns |
|---|---|---|
| `TextProcessor` | `(output_dir, device="cpu")` | `TextModel` or `TextFormulaModel` |
| `TableProcessor` | `(output_dir, table_settings=None)` | `TableModel` |
| `MathProcessor` | `(output_dir=None, model_name="breezedeus/pix2text-mfr-1.5")` | `TextModel` |
| `ImageProcessor` | `()` | `ImageModel` |
| `ScannedImageProcessor` | `(output_dir=None, model_name="PaddlePaddle/PaddleOCR-VL-1.5", device="cuda", task="ocr")` | `TextModel` |

Arguments of `process`:

- `page`: `fitz.Page` of the PDF.
- `page_number`: page number (starting at 1).
- `block`: dictionary from `classifications.json` (`id`, `class_name`, `confidence`, `bbox_pdf`…).

## `src/ocr/`

| Class | Description |
|---|---|
| `FormulaDetection(model_name="pix2text-mfd-1.5.onnx", device="cuda")` | `detect(img)` returns the list of formulas `{class_name, confidence, bbox_pdf}` (coordinates in the provided image). Automatic CPU fallback |
| `FormulaDetector` | Subclass of `cnstd.yolo_detector.YoloDetector` |
| `FormulaRecognition(model_name="breezedeus/pix2text-mfr-1.5")` | `recognize(img)` returns a list of LaTeX strings |
| `VlmImageRecognition(model_name="PaddlePaddle/PaddleOCR-VL-1.5", device="cpu", task="ocr")` | `recognize(img)` returns the recognized text (tasks `ocr`, `table`, `formula`, `chart`, `spotting`, `seal`) |

## `src/datamodel/`

See [datamodel.md](datamodel.md).

## `src/utils/`

### `bounding_box.py`

| Function | Description |
|---|---|
| `image_bbox_to_pdf(bbox, scale)` | Image pixels → PDF points (with margin) |
| `transform_bbox_for_rotation(bbox, rotation, w, h)` | Puts a bbox back into the original page coordinate system |
| `check_overlap(x, y, tolerance)` | Whether two values are close within `tolerance` |
| `is_superimposed(b1, b2, tolerance)` | Whether the four corners of two bboxes are close |
| `overlaps(b1, b2)` | Whether the two bboxes overlap |
| `contained(b1, b2, tolerance)` | Whether `b1` is contained in `b2` |
| `identified_bbox_mask(image, blocks_list)` | Computes the areas of an image not covered by a list of bboxes |
| `correct_blocks_redundancy(blocks, class_list)` | Removes redundant blocks, returns `(kept_blocks, removed_indices)` |
| `sort_blocks_by_position(blocks, y_tolerance=10)` | Reading order sorting |

### `scanned.py`

| Function | Description |
|---|---|
| `image_coverage_ratio(page)` | Share of the page covered by images |
| `is_scanned_image(page)` | Scanned page detection score |
| `is_scanned_block(page, bbox, class_name)` | Whether a block only contains scanned content |

### `utils.py`

| Function | Description |
|---|---|
| `normalize_text(text)` | Replaces line breaks/tabs with spaces and collapses multiple spaces |
| `is_empty(text)` | Returns `True` if the text is empty or only contains whitespace |

### `numpy_encoder.py`

`NumpyJSONEncoder`: JSON encoder handling `np.integer`, `np.floating` and `np.ndarray`.

## `test.py`

Development utility script: extracts a few pages of a PDF into new files with PyMuPDF. The source path is hard-coded (`./data/sample_pdfs/HN01-clio1-présentation.pdf`) and must be adapted.
