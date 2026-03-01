import argparse
from content_extractor import ContentExtractor


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
        type=bool,
        default=True,
        help="Enable saving of the extracted content as markdown"
    )
    args.add_argument(
        "--save_html",
        type=bool,
        default=False,
        help="Enable saving of the extracted content as html"
    )

    args = args.parse_args()


    print(f"Output directory: {args.output_dir}")
    pdf_files = args.pdf_dir.rglob("*.pdf")
    document_amount = len(pdf_files)

    for i, pdf_file in enumerate(pdf_files):
        print(f"Processing document {i}/{document_amount} stored into : {pdf_file}")
        parser = ContentExtractor(
            pdf_path=args.pdf_path,
            output_dir=args.output_dir,
            device=args.device,
            verbose=args.verbose,
            save_md=args.save_md,
            save_html=args.save_html
        )

        parser.extract()


if __name__ == "__main__":
    texparser()