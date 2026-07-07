import re

ITEM2_PATTERN = re.compile(r"Item\s*2\.\s*Management")
ITEM3_PATTERN = re.compile(r"Item\s*3\.")

MIN_SECTION_GAP = 3000


def extract_mdna_section(text: str, min_gap: int = MIN_SECTION_GAP) -> str | None:
    item2_starts = [m.start() for m in ITEM2_PATTERN.finditer(text)]
    item3_starts = [m.start() for m in ITEM3_PATTERN.finditer(text)]

    if not item2_starts or not item3_starts:
        return None

    for start in item2_starts:
        following_item3 = [i for i in item3_starts if i > start]
        if not following_item3:
            continue
        end = min(following_item3)
        if end - start >= min_gap:
            return text[start:end].strip()

    return None
