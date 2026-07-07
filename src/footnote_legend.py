import re


def build_plain_text(main_doc_path: str) -> str:
    with open(main_doc_path, encoding="utf-8", errors="ignore") as f:
        content = f.read()
    text = re.sub(r"<[^>]+>", " ", content)
    text = re.sub(r"&#160;|&nbsp;", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text


def find_non_accrual_footnote_candidates(text_only: str) -> list[int]:
    matches = re.finditer(r"\((\d+)\)\s*Loan was on non-accrual status", text_only)
    seen = []
    for m in matches:
        n = int(m.group(1))
        if n not in seen:
            seen.append(n)
    return seen


def find_non_accrual_footnote_number(text_only: str) -> int | None:
    candidates = find_non_accrual_footnote_candidates(text_only)
    return candidates[0] if candidates else None


def footnotes_contain_number(footnotes: str, number: int) -> bool:
    if footnotes is None or not isinstance(footnotes, str):
        return False
    return f"({number})" in footnotes
