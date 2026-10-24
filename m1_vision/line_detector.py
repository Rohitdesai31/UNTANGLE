import json
from pathlib import Path

import cv2
import numpy as np


def detect_lines(image_path: str, page: int = 1):
    """
    Detect line segments from a P&ID page image.

    Returns line candidates in page-image coordinates.
    """

    image = cv2.imread(image_path)

    if image is None:
        raise FileNotFoundError(
            f"Could not read image: {image_path}"
        )

    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    # Convert the drawing into a binary image.
    binary = cv2.adaptiveThreshold(
        gray,
        255,
        cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY_INV,
        31,
        10,
    )

    # Detect straight line segments.
    segments = cv2.HoughLinesP(
        binary,
        rho=1,
        theta=np.pi / 180,
        threshold=80,
        minLineLength=40,
        maxLineGap=15,
    )

    lines = []

    if segments is None:
        return lines

    for index, segment in enumerate(segments, start=1):
        x1, y1, x2, y2 = segment[0]

        length = float(
            np.hypot(x2 - x1, y2 - y1)
        )

        if length < 40:
            continue

        lines.append({
            "id": f"LINE-{index:03d}",
            "points": [
                [int(x1), int(y1)],
                [int(x2), int(y2)],
            ],
            "line_type": "unknown",
            "confidence": 0.5,
            "page": page,
        })

    return lines

def filter_line_candidates(lines, image_width, image_height):
    """
    Remove obvious non-process-line candidates.

    Filtering is based on geometry, not on specific P&ID coordinates:
    - remove very short segments
    - remove segments that are far from horizontal/vertical orientation
    - remove segments lying on the page border
    """

    filtered = []

    min_length = 60
    orientation_tolerance = 5
    border_margin_x = image_width * 0.02
    border_margin_y = image_height * 0.02

    for line in lines:
        (x1, y1), (x2, y2) = line["points"]

        dx = x2 - x1
        dy = y2 - y1

        length = float(np.hypot(dx, dy))

        # 1. Remove very short segments.
        if length < min_length:
            continue

        # 2. Calculate line angle.
        angle = abs(np.degrees(np.arctan2(dy, dx)))

        # Normalize angle to 0-90 degrees.
        if angle > 90:
            angle = 180 - angle

        # Keep approximately horizontal or vertical lines.
        horizontal = angle <= orientation_tolerance
        vertical = abs(angle - 90) <= orientation_tolerance

        if not (horizontal or vertical):
            continue

        # 3. Remove page-border lines.
        near_left = min(x1, x2) <= border_margin_x
        near_right = max(x1, x2) >= image_width - border_margin_x
        near_top = min(y1, y2) <= border_margin_y
        near_bottom = max(y1, y2) >= image_height - border_margin_y

        if near_left or near_right or near_top or near_bottom:
            continue

        filtered.append(line)

    return filtered

def merge_line_segments(lines, coordinate_tolerance=10, gap_tolerance=30):
    """
    Merge nearby collinear horizontal and vertical line segments.

    Segments are merged when:
    - they have the same orientation
    - they lie close to the same horizontal/vertical coordinate
    - the gap between them is small or they overlap
    """

    horizontal = []
    vertical = []

    for line in lines:
        (x1, y1), (x2, y2) = line["points"]

        if abs(y2 - y1) <= coordinate_tolerance:
            x_start = min(x1, x2)
            x_end = max(x1, x2)
            y = (y1 + y2) / 2

            horizontal.append({
                "x_start": x_start,
                "x_end": x_end,
                "y": y,
                "page": line["page"],
            })

        elif abs(x2 - x1) <= coordinate_tolerance:
            y_start = min(y1, y2)
            y_end = max(y1, y2)
            x = (x1 + x2) / 2

            vertical.append({
                "y_start": y_start,
                "y_end": y_end,
                "x": x,
                "page": line["page"],
            })

    def merge_horizontal_segments(segments):
        changed = True

        while changed:
            changed = False
            merged = []
            used = [False] * len(segments)

            for i, current in enumerate(segments):
                if used[i]:
                    continue

                x_start = current["x_start"]
                x_end = current["x_end"]
                y = current["y"]
                page = current["page"]

                for j in range(i + 1, len(segments)):
                    if used[j]:
                        continue

                    other = segments[j]

                    if abs(y - other["y"]) > coordinate_tolerance:
                        continue

                    gap = max(
                        other["x_start"] - x_end,
                        x_start - other["x_end"],
                        0,
                    )

                    if gap <= gap_tolerance:
                        x_start = min(x_start, other["x_start"])
                        x_end = max(x_end, other["x_end"])
                        y = (y + other["y"]) / 2
                        used[j] = True
                        changed = True

                used[i] = True

                merged.append({
                    "x_start": x_start,
                    "x_end": x_end,
                    "y": y,
                    "page": page,
                })

            segments = merged

        return segments

    def merge_vertical_segments(segments):
        changed = True

        while changed:
            changed = False
            merged = []
            used = [False] * len(segments)

            for i, current in enumerate(segments):
                if used[i]:
                    continue

                y_start = current["y_start"]
                y_end = current["y_end"]
                x = current["x"]
                page = current["page"]

                for j in range(i + 1, len(segments)):
                    if used[j]:
                        continue

                    other = segments[j]

                    if abs(x - other["x"]) > coordinate_tolerance:
                        continue

                    gap = max(
                        other["y_start"] - y_end,
                        y_start - other["y_end"],
                        0,
                    )

                    if gap <= gap_tolerance:
                        y_start = min(y_start, other["y_start"])
                        y_end = max(y_end, other["y_end"])
                        x = (x + other["x"]) / 2
                        used[j] = True
                        changed = True

                used[i] = True

                merged.append({
                    "y_start": y_start,
                    "y_end": y_end,
                    "x": x,
                    "page": page,
                })

            segments = merged

        return segments

    horizontal = merge_horizontal_segments(horizontal)
    vertical = merge_vertical_segments(vertical)

    merged_lines = []
    line_number = 1

    for segment in horizontal:
        merged_lines.append({
            "id": f"LINE-{line_number:03d}",
            "points": [
                [
                    int(segment["x_start"]),
                    int(segment["y"])
                ],
                [
                    int(segment["x_end"]),
                    int(segment["y"])
                ],
            ],
            "line_type": "unknown",
            "confidence": 0.5,
            "page": segment["page"],
        })
        line_number += 1

    for segment in vertical:
        merged_lines.append({
            "id": f"LINE-{line_number:03d}",
            "points": [
                [
                    int(segment["x"]),
                    int(segment["y_start"])
                ],
                [
                    int(segment["x"]),
                    int(segment["y_end"])
                ],
            ],
            "line_type": "unknown",
            "confidence": 0.5,
            "page": segment["page"],
        })
        line_number += 1

    return merged_lines

def associate_lines_with_symbols(lines, symbols, max_distance=40):
    """
    Associate line endpoints with nearby detected symbols.

    A candidate association is accepted only when:
    1. The symbol is within max_distance.
    2. The endpoint approaches the symbol from a geometrically
       valid direction.

    A line is rejected if both endpoints map to the same symbol.
    """

    def point_to_bbox_distance(point, bbox):
        px, py = point
        x1, y1, x2, y2 = bbox

        dx = max(x1 - px, 0, px - x2)
        dy = max(y1 - py, 0, py - y2)

        return float(np.hypot(dx, dy))

    associations = []

    for line in lines:
        endpoint_a, endpoint_b = line["points"]

        endpoint_matches = []

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

                if distance > max_distance:
                    continue

                if distance >= best_distance:
                    continue

                if not validate_endpoint_connection(
                    endpoint,
                    other_endpoint,
                    symbol["bbox"]
                ):
                    continue

                best_symbol = symbol
                best_distance = distance

            if best_symbol is not None:
                endpoint_matches.append({
                    "endpoint": endpoint_name,
                    "symbol_id": best_symbol["id"],
                    "distance": round(best_distance, 2),
                })

        # Reject if both endpoints map to the same symbol.
        if len(endpoint_matches) == 2:
            if (
                endpoint_matches[0]["symbol_id"]
                == endpoint_matches[1]["symbol_id"]
            ):
                continue

        if endpoint_matches:
            for match in endpoint_matches:
                associations.append({
                    "source_id": line["id"],
                    "target_id": match["symbol_id"],
                    "relation": (
                        "connects_from"
                        if match["endpoint"] == "endpoint_a"
                        else "connects_to"
                    ),
                    "confidence": round(
                        max(
                            0.0,
                            min(
                                1.0,
                                1.0 / (1.0 + match["distance"])
                            )
                        ),
                        3
                    )
                })

    return associations


def validate_endpoint_connection(
    endpoint,
    other_endpoint,
    bbox,
    tolerance=15
):
    """
    Validate whether a line endpoint represents a real connection
    to a symbol bounding box.

    Rules:
    1. The endpoint may be slightly inside the bbox, but must be
       close to one of its boundaries.
    2. The line must approach the symbol from that boundary's direction.
    3. An endpoint deep inside the bbox is rejected.
    4. An endpoint outside the bbox is accepted only when it is
       close to a valid boundary and approaches it correctly.
    """

    px, py = endpoint
    ox, oy = other_endpoint

    x1, y1, x2, y2 = bbox

    # --------------------------------------------------
    # Determine line orientation
    # --------------------------------------------------

    dx = ox - px
    dy = oy - py

    horizontal = abs(dx) >= abs(dy)

    # --------------------------------------------------
    # Horizontal line
    # --------------------------------------------------

    if horizontal:

        # The endpoint must be vertically aligned with
        # the symbol bbox.
        if not (
            y1 - tolerance
            <= py
            <= y2 + tolerance
        ):
            return False

        # ----------------------------------------------
        # Endpoint is inside bbox
        # ----------------------------------------------

        if x1 <= px <= x2:

            distance_left = px - x1
            distance_right = x2 - px

            # Close to LEFT boundary.
            #
            # The other endpoint must be to the LEFT,
            # meaning the line approaches the symbol
            # from the left side.
            if distance_left <= tolerance:

                if ox < px:
                    return True

            # Close to RIGHT boundary.
            #
            # The other endpoint must be to the RIGHT.
            if distance_right <= tolerance:

                if ox > px:
                    return True

            return False

        # ----------------------------------------------
        # Endpoint is outside bbox
        # ----------------------------------------------

        # Endpoint is LEFT of bbox.
        if px < x1:

            if x1 - px <= tolerance and ox > px:
                return True

        # Endpoint is RIGHT of bbox.
        if px > x2:

            if px - x2 <= tolerance and ox < px:
                return True

    # --------------------------------------------------
    # Vertical line
    # --------------------------------------------------

    else:

        # The endpoint must be horizontally aligned with
        # the symbol bbox.
        if not (
            x1 - tolerance
            <= px
            <= x2 + tolerance
        ):
            return False

        # ----------------------------------------------
        # Endpoint is inside bbox
        # ----------------------------------------------

        if y1 <= py <= y2:

            distance_top = py - y1
            distance_bottom = y2 - py

            # Close to TOP boundary.
            #
            # The other endpoint must be ABOVE.
            if distance_top <= tolerance:

                if oy < py:
                    return True

            # Close to BOTTOM boundary.
            #
            # The other endpoint must be BELOW.
            if distance_bottom <= tolerance:

                if oy > py:
                    return True

            return False

        # ----------------------------------------------
        # Endpoint is outside bbox
        # ----------------------------------------------

        # Endpoint is ABOVE bbox.
        if py < y1:

            if y1 - py <= tolerance and oy > py:
                return True

        # Endpoint is BELOW bbox.
        if py > y2:

            if py - y2 <= tolerance and oy < py:
                return True

    return False



def create_debug_image(image_path: str, lines, output_path: str):
    """Draw detected line candidates over the original image."""

    image = cv2.imread(image_path)

    if image is None:
        raise FileNotFoundError(
            f"Could not read image: {image_path}"
        )

    for line in lines:
        (x1, y1), (x2, y2) = line["points"]

        cv2.line(
            image,
            (x1, y1),
            (x2, y2),
            (0, 0, 255),
            2
        )

    output_path = Path(output_path)
    output_path.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    cv2.imwrite(
        str(output_path),
        image
    )

    print(f"Debug image saved: {output_path}")


def save_lines(lines, output_path: str):
    """Save detected lines to lines.json."""

    output_path = Path(output_path)
    output_path.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    with open(
        output_path,
        "w",
        encoding="utf-8"
    ) as file:
        json.dump(
            lines,
            file,
            indent=2
        )

    print(f"Lines detected: {len(lines)}")
    print(f"Lines saved: {output_path}")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Detect lines from a P&ID image."
    )

    parser.add_argument(
        "--input",
        required=True,
        help="Path to P&ID page image."
    )

    parser.add_argument(
        "--output",
        required=True,
        help="Path to output lines.json."
    )

    parser.add_argument(
        "--page",
        type=int,
        default=1,
        help="Page number."
    )

    args = parser.parse_args()

    # Step 1: Detect raw line candidates.
    lines = detect_lines(
        args.input,
        args.page
    )

    # Step 2: Remove obvious non-process-line candidates.
    image = cv2.imread(args.input)

    if image is None:
        raise FileNotFoundError(
            f"Could not read image: {args.input}"
        )

    height, width = image.shape[:2]

    lines = filter_line_candidates(
        lines,
        width,
        height
    )

    # Step 3: Merge fragmented collinear segments.
    lines = merge_line_segments(
        lines
    )

    # Step 4: Save cleaned lines.
    save_lines(
        lines,
        args.output
    )