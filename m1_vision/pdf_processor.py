from pathlib import Path
import pymupdf


def pdf_to_images(pdf_path: str, output_dir: str):
    """Convert each PDF page into a PNG image."""
    pdf = pymupdf.open(pdf_path)

    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    for page_number, page in enumerate(pdf):
        pix = page.get_pixmap(matrix=pymupdf.Matrix(2, 2))

        image_path = output_path / f"page_{page_number + 1}.png"
        pix.save(image_path)

    pdf.close()