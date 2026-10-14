
import hashlib
import json
import sqlite3
from contextlib import contextmanager
from pathlib import Path

DB_PATH = Path("data/dhaba.sqlite3")


def connect():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(
        DB_PATH,
        timeout=10,
    )
    connection.row_factory = sqlite3.Row
    return connection


@contextmanager
def database_connection():
    connection = connect()
    try:
        yield connection
        connection.commit()
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()


def initialize_db():
    with database_connection() as connection:
        connection.execute("""
            CREATE TABLE IF NOT EXISTS triage_results (
                ticket_id TEXT PRIMARY KEY,
                content_hash TEXT NOT NULL,
                status TEXT NOT NULL
                    CHECK (status IN ('processing', 'completed')),
                result_json TEXT
            )
        """)


def content_hash(ticket: dict) -> str:
    canonical = json.dumps(
        ticket,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    )
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def claim_ticket(ticket: dict):
    initialize_db()

    ticket_id = ticket["id"]
    digest = content_hash(ticket)

    with database_connection() as connection:
        connection.execute("BEGIN IMMEDIATE")

        existing = connection.execute(
            """
            SELECT content_hash, status, result_json
            FROM triage_results
            WHERE ticket_id = ?
            """,
            (ticket_id,),
        ).fetchone()

        if existing is None:
            connection.execute(
                """
                INSERT INTO triage_results
                    (ticket_id, content_hash, status)
                VALUES (?, ?, 'processing')
                """,
                (ticket_id, digest),
            )
            return "claimed", None

        if existing["content_hash"] != digest:
            return "conflict", None

        if existing["status"] == "completed":
            return "completed", json.loads(existing["result_json"])

        return "conflict", None


def complete_ticket(ticket_id: str, result: dict):
    result_json = json.dumps(result, ensure_ascii=False)

    with database_connection() as connection:
        cursor = connection.execute(
            """
            UPDATE triage_results
            SET status = 'completed', result_json = ?
            WHERE ticket_id = ? AND status = 'processing'
            """,
            (result_json, ticket_id),
        )

        if cursor.rowcount != 1:
            raise RuntimeError("Could not mark ticket as completed")


def release_ticket(ticket_id: str):
    """Release a failed claim so the same ticket can be retried."""
    with database_connection() as connection:
        connection.execute(
            """
            DELETE FROM triage_results
            WHERE ticket_id = ? AND status = 'processing'
            """,
            (ticket_id,),
        )
