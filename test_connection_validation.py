import json
from pathlib import Path

from m1_vision.line_detector import (
    detect_lines,
    filter_line_candidates,
    merge_line_segments,
    validate_endpoint_connection,
)

IMAGE_PATH = "output/m1_test/page_5.png"
SYMBOLS_PATH = "output/m1_test/symbols.json"


def point_to_bbox_distance(point, bbox):
    px, py = point
    x1, y1, x2, y2 = bbox

    dx = max(x1 - px, 0, px - x2)
    dy = max(y1 - py, 0, py - y2)

    return (dx ** 2 + dy ** 2) ** 0.5


# Load existing symbols
with open(SYMBOLS_PATH, "r", encoding="utf-8") as file:
    all_symbols = json.load(file)

symbols = [
    symbol
    for symbol in all_symbols
    if symbol["page"] == 5
]

# Generate the same line-processing stages we already tested
raw_lines = detect_lines(IMAGE_PATH, page=5)

from PIL import Image

with Image.open(IMAGE_PATH) as image:
    width, height = image.size

filtered_lines = filter_line_candidates(
    raw_lines,
    width,
    height
)

merged_lines = merge_line_segments(filtered_lines)

print(f"Raw lines: {len(raw_lines)}")
print(f"Filtered lines: {len(filtered_lines)}")
print(f"Merged lines: {len(merged_lines)}")
print(f"Page 5 symbols: {len(symbols)}")

nearby_count = 0
validated_count = 0

for line in merged_lines:

    endpoint_a, endpoint_b = line["points"]

    for endpoint_name, endpoint, other_endpoint in [
        ("endpoint_a", endpoint_a, endpoint_b),
        ("endpoint_b", endpoint_b, endpoint_a),
    ]:

        best_symbol = None
        best_distance = float("inf")

        for symbol in symbols:

            distance = point_to_bbox_distance(
                endpoint,
                symbol["bbox"]
            )

            if distance <= 40 and distance < best_distance:
                best_symbol = symbol
                best_distance = distance

        if best_symbol is None:
            continue

        nearby_count += 1

        valid = validate_endpoint_connection(
            endpoint,
            other_endpoint,
            best_symbol["bbox"]
        )

        if valid:
            validated_count += 1

            print(
                f"VALID: {line['id']} "
                f"{endpoint_name} -> {best_symbol['id']} "
                f"distance={best_distance:.1f}"
            )

        else:
            print(
                f"REJECTED: {line['id']} "
                f"{endpoint_name} -> {best_symbol['id']} "
                f"distance={best_distance:.1f}"
            )

print()
print(f"Nearby endpoint candidates: {nearby_count}")
print(f"Validated connections: {validated_count}")