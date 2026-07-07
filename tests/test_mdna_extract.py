import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.mdna_extract import extract_mdna_section


def build_sample_text():
    toc = "Item 2. Management's Discussion and Analysis of Financial Condition and Results of Operations 205 Item 3. Quantitative and Qualitative Disclosures "
    filler = "x" * 5000
    real_section = (
        "Item 2. Management's Discussion and Analysis of Financial Condition and Results of Operations "
        "The information contained in this section should be read in conjunction with our financial statements. "
        + filler +
        " end of mdna body here. "
    )
    closing = "Item 3. Quantitative and Qualitative Disclosures About Market Risk We are subject to financial market risks"
    return toc + real_section + closing


def run():
    text = build_sample_text()
    result = extract_mdna_section(text)

    assert result is not None
    assert result.startswith("Item 2. Management")
    assert "end of mdna body here" in result
    assert "Quantitative and Qualitative" not in result

    print("PASS")
    print("extracted length:", len(result))


if __name__ == "__main__":
    run()
