from pathlib import Path

from src.sec_client import fetch_text


def fetch_main_document(ticker: str, accession: str, primary_doc_url: str, raw_dir: str = "raw") -> str:
    accession_nodash = accession.replace("-", "")
    base_dir = Path(raw_dir) / ticker / accession_nodash
    base_dir.mkdir(parents=True, exist_ok=True)
    cache_path = base_dir / "main_doc.htm"
    fetch_text(primary_doc_url, cache_path=str(cache_path))
    return str(cache_path)
