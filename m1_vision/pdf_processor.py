from pathlib import Path
import json
import pymupdf


def pdf_to_images(pdf_path: str, output_dir: str):
    """Convert each PDF page into a PNG image and create pages.json."""

    pdf = pymupdf.open(pdf_path)

    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    pages = []

    for page_number, page in enumerate(pdf):
        pix = page.get_pixmap(matrix=pymupdf.Matrix(2, 2))

        image_filename = f"page_{page_number + 1}.png"
        image_path = output_path / image_filename

        pix.save(image_path)

        pages.append({
            "id": f"PAGE-{page_number + 1:03d}",
            "page_number": page_number + 1,
            "width": pix.width,
            "height": pix.height
        })

    pdf.close()

    json_path = output_path / "pages.json"

    with open(json_path, "w", encoding="utf-8") as file:
        json.dump(pages, file, indent=2)

    return pages