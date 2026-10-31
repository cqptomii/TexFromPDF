# Data model

The extracted content is represented by a hierarchy of dataclasses defined in `src/datamodel/`.

```
Document
└── pages: list[Page]
    └── content_blocks: list[BaseModel]
        ├── TextModel
        ├── TextFormulaModel
        ├── TableModel
        └── ImageModel
```

## `Document`

| Field | Type | Description |
|---|---|---|
| `id` | `str` | MD5 hash of the source PDF file |
| `pages` | `list[Page]` | Processed pages |

Methods: `to_dict()`, `to_markdown(page_number=0, page_separator="\n---\n\n")`, `to_html(page_number=0)`.

`page_number=0` exports **all pages** (separated by `---` in Markdown, `<hr>` in HTML); `page_number=n` (1-based) exports page `n`; an out-of-range value raises `IndexError`.

## `Page`

| Field | Type | Description |
|---|---|---|
| `page_number` | `int` | Page number (starting at 1) |
| `content_blocks` | `list[BaseModel]` | Blocks in reading order |

In the JSON, the block list is exposed under the **`blocks_extracted`** key.

## `BaseModel` (abstract class)

Fields common to all blocks:

| Field | Type | Description |
|---|---|---|
| `page` | `int` | Page number |
| `class_name` | `str` | Detected class (`Text`, `Table`, `Formula`…) |
| `confidence` | `float` | YOLO detection confidence |
| `bbox` | `list[float]` | `[x0, y0, x1, y1]` in PDF points |

Abstract methods: `to_dict()`, `to_markdown()`, `to_html()`.

## Concrete blocks

### `TextModel`

Added field: `content: str`.

Produced for text, titles, lists, captions, footnotes, page headers/footers, isolated formulas (`Formula`) and scanned areas (`scanned-image`).

Markdown rendering:

| `class_name` | Rendering |
|---|---|
| `title`, `section-header`, `page-header` | `## content` (line breaks replaced by spaces) |
| `formula` | `$$content$$` |
| others | `content` |

HTML rendering: `<h2>` for `title` and `section-header`, plain text otherwise.

### `TextFormulaModel`

Added fields: `content: str`, `structured_blocks: dict`.

Only produced when `TextProcessor._use_bounding_box` is enabled (disabled by default). `structured_blocks` contains the sub-blocks (text and formulas) with their bbox.

### `TableModel`

Added field: `structured_content: list[list[str]]` (cell matrix).

Rendering: an HTML table. Adjacent cells with identical, non-empty content are merged into `colspan` / `rowspan`. Inner line breaks become `<br>`. With `table_format="json"`, `to_markdown()` returns the cell matrix serialized as JSON.

### `ImageModel`

Added field: `image_base64: str` (base64-encoded PNG).

Markdown rendering: `![class](data:image/png;base64,…)`. HTML rendering: `<img>` tag with a data URI.

## Full JSON format

Illustrative example (values are indicative):

```json
{
  "id": "37937cde681a45109a4b60507831b5b2",
  "pages": [
    {
      "page_number": 1,
      "blocks_extracted": [
        {
          "page": 1,
          "class_name": "Section-header",
          "confidence": 0.88,
          "bbox": [47.3, 105.2, 392.8, 120.1],
          "content": "0.  ASPECTS PARTICULIERS DE SURETE, SECURITE,  ENVIRONNEMENT"
        },
        {
          "page": 1,
          "class_name": "Table",
          "confidence": 0.77,
          "bbox": [50.3, 35.3, 561.5, 97.9],
          "structured_content": [["", "OPERATIONS\nINSTRUCTION"]]
        },
        {
          "page": 1,
          "class_name": "Picture",
          "confidence": 0.91,
          "bbox": [100.0, 200.0, 300.0, 400.0],
          "image_base64": "iVBORw0KGgo..."
        }
      ]
    }
  ]
}
```

The keys present vary depending on the block type (`content`, `structured_content` or `image_base64`). NumPy numeric values are serialized by `NumpyJSONEncoder`.
