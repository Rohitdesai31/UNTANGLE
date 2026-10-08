import json
from difflib import SequenceMatcher
from pathlib import Path
import re

from m1_vision.tag_normalizer import normalize_tag


def _center(bbox):
    x1, y1, x2, y2 = bbox
    return (
        (x1 + x2) / 2,
        (y1 + y2) / 2,
    )


def _distance(point_a, point_b):
    ax, ay = point_a
    bx, by = point_b
    return ((ax - bx) ** 2 + (ay - by) ** 2) ** 0.5


def _build_io_tags(io_list):
    """Create a set of valid reference tags from the IO list."""
    return {
        item["tag"].strip().upper()
        for item in io_list
        if item.get("tag")
    }


def _split_tag(tag):
    """
    Split an engineering tag into prefix and numeric portion.

    Examples:
        FT-101  -> ("FT", "101")
        P-101   -> ("P", "101")
        FIC-101 -> ("FIC", "101")
    """
    match = re.fullmatch(
        r"([A-Z]+)-([0-9]+)([A-Z0-9]*)",
        tag.upper()
    )

    if not match:
        return None

    prefix = match.group(1)
    number = match.group(2)
    suffix = match.group(3)

    return prefix, number, suffix

def _reconstruct_tag_from_ocr(
    ocr_data,
    io_tags,
    max_vertical_gap=80,
    max_horizontal_gap=80,
):
    """
    Reconstruct split engineering tags from nearby OCR tokens.

    Each numeric OCR token can be used only once.
    Each reconstructed IO tag is returned only once.
    """

    candidates = []
    used_number_ids = set()
    used_tags = set()

    for prefix_ocr in ocr_data:
        prefix_text = prefix_ocr.get("text", "").strip().upper()

        if not re.fullmatch(r"[A-Z]+", prefix_text):
            continue

        prefix_page = prefix_ocr["page"]
        prefix_x1, prefix_y1, prefix_x2, prefix_y2 = prefix_ocr["bbox"]

        best_candidate = None
        best_distance = float("inf")

        for number_ocr in ocr_data:

            if number_ocr["id"] in used_number_ids:
                continue

            if number_ocr["page"] != prefix_page:
                continue

            number_text = number_ocr.get("text", "").strip().upper()

            if not re.fullmatch(r"\d+", number_text):
                continue

            number_x1, number_y1, number_x2, number_y2 = number_ocr["bbox"]

            prefix_center_x = (prefix_x1 + prefix_x2) / 2
            number_center_x = (number_x1 + number_x2) / 2

            horizontal_gap = abs(
                prefix_center_x - number_center_x
            )

            if horizontal_gap > max_horizontal_gap:
                continue

            prefix_center_y = (prefix_y1 + prefix_y2) / 2
            number_center_y = (number_y1 + number_y2) / 2

            vertical_gap = abs(
                prefix_center_y - number_center_y
            )

            if vertical_gap > max_vertical_gap:
                continue

            candidate_tag = f"{prefix_text}-{number_text}"

            if candidate_tag not in io_tags:
                continue

            if candidate_tag in used_tags:
                continue

            distance = horizontal_gap + vertical_gap

            if distance < best_distance:
                best_distance = distance

                best_candidate = {
                    "tag": candidate_tag,
                    "prefix_id": prefix_ocr["id"],
                    "number_id": number_ocr["id"],
                }

        if best_candidate is not None:
            candidates.append(best_candidate)

            used_number_ids.add(
                best_candidate["number_id"]
            )

            used_tags.add(
                best_candidate["tag"]
            )

    return candidates


def _ocr_correction(value):
    """
    Apply only common OCR substitutions.

    These are intentionally conservative.
    """
    return (
        value.upper()
        .replace("O", "0")
        .replace("I", "1")
        .replace("L", "1")
    )


def _plausible_tag_match(ocr_tag, io_tag):
    """
    Determine whether an OCR tag is plausibly the same
    engineering tag as an IO-list tag.
    """

    ocr_parts = _split_tag(ocr_tag)
    io_parts = _split_tag(io_tag)

    if ocr_parts is None or io_parts is None:
        return False, 0.0

    ocr_prefix, ocr_number, ocr_suffix = ocr_parts
    io_prefix, io_number, io_suffix = io_parts

    # Prefix must match exactly.
    if ocr_prefix != io_prefix:
        return False, 0.0

    # Suffix must match exactly when present.
    if ocr_suffix != io_suffix:
        return False, 0.0

    # Exact numeric match.
    if ocr_number == io_number:
        return True, 1.0

    # Only allow plausible OCR substitutions in the numeric portion.
    corrected_number = _ocr_correction(ocr_number)

    if corrected_number == io_number:
        return True, 0.95

    return False, 0.0


def _find_io_match(tag, io_tags):
    """
    Match an OCR tag against the IO list.

    Exact normalized matches are preferred.
    Fuzzy matching is only allowed when the engineering
    tag structure remains compatible.
    """

    if not tag:
        return None, 0.0

    tag = tag.upper()

    # 1. Exact match.
    if tag in io_tags:
        return tag, 1.0

    # 2. Structure-aware OCR correction.
    best_match = None
    best_score = 0.0

    for io_tag in io_tags:
        is_match, score = _plausible_tag_match(
            tag,
            io_tag
        )

        if is_match and score > best_score:
            best_match = io_tag
            best_score = score

    return best_match, best_score

def associate_tags(
    symbols,
    ocr_data,
    io_list=None,
    max_distance=250,
):
    """
    Associate IO-list tags with detected symbols.

    Supports:
    1. Complete OCR tags.
    2. Reconstructed split OCR tags.

    The IO list remains the authoritative source for valid tags.
    """

    associations = []
    used_ocr = set()

    io_tags = _build_io_tags(io_list or [])

    # Reconstruct tags from split OCR tokens.
    reconstructed_tags = _reconstruct_tag_from_ocr(
        ocr_data,
        io_tags
    )

    # Create lookup for reconstructed tags.
    reconstructed_lookup = {
        item["tag"]: item
        for item in reconstructed_tags
    }

    for symbol in symbols:

        # Detector-provided tags are not trusted.
        symbol["tag"] = None

        best_match = None
        best_score = -1
        best_tag = None
        best_source_ids = []

        symbol_center = _center(symbol["bbox"])

        # --------------------------------------------------
        # 1. Check complete OCR tags
        # --------------------------------------------------

        for ocr in ocr_data:

            if ocr["id"] in used_ocr:
                continue

            if ocr["page"] != symbol["page"]:
                continue

            normalized_tag = normalize_tag(
                ocr.get("text", "")
            )

            if normalized_tag is None:
                continue

            io_match, tag_score = _find_io_match(
                normalized_tag,
                io_tags
            )

            if io_match is None:
                continue

            distance = _distance(
                symbol_center,
                _center(ocr["bbox"])
            )

            if distance > max_distance:
                continue

            spatial_score = (
                1 - distance / max_distance
            )

            match_score = (
                0.7 * tag_score
                + 0.3 * spatial_score
            )

            if match_score > best_score:
                best_match = ocr
                best_score = match_score
                best_tag = io_match
                best_source_ids = [ocr["id"]]

        # --------------------------------------------------
        # 2. Check reconstructed split tags
        # --------------------------------------------------

        for tag, reconstructed in reconstructed_lookup.items():

            if tag in {
                symbol.get("tag")
            }:
                continue

            prefix_ocr = next(
                (
                    item
                    for item in ocr_data
                    if item["id"]
                    == reconstructed["prefix_id"]
                ),
                None
            )

            number_ocr = next(
                (
                    item
                    for item in ocr_data
                    if item["id"]
                    == reconstructed["number_id"]
                ),
                None
            )

            if prefix_ocr is None or number_ocr is None:
                continue

            if prefix_ocr["id"] in used_ocr:
                continue

            if number_ocr["id"] in used_ocr:
                continue

            if prefix_ocr["page"] != symbol["page"]:
                continue

            prefix_center = _center(
                prefix_ocr["bbox"]
            )

            number_center = _center(
                number_ocr["bbox"]
            )

            tag_center = (
                (
                    prefix_center[0]
                    + number_center[0]
                ) / 2,
                (
                    prefix_center[1]
                    + number_center[1]
                ) / 2,
            )

            distance = _distance(
                symbol_center,
                tag_center
            )

            if distance > max_distance:
                continue

            spatial_score = (
                1 - distance / max_distance
            )

            match_score = (
                0.8
                + 0.2 * spatial_score
            )

            if match_score > best_score:
                best_match = reconstructed
                best_score = match_score
                best_tag = tag
                best_source_ids = [
                    reconstructed["prefix_id"],
                    reconstructed["number_id"],
                ]

        # --------------------------------------------------
        # 3. Save best association
        # --------------------------------------------------

        if best_match is not None:

            symbol["tag"] = best_tag

            for source_id in best_source_ids:

                associations.append({
                    "source_id": source_id,
                    "target_id": symbol["id"],
                    "relation": "tag_of",
                    "confidence": round(
                        max(
                            0.0,
                            min(
                                best_score,
                                1.0
                            )
                        ),
                        3
                    )
                })

                used_ocr.add(source_id)

    return symbols, associations


def save_results(symbols, associations, output_dir):
    output_dir = Path(output_dir)
    output_dir.mkdir(
        parents=True,
        exist_ok=True
    )

    with open(
        output_dir / "symbols.json",
        "w",
        encoding="utf-8"
    ) as file:
        json.dump(
            symbols,
            file,
            indent=2
        )

    with open(
        output_dir / "associations.json",
        "w",
        encoding="utf-8"
    ) as file:
        json.dump(
            associations,
            file,
            indent=2
        )