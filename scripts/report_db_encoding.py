from __future__ import annotations

import sqlite3
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
DB_PATH = ROOT / "database" / "colombia_exam.db"
TEXT_COLUMNS = {
    "questions": (
        "question_es",
        "question_ru",
        "answer_a",
        "answer_a_ru",
        "answer_b",
        "answer_b_ru",
        "answer_c",
        "answer_c_ru",
        "answer_d",
        "answer_d_ru",
        "topic",
        "explanation_es",
        "explanation_ru",
        "source_quote",
    ),
    "material_pages": ("text",),
    "material_chapters": ("title",),
    "sources": ("title", "url", "document_type"),
}
SUSPICIOUS_MARKERS = (
    "Вї",
    "ВЎ",
    "вЂ",
    "ГЎ",
    "Г©",
    "Г­",
    "Гі",
    "Гє",
    "Г±",
    "ГЃ",
    "ГЌ",
    "Г“",
    "Гљ",
    "Г‘",
    "Ã",
    "Ð",
    "Ñ",
    "Ñ",
    "Ñ",
    "Ñ",
    "Ñ",
    "Р°",
    "Рµ",
    "Рё",
    "Рѕ",
    "Рґ",
    "Рџ",
    "Рљ",
    "Рќ",
    "Рњ",
    "Р",
    "СЃ",
    "С‚",
    "СЊ",
    "С‹",
    "СЏ",
    "С‡",
    "С€",
)


def table_exists(db: sqlite3.Connection, table: str) -> bool:
    row = db.execute(
        "SELECT 1 FROM sqlite_master WHERE type='table' AND name=?",
        (table,),
    ).fetchone()
    return row is not None


def existing_columns(db: sqlite3.Connection, table: str) -> set[str]:
    return {row[1] for row in db.execute(f"PRAGMA table_info({table})")}


def main() -> None:
    if not DB_PATH.exists():
        raise SystemExit(f"Database not found: {DB_PATH}")

    def write(line: str) -> None:
        sys.stdout.buffer.write((line + "\n").encode("utf-8", errors="replace"))

    write(f"Dry-run only. No database writes: {DB_PATH}")
    write(f"Before applying any fix, create backup: {DB_PATH.with_suffix('.backup-YYYYMMDD-HHMMSS.db')}")

    total_suspicious = 0
    with sqlite3.connect(DB_PATH) as db:
        db.row_factory = sqlite3.Row
        for table, wanted_columns in TEXT_COLUMNS.items():
            if not table_exists(db, table):
                continue
            columns = [column for column in wanted_columns if column in existing_columns(db, table)]
            if not columns:
                continue

            select_columns = ", ".join(["id", *columns])
            rows = db.execute(f"SELECT {select_columns} FROM {table}").fetchall()
            table_count = 0
            samples: list[str] = []
            for row in rows:
                bad_columns = [
                    column
                    for column in columns
                    if row[column] and any(marker in str(row[column]) for marker in SUSPICIOUS_MARKERS)
                ]
                if not bad_columns:
                    continue
                table_count += 1
                if len(samples) < 5:
                    first = bad_columns[0]
                    value = str(row[first]).replace("\n", " ")[:120]
                    samples.append(f"  id={row['id']} column={first}: {value}")
            total_suspicious += table_count
            write(f"{table}: {table_count} suspicious rows")
            for sample in samples:
                write(sample)

    write(f"Total suspicious rows: {total_suspicious}")
    write("No changes were applied.")


if __name__ == "__main__":
    main()
