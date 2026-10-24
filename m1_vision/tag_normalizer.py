import re


def clean_tag(text: str) -> str:
    """Clean OCR text and return a normalized tag candidate."""

    if not isinstance(text, str):
        return ""

    text = text.strip().upper()

    # Remove surrounding whitespace and common OCR punctuation.
    text = text.strip(".,:;()[]{}")

    # Normalize spaces around hyphens.
    text = re.sub(r"\s*-\s*", "-", text)

    # Remove spaces inside a possible tag.
    text = re.sub(r"\s+", "", text)

    return text


def is_tag_candidate(text: str) -> bool:
    """Check whether text has a plausible engineering tag structure."""

    text = clean_tag(text)

    if not text:
        return False

    # Generic structure:
    # letters + optional letters/numbers + hyphen + numbers
    #
    # Examples:
    # FT-101
    # FIC-101
    # PT-101A
    # P-101
    #
    # This intentionally does not restrict the prefix
    # to a fixed list of instrument types.
    pattern = r"^[A-Z]+[A-Z0-9]*-\d+[A-Z0-9]*$"

    return bool(re.fullmatch(pattern, text))


def normalize_tag(text: str) -> str | None:
    """Return a normalized tag candidate or None if it is not tag-like."""

    cleaned = clean_tag(text)

    if not is_tag_candidate(cleaned):
        return None

    return cleaned