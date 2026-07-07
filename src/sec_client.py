import os
import time
import json
from pathlib import Path

import requests

_SEC_RATE_LIMIT_PER_SEC = 5
_MIN_INTERVAL = 1.0 / _SEC_RATE_LIMIT_PER_SEC
_last_request_time = 0.0
_contact_email = None


def set_contact_email(email: str) -> None:
    global _contact_email
    _contact_email = email


def _get_headers() -> dict:
    email = _contact_email or os.environ.get("SEC_CONTACT_EMAIL")
    if not email:
        raise RuntimeError(
            "SEC requires a contact email in every request's User-Agent header.\n\n"
            "Set it at the top of your notebook with:\n"
            "  from src.sec_client import set_contact_email\n"
            "  set_contact_email(\"you@example.com\")\n\n"
            "(Alternatively, set the SEC_CONTACT_EMAIL environment variable.)"
        )
    return {"User-Agent": f"Research Project {email}"}


def _throttle():
    global _last_request_time
    elapsed = time.time() - _last_request_time
    if elapsed < _MIN_INTERVAL:
        time.sleep(_MIN_INTERVAL - elapsed)
    _last_request_time = time.time()


def fetch_json(url: str, cache_path: str | None = None) -> dict:
    if cache_path and Path(cache_path).exists():
        return json.loads(Path(cache_path).read_text())

    _throttle()
    resp = requests.get(url, headers=_get_headers(), timeout=30)
    resp.raise_for_status()
    data = resp.json()

    if cache_path:
        Path(cache_path).parent.mkdir(parents=True, exist_ok=True)
        Path(cache_path).write_text(json.dumps(data))

    return data


def fetch_text(url: str, cache_path: str | None = None) -> str:
    if cache_path and Path(cache_path).exists():
        return Path(cache_path).read_text(encoding="utf-8", errors="ignore")

    _throttle()
    resp = requests.get(url, headers=_get_headers(), timeout=30)
    resp.raise_for_status()
    text = resp.text

    if cache_path:
        Path(cache_path).parent.mkdir(parents=True, exist_ok=True)
        Path(cache_path).write_text(text, encoding="utf-8")

    return text


def submissions_url(cik_padded: str) -> str:
    return f"https://data.sec.gov/submissions/CIK{cik_padded}.json"


def companyfacts_url(cik_padded: str) -> str:
    return f"https://data.sec.gov/api/xbrl/companyfacts/CIK{cik_padded}.json"


def filing_summary_url(cik: str, accession_nodash: str) -> str:
    return f"https://www.sec.gov/Archives/edgar/data/{cik}/{accession_nodash}/FilingSummary.xml"


def archive_base_url(cik: str, accession_nodash: str) -> str:
    return f"https://www.sec.gov/Archives/edgar/data/{cik}/{accession_nodash}/"
