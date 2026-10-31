import argparse
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from src.content_extractor import ContentExtractor


def texparser():

    args = argparse.ArgumentParser()

    args.add_argument(
        "--device",
        type=str,
        default="cuda",
        help="Device to use for DL models inference"
    )

    args.add_argument(
        "--output_dir",
        type=str,
        required=True,
        help="Directory to save the output"
    )

    args.add_argument(
        "--pdf_dir",
        type=str,
        required=True,
        help="Path to the directory containing the PDF files"
    )

    args.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose mode"
    )

    args.add_argument(
        "--save_md",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="Enable saving of the extracted content as markdown (use --no-save_md to disable)"
    )
    args.add_argument(
        "--save_html",
        action=argparse.BooleanOptionalAction,
        default=False,
        help="Enable saving of the extracted content as html (use --no-save_html to disable)"
    )

    args = args.parse_args()


    print(f"Output directory: {args.output_dir}")
    pdf_dir = Path(args.pdf_dir)
    pdf_files = list(pdf_dir.rglob("*.pdf"))
    document_amount = len(pdf_files)

    for i, pdf_file in enumerate(pdf_files, start=1):
        print(f"Processing document {i}/{document_amount} stored into : {pdf_file}")
        parser = ContentExtractor(
            pdf_path=pdf_file,
            output_dir=args.output_dir,
            device=args.device,
            verbose=args.verbose,
            save_md=args.save_md,
            save_html=args.save_html
        )

        parser.extract()


if __name__ == "__main__":
    texparser()