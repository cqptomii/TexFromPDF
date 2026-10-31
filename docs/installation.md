# Installation

## Requirements

| Item | Detail |
|---|---|
| Python | **3.12 or later** (the code uses f-strings with nested quotes, e.g. `f"{d.get("k")}"`, which are valid from Python 3.12) |
| GPU (optional) | NVIDIA + CUDA recommended for layout detection and the PaddleOCR-VL model. Without a GPU, use `--device cpu` (slower) |
| Disk space | Model weights take several hundred MB (see [models.md](models.md)); the PaddleOCR-VL model is downloaded from Hugging Face on first run |
| Internet access | Required on first run to download `PaddlePaddle/PaddleOCR-VL-1.5` and `breezedeus/pix2text-mfr-1.5` from Hugging Face |

## 1. Clone the repository

```bash
git clone git@github.com:cqptomii/TexFromPDF.git
cd TexFromPDF
```

## 2. Create a virtual environment

```bash
python -m venv .venv
# Linux / macOS
source .venv/bin/activate
# Windows (PowerShell)
.venv\Scripts\Activate.ps1
```

## 3. Install the dependencies

The `requirements.txt` file lists all the project dependencies:

| Library (pip) | Used for |
|---|---|
| `pymupdf` (import `fitz`) | PDF reading, rasterization, text extraction, table detection |
| `ultralytics` | Loading and running the YOLO layout analysis model |
| `torch` | Model backend, CUDA detection |
| `transformers`, `safetensors`, `sentencepiece` | Loading PaddleOCR-VL and the TrOCR processor |
| `optimum[onnxruntime]` | ONNX execution of the formula recognition model (`ORTModelForVision2Seq`) |
| `cnstd` | YOLO formula detector (`cnstd.yolo_detector`) |
| `opencv-python` | `TextProcessor` debug images |
| `pillow` | Image handling |
| `numpy` | Matrix computations, page rotation |
| `pyyaml` | Loading configuration from YAML |

Installation:

```bash
pip install -r requirements.txt
```

> To use the GPU, install the `torch` build matching your CUDA version by following the instructions on [pytorch.org](https://pytorch.org/get-started/locally/).

> The versions of `transformers`, `safetensors` and `sentencepiece` are pinned; the other packages use a minimum bound. These bounds have not been tested in a complete environment: adjust them if needed.

## 4. Place the local models

Two models are **not** downloaded automatically and must be placed in the `models/` folder at the project root:

```
models/
├── layout_detection/
│   ├── yolov12l-doclaynet.pt      # default model
│   └── yolo26m-doclaynet.pt       # lighter alternative
└── formula/
    └── pix2text-mfd-1.5.onnx      # formula detector (MFD)
```

- The YOLO models trained on **DocLayNet** are used for layout analysis.
- `pix2text-mfd-1.5.onnx` comes from the [Pix2Text](https://github.com/breezedeus/pix2text) project.

The other models (`breezedeus/pix2text-mfr-1.5`, `PaddlePaddle/PaddleOCR-VL-1.5`) are fetched automatically through Hugging Face.

> The `models/` folder is large: it is excluded from the repository by `.gitignore`.

## 5. Check the installation

```bash
python src/texparser.py --help
```

The command should display the options `--device`, `--output_dir`, `--pdf_dir`, `--verbose`, `--save_md` and `--save_html` (with their `--no-save_md` / `--no-save_html` variants).
