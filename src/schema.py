import sqlite3
from pathlib import Path

SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS filings (
    accession       TEXT PRIMARY KEY,
    ticker          TEXT NOT NULL,
    cik             TEXT NOT NULL,
    form_type       TEXT NOT NULL,
    filing_date     TEXT NOT NULL,
    period_end      TEXT NOT NULL,
    primary_doc_url TEXT,
    filing_summary_url TEXT,
    fetched_at      TEXT
);

CREATE TABLE IF NOT EXISTS portfolio_holdings (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    accession       TEXT NOT NULL REFERENCES filings(accession),
    ticker          TEXT NOT NULL,
    issuer          TEXT NOT NULL,
    industry        TEXT,
    investment_type TEXT,
    reference_rate  TEXT,
    spread_pct      REAL,
    interest_rate_pct REAL,
    principal       REAL,
    cost            REAL,
    fair_value      REAL,
    non_accrual     INTEGER DEFAULT 0,
    risk_rating     TEXT,
    UNIQUE(accession, issuer, investment_type, reference_rate, principal)
);

CREATE TABLE IF NOT EXISTS financial_metrics (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    accession       TEXT REFERENCES filings(accession),
    ticker          TEXT NOT NULL,
    metric_name     TEXT NOT NULL,
    xbrl_tag        TEXT,
    value           REAL,
    period_end      TEXT NOT NULL,
    UNIQUE(accession, metric_name)
);

CREATE TABLE IF NOT EXISTS mdna_sections (
    accession       TEXT PRIMARY KEY REFERENCES filings(accession),
    ticker          TEXT NOT NULL,
    raw_text        TEXT NOT NULL,
    word_count      INTEGER
);

CREATE TABLE IF NOT EXISTS sentiment_scores (
    accession       TEXT PRIMARY KEY REFERENCES filings(accession),
    ticker          TEXT NOT NULL,
    positive_pct    REAL,
    negative_pct    REAL,
    uncertainty_pct REAL,
    litigious_pct   REAL,
    constraining_pct REAL,
    total_words     INTEGER
);

CREATE TABLE IF NOT EXISTS data_quality_checks (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    accession       TEXT REFERENCES filings(accession),
    check_name      TEXT NOT NULL,
    expected_value  REAL,
    actual_value    REAL,
    diff_pct        REAL,
    passed          INTEGER,
    checked_at      TEXT
);
"""


def init_db(db_path: str = "parsed/dd_platform.db") -> sqlite3.Connection:
    Path(db_path).parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(db_path)
    conn.executescript(SCHEMA_SQL)
    conn.commit()
    return conn


if __name__ == "__main__":
    conn = init_db()
    cur = conn.execute("SELECT name FROM sqlite_master WHERE type='table'")
    print([r[0] for r in cur.fetchall()])
    conn.close()
