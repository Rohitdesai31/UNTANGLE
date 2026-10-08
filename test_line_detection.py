from pathlib import Path
from PIL import Image

from m1_vision.line_detector import (
    detect_lines,
    filter_line_candidates,
    merge_line_segments,
    save_lines,
)


# --------------------------------------------------
# Input / output paths
# --------------------------------------------------

IMAGE_PATH = "output/m1_test/page_2.png"

OUTPUT_PATH = "output/m1_test/lines.json"

DEBUG_PATH = "output/m1_test/page_2_lines_debug.png"


# --------------------------------------------------
# Detect raw lines
# --------------------------------------------------

raw_lines = detect_lines(
    IMAGE_PATH,
    page=2
)


# --------------------------------------------------
# Get image dimensions
# --------------------------------------------------

with Image.open(IMAGE_PATH) as image:
    width, height = image.size


# --------------------------------------------------
# Filter line candidates
# --------------------------------------------------

filtered_lines = filter_line_candidates(
    raw_lines,
    width,
    height
)


# --------------------------------------------------
# Merge line segments
# --------------------------------------------------

merged_lines = merge_line_segments(
    filtered_lines
)


# --------------------------------------------------
# Save final lines.json
# --------------------------------------------------

save_lines(
    merged_lines,
    OUTPUT_PATH
)


# --------------------------------------------------
# Create debug image
# --------------------------------------------------

from m1_vision.line_detector import create_debug_image

create_debug_image(
    IMAGE_PATH,
    merged_lines,
    DEBUG_PATH
)


# --------------------------------------------------
# Print summary
# --------------------------------------------------

print()
print("Line detection test complete.")
print(f"Raw lines: {len(raw_lines)}")
print(f"Filtered lines: {len(filtered_lines)}")
print(f"Merged lines: {len(merged_lines)}")
print(f"JSON: {OUTPUT_PATH}")
print(f"Debug image: {DEBUG_PATH}")