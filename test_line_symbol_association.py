import json

import cv2
from PIL import Image

from m1_vision.line_detector import (
    detect_lines,
    filter_line_candidates,
    merge_line_segments,
    associate_lines_with_symbols,
)


IMAGE_PATH = "output/m1_test/page_2.png"
SYMBOLS_PATH = "output/m1_test/symbols.json"


# --------------------------------------------------
# Load existing symbols for page 2
# --------------------------------------------------

with open(SYMBOLS_PATH, "r", encoding="utf-8") as file:
    all_symbols = json.load(file)


symbols = [
    symbol
    for symbol in all_symbols
    if symbol["page"] == 2
]


# --------------------------------------------------
# Detect and process lines
# --------------------------------------------------

raw_lines = detect_lines(
    IMAGE_PATH,
    page=2
)


with Image.open(IMAGE_PATH) as image:
    width, height = image.size


filtered_lines = filter_line_candidates(
    raw_lines,
    width,
    height
)


merged_lines = merge_line_segments(
    filtered_lines
)


# --------------------------------------------------
# Associate lines with symbols
# --------------------------------------------------

associations = associate_lines_with_symbols(
    merged_lines,
    symbols
)


# --------------------------------------------------
# Print results
# --------------------------------------------------

print(f"Raw lines: {len(raw_lines)}")
print(f"Filtered lines: {len(filtered_lines)}")
print(f"Merged lines: {len(merged_lines)}")
print(f"Page 2 symbols: {len(symbols)}")
print(f"Final associations: {len(associations)}")


print("\nAssociations:")

for association in associations:
    print(association)


# --------------------------------------------------
# Create association debug image
# --------------------------------------------------

debug_path = (
    "output/m1_test/page_2_associations_debug.png"
)


image = cv2.imread(IMAGE_PATH)


if image is None:
    raise FileNotFoundError(
        f"Could not read image: {IMAGE_PATH}"
    )


# --------------------------------------------------
# Draw all merged lines in RED
# --------------------------------------------------

for line in merged_lines:

    (x1, y1), (x2, y2) = line["points"]

    cv2.line(
        image,
        (x1, y1),
        (x2, y2),
        (0, 0, 255),
        2
    )


# --------------------------------------------------
# Draw symbol bounding boxes in BLUE
# --------------------------------------------------

symbol_lookup = {}


for symbol in symbols:

    symbol_lookup[symbol["id"]] = symbol

    x1, y1, x2, y2 = symbol["bbox"]

    cv2.rectangle(
        image,
        (x1, y1),
        (x2, y2),
        (255, 0, 0),
        2
    )

    cv2.putText(
        image,
        symbol["id"],
        (x1, max(y1 - 5, 15)),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.45,
        (255, 0, 0),
        1
    )


# --------------------------------------------------
# Draw ONLY accepted associations in GREEN
# --------------------------------------------------

for association in associations:

    line = next(
        line
        for line in merged_lines
        if line["id"] == association["line_id"]
    )

    for endpoint_match in association["endpoints"]:

        symbol = symbol_lookup[
            endpoint_match["symbol_id"]
        ]

        if endpoint_match["endpoint"] == "endpoint_a":
            endpoint = line["points"][0]
        else:
            endpoint = line["points"][1]

        sx1, sy1, sx2, sy2 = symbol["bbox"]

        symbol_center = (
            int((sx1 + sx2) / 2),
            int((sy1 + sy2) / 2)
        )


        # Green circle = accepted endpoint

        cv2.circle(
            image,
            tuple(endpoint),
            6,
            (0, 255, 0),
            -1
        )


        # Green line = accepted connection

        cv2.line(
            image,
            tuple(endpoint),
            symbol_center,
            (0, 255, 0),
            2
        )


        # Label accepted association

        cv2.putText(
            image,
            association["line_id"],
            (
                int(endpoint[0]) + 5,
                int(endpoint[1]) - 5
            ),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.4,
            (0, 128, 0),
            1
        )


# --------------------------------------------------
# Save debug image
# --------------------------------------------------

cv2.imwrite(
    debug_path,
    image
)


print(
    f"\nAssociation debug image saved: {debug_path}"
)