import json
from pathlib import Path

import torch
from PIL import Image
from paddleocr import PaddleOCR


TILE_SIZE = 1200
TILE_OVERLAP = 200


def _iou(box_a, box_b):
    """Calculate IoU between two bounding boxes."""

    ax1, ay1, ax2, ay2 = box_a
    bx1, by1, bx2, by2 = box_b

    inter_x1 = max(ax1, bx1)
    inter_y1 = max(ay1, by1)
    inter_x2 = min(ax2, bx2)
    inter_y2 = min(ay2, by2)

    if inter_x2 <= inter_x1 or inter_y2 <= inter_y1:
        return 0.0

    intersection = (inter_x2 - inter_x1) * (inter_y2 - inter_y1)

    area_a = (ax2 - ax1) * (ay2 - ay1)
    area_b = (bx2 - bx1) * (by2 - by1)

    union = area_a + area_b - intersection

    if union == 0:
        return 0.0

    return intersection / union


def _is_duplicate(candidate, existing):
    """Check whether an OCR detection is a duplicate."""

    if candidate["text"].upper() != existing["text"].upper():
        return False

    return _iou(candidate["bbox"], existing["bbox"]) > 0.5


def _ocr_tile(ocr, tile_path, page, offset_x, offset_y):
    """Run OCR on one tile and convert coordinates to page coordinates."""

    results = ocr.predict(str(tile_path))

    detections = []

    for result in results:
        texts = result["rec_texts"]
        scores = result["rec_scores"]
        boxes = result["rec_polys"]

        for text, score, box in zip(texts, scores, boxes):
            text = text.strip()

            if not text:
                continue

            x_coordinates = [point[0] for point in box]
            y_coordinates = [point[1] for point in box]

            bbox = [
                round(min(x_coordinates) + offset_x),
                round(min(y_coordinates) + offset_y),
                round(max(x_coordinates) + offset_x),
                round(max(y_coordinates) + offset_y),
            ]

            detections.append({
                "text": text,
                "bbox": bbox,
                "confidence": round(float(score), 3),
                "page": page,
            })

    return detections


def run_ocr(image_path: str, page: int, output_path: str):
    """Run tiled OCR on one P&ID page and save the OCR results."""

    image_path = Path(image_path)
    output_path = Path(output_path)

    if not image_path.exists():
        raise FileNotFoundError(f"Image not found: {image_path}")

    ocr = PaddleOCR(lang="en")

    with Image.open(image_path) as image:
        width, height = image.size

        step = TILE_SIZE - TILE_OVERLAP

        tile_dir = output_path.parent / "_ocr_tiles"
        tile_dir.mkdir(parents=True, exist_ok=True)

        all_detections = []

        tile_number = 1

        for y in range(0, height, step):
            for x in range(0, width, step):

                x2 = min(x + TILE_SIZE, width)
                y2 = min(y + TILE_SIZE, height)

                tile = image.crop((x, y, x2, y2))

                tile_path = tile_dir / f"tile_{tile_number}.png"
                tile.save(tile_path)

                detections = _ocr_tile(
                    ocr,
                    tile_path,
                    page,
                    x,
                    y,
                )

                all_detections.extend(detections)

                tile_number += 1

                if x2 == width:
                    break

            if y2 == height:
                break

    # Remove duplicate detections created by overlapping tiles.
    unique_detections = []

    for detection in all_detections:
        duplicate = False

        for existing in unique_detections:
            if _is_duplicate(detection, existing):
                duplicate = True

                # Keep the higher-confidence detection.
                if detection["confidence"] > existing["confidence"]:
                    existing.update(detection)

                break

        if not duplicate:
            unique_detections.append(detection)

    ocr_data = []

    for number, detection in enumerate(unique_detections, start=1):
        ocr_data.append({
            "id": f"OCR-{number:03d}",
            "text": detection["text"],
            "bbox": detection["bbox"],
            "confidence": detection["confidence"],
            "page": detection["page"],
        })

    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, "w", encoding="utf-8") as file:
        json.dump(ocr_data, file, indent=2)

    return ocr_data


def run_ocr_on_pages(image_dir: str, output_path: str):
    """Run tiled OCR automatically on every page image in a directory."""

    image_dir = Path(image_dir)
    output_path = Path(output_path)

    if not image_dir.exists():
        raise FileNotFoundError(f"Image directory not found: {image_dir}")

    ocr = PaddleOCR(lang="en")

    all_ocr_data = []

    
    image_paths = sorted(
    image_dir.glob("page_*.png"),
    key=lambda path: int(path.stem.split("_")[1])
)

    if not image_paths:
        raise FileNotFoundError(
            f"No page images found in: {image_dir}"
        )

    ocr_number = 1

    for page_number, image_path in enumerate(image_paths, start=1):

        print(f"OCR processing page {page_number}: {image_path.name}")

        with Image.open(image_path) as image:
            width, height = image.size

            step = TILE_SIZE - TILE_OVERLAP

            tile_dir = output_path.parent / "_ocr_tiles"
            tile_dir.mkdir(parents=True, exist_ok=True)

            page_detections = []

            tile_number = 1

            for y in range(0, height, step):
                for x in range(0, width, step):

                    x2 = min(x + TILE_SIZE, width)
                    y2 = min(y + TILE_SIZE, height)

                    tile = image.crop((x, y, x2, y2))

                    tile_path = tile_dir / (
                        f"page_{page_number}_tile_{tile_number}.png"
                    )

                    tile.save(tile_path)

                    detections = _ocr_tile(
                        ocr,
                        tile_path,
                        page_number,
                        x,
                        y,
                    )

                    page_detections.extend(detections)

                    tile_number += 1

                    if x2 == width:
                        break

                if y2 == height:
                    break

        # Deduplicate overlapping tiles.
        unique_page_detections = []

        for detection in page_detections:
            duplicate = False

            for existing in unique_page_detections:
                if _is_duplicate(detection, existing):
                    duplicate = True

                    if detection["confidence"] > existing["confidence"]:
                        existing.update(detection)

                    break

            if not duplicate:
                unique_page_detections.append(detection)

        for detection in unique_page_detections:
            all_ocr_data.append({
                "id": f"OCR-{ocr_number:03d}",
                "text": detection["text"],
                "bbox": detection["bbox"],
                "confidence": detection["confidence"],
                "page": page_number,
            })

            ocr_number += 1

    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, "w", encoding="utf-8") as file:
        json.dump(all_ocr_data, file, indent=2)

    print(f"Total OCR entries: {len(all_ocr_data)}")
    print(f"Saved: {output_path}")

    return all_ocr_data