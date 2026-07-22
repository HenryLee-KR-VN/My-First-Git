"""SQLite 저장 레이어. collector.py와 app.py가 공유한다."""
import hashlib
import sqlite3
from contextlib import contextmanager
from datetime import datetime

from config import DB_PATH

SCHEMA = """
CREATE TABLE IF NOT EXISTS jobs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    hash TEXT UNIQUE NOT NULL,
    source TEXT NOT NULL,
    company_name TEXT NOT NULL,
    company_domain TEXT,
    job_title TEXT NOT NULL,
    employment_type TEXT,
    tech_stack TEXT,
    career_level TEXT,
    location TEXT,
    url TEXT NOT NULL,
    posted_date TEXT,
    deadline TEXT,
    matched_keyword TEXT,
    first_seen TEXT NOT NULL,
    last_seen TEXT NOT NULL,
    collected_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_jobs_source ON jobs(source);
CREATE INDEX IF NOT EXISTS idx_jobs_domain ON jobs(company_domain);
CREATE INDEX IF NOT EXISTS idx_jobs_posted_date ON jobs(posted_date);
CREATE INDEX IF NOT EXISTS idx_jobs_company ON jobs(company_name);
"""


@contextmanager
def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def init_db():
    with get_conn() as conn:
        conn.executescript(SCHEMA)


def make_hash(company_name: str, job_title: str, url: str) -> str:
    raw = f"{company_name.strip()}|{job_title.strip()}|{url.strip()}"
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def upsert_job(conn, job: dict) -> str:
    """job 딕셔너리를 저장한다. 이미 존재하면(hash 동일) last_seen만 갱신.

    반환값: "inserted" | "updated"
    """
    job_hash = make_hash(job["company_name"], job["job_title"], job["url"])
    now = datetime.now().isoformat(timespec="seconds")

    cur = conn.execute("SELECT id FROM jobs WHERE hash = ?", (job_hash,))
    existing = cur.fetchone()

    if existing:
        conn.execute(
            "UPDATE jobs SET last_seen = ?, deadline = ?, collected_at = ? WHERE hash = ?",
            (now, job.get("deadline"), now, job_hash),
        )
        return "updated"

    conn.execute(
        """
        INSERT INTO jobs (
            hash, source, company_name, company_domain, job_title,
            employment_type, tech_stack, career_level, location, url,
            posted_date, deadline, matched_keyword, first_seen, last_seen, collected_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            job_hash,
            job["source"],
            job["company_name"],
            job.get("company_domain"),
            job["job_title"],
            job.get("employment_type"),
            job.get("tech_stack", ""),
            job.get("career_level"),
            job.get("location"),
            job["url"],
            job.get("posted_date"),
            job.get("deadline"),
            job.get("matched_keyword"),
            now,
            now,
            now,
        ),
    )
    return "inserted"
