import json
from pathlib import Path

import torch
from PIL import Image

from m1_vision.pdf_processor import pdf_to_images
from m1_vision.preprocess import validate_image
from m1_vision.detector import detect_symbols
from m1_vision.ocr import run_ocr_on_pages
from m1_vision.association import associate_tags


SUPPORTED_IMAGE_EXTENSIONS = {
    ".png",
    ".jpg",
    ".jpeg",
    ".webp",
}


def _prepare_input(input_path: Path, output_dir: Path):
    """
    Normalize PDF or image input into page images.

    PDF:
        Uses the existing pdf_processor module.

    Image:
        Validates the image and converts it into page_1.png
        so the rest of the pipeline can treat it like a PDF page.
    """

    suffix = input_path.suffix.lower()

    if suffix == ".pdf":
        print("Input type: PDF")
        print("Converting PDF into page images...")

        pages_data = pdf_to_images(
            str(input_path),
            str(output_dir)
        )

        return pages_data

    if suffix in SUPPORTED_IMAGE_EXTENSIONS:
        print("Input type: Image")
        print("Validating image...")

        validate_image(str(input_path))

        output_image = output_dir / "page_1.png"

        with Image.open(input_path) as image:
            image = image.convert("RGB")
            image.save(output_image)

        width, height = image.size

        pages_data = {
            "pages": [
                {
                    "page_id": 1,
                    "image": "page_1.png",
                    "width": width,
                    "height": height,
                }
            ]
        }

        with open(
            output_dir / "pages.json",
            "w",
            encoding="utf-8"
        ) as file:
            json.dump(pages_data, file, indent=2)

        return pages_data

    raise ValueError(
        "Unsupported input format. "
        "Use a PDF or PNG/JPG/JPEG/WEBP image."
    )


def run_m1_pipeline(
    input_path: str,
    output_dir: str,
    model_path: str
):
    """Run the M1 vision pipeline on a P&ID PDF or image."""

    input_path = Path(input_path)
    output_dir = Path(output_dir)
    model_path = Path(model_path)

    if not input_path.exists():
        raise FileNotFoundError(
            f"Input file not found: {input_path}"
        )

    if not model_path.exists():
        raise FileNotFoundError(
            f"Model not found: {model_path}"
        )

    output_dir.mkdir(parents=True, exist_ok=True)

    # 1. Normalize PDF/image input into page images.
    pages_data = _prepare_input(
        input_path,
        output_dir
    )

    # 2. Run YOLO on every generated page.
    all_symbols = []
    symbol_number = 1

    for page in pages_data["pages"]:
        page_number = page["page_id"]
        image_path = output_dir / page["image"]

        print(
            f"Detecting symbols on page {page_number}..."
        )

        symbols = detect_symbols(
            str(image_path),
            str(model_path),
            page_number
        )

        # Ensure symbol IDs remain globally unique
        # across all pages.
        for symbol in symbols:
            symbol["id"] = f"SYM-{symbol_number:03d}"
            symbol_number += 1

        all_symbols.extend(symbols)

    # 3. Run tiled OCR on every generated page.
    print("\nRunning OCR...")

    ocr_path = output_dir / "ocr.json"

    all_ocr = run_ocr_on_pages(
        str(output_dir),
        str(ocr_path)
    )

    # 4. Associate OCR text with detected symbols.
    print("\nAssociating OCR text with symbols...")

    all_symbols, associations = associate_tags(
        all_symbols,
        all_ocr
    )

    # 5. Save final M1 symbol output.
    symbols_path = output_dir / "symbols.json"

    with open(
        symbols_path,
        "w",
        encoding="utf-8"
    ) as file:
        json.dump(
            all_symbols,
            file,
            indent=2
        )

    # 6. Save association output.
    associations_path = output_dir / "associations.json"

    with open(
        associations_path,
        "w",
        encoding="utf-8"
    ) as file:
        json.dump(
            associations,
            file,
            indent=2
        )

    print("\nM1 vision pipeline complete.")
    print(
        f"Pages processed: "
        f"{len(pages_data['pages'])}"
    )
    print(
        f"Symbols detected: "
        f"{len(all_symbols)}"
    )
    print(
        f"OCR entries: "
        f"{len(all_ocr)}"
    )
    print(
        f"Associations: "
        f"{len(associations)}"
    )

    print(f"Symbols saved: {symbols_path}")
    print(f"OCR saved: {ocr_path}")
    print(
        f"Associations saved: "
        f"{associations_path}"
    )

    return {
        "pages": pages_data,
        "symbols": all_symbols,
        "ocr": all_ocr,
        "associations": associations,
    }


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description=(
            "Run the UNTANGLE M1 vision pipeline "
            "on a P&ID PDF or image."
        )
    )

    parser.add_argument(
        "--input",
        required=True,
        help="Path to the input P&ID PDF or image."
    )

    parser.add_argument(
        "--out",
        required=True,
        help="Directory where M1 outputs will be saved."
    )

    parser.add_argument(
        "--model",
        required=True,
        help="Path to the trained YOLO model."
    )

    args = parser.parse_args()

    run_m1_pipeline(
        input_path=args.input,
        output_dir=args.out,
        model_path=args.model
    )