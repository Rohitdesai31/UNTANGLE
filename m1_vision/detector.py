from pathlib import Path
from ultralytics import YOLO


CLASS_NAMES = {
    0: "pump",
    1: "tank",
    2: "vessel",
    3: "heat_exchanger",
    4: "compressor",
    5: "motor",
    6: "valve",
    7: "instrument",
}


def detect_symbols(
    image_path: str,
    model_path: str,
    page: int
):
    """Detect P&ID symbols in a page image using the trained YOLO model."""

    image_path = Path(image_path)
    model_path = Path(model_path)

    if not image_path.exists():
        raise FileNotFoundError(f"Image not found: {image_path}")

    if not model_path.exists():
        raise FileNotFoundError(f"Model not found: {model_path}")

    model = YOLO(str(model_path))

    results = model.predict(
        source=str(image_path),
        conf=0.25,
        verbose=False
    )

    symbols = []
    symbol_number = 1

    for result in results:
        boxes = result.boxes

        for box in boxes:
            class_id = int(box.cls[0])
            confidence = float(box.conf[0])

            x1, y1, x2, y2 = box.xyxy[0].tolist()

            symbols.append({
                "id": f"SYM-{symbol_number:03d}",
                "class_name": CLASS_NAMES[class_id],
                "tag": None,
                "bbox": [
                    round(x1),
                    round(y1),
                    round(x2),
                    round(y2)
                ],
                "confidence": round(confidence, 3),
                "page": page
            })

            symbol_number += 1

    return symbols