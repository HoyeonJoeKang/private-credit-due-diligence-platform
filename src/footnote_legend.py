import re

LEGEND_ENTRY_PATTERN = re.compile(r"\((\d+)\)\s+(?=[A-Z][a-z])")


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


def _find_sequential_chains(text: str, max_gap: int = 800) -> list[list[re.Match]]:
    matches = list(LEGEND_ENTRY_PATTERN.finditer(text))
    if not matches:
        return []

    chains = []
    current_chain = [matches[0]]
    for m in matches[1:]:
        prev_match = current_chain[-1]
        prev_number = int(prev_match.group(1))
        this_number = int(m.group(1))
        close_enough = (m.start() - prev_match.start()) <= max_gap
        if this_number == prev_number + 1 and close_enough:
            current_chain.append(m)
        else:
            chains.append(current_chain)
            current_chain = [m]
    chains.append(current_chain)
    return chains


def parse_footnote_legend(text: str, max_gap: int = 800, max_definition_length: int = 300) -> dict[int, str]:
    anchor_number = find_non_accrual_footnote_number(text)
    if anchor_number is None:
        return {}

    chains = _find_sequential_chains(text, max_gap)
    target_chain = None
    for chain in chains:
        numbers_in_chain = {int(m.group(1)) for m in chain}
        if anchor_number in numbers_in_chain:
            if target_chain is None or len(chain) > len(target_chain):
                target_chain = chain

    if target_chain is None:
        return {}

    legend = {}
    for i, m in enumerate(target_chain):
        number = int(m.group(1))
        entry_start = m.end()
        if i + 1 < len(target_chain):
            entry_end = target_chain[i + 1].start()
            definition = text[entry_start:entry_end].strip()
        else:
            window_text = text[entry_start:entry_start + max_definition_length]
            period_pos = window_text.find(".")
            definition = window_text[:period_pos + 1].strip() if period_pos != -1 else window_text.strip()
        legend[number] = definition
    return legend
