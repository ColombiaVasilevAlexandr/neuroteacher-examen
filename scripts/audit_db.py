from __future__ import annotations

import argparse
import hashlib
import sqlite3
from collections import Counter
from datetime import datetime
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
DB_PATH = ROOT / "database" / "colombia_exam.db"
DOC_PATH = ROOT / "docs" / "DATABASE_AUDIT.md"
MODULE_ORDER = ("География", "История", "Конституция", "Испанский", "Культура", "Натурализация", "Микротемы")
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


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def module_name(topic: str) -> str:
    if topic in MODULE_ORDER:
        return topic
    value = topic.casefold()
    if any(key in value for key in ("geograf", "hidrograf", "relieve", "cordillera", "amazon")) or "гидрограф" in value:
        return "География"
    if any(key in value for key in ("historia", "independencia", "colonial", "guerra", "violencia", "república", "republica")):
        return "История"
    if any(key in value for key in ("constituci", "tutela", "habeas", "rama ", "soberan", "plebiscito", "referendo", "legislativa", "control", "participación", "participacion", "ciudadano", "derecho")):
        return "Конституция"
    if any(key in value for key in ("castellano", "español", "espaã", "verbo", "adjet", "sustant", "pret", "futuro", "género", "genero", "palabra", "sílaba", "silaba", "vocabulario", "prepos")):
        return "Испанский"
    if any(key in value for key in ("cultura", "paz", "valores", "patrimonio", "afrocolomb", "indígen", "indigen", "turismo")):
        return "Культура"
    if any(key in value for key in ("naturaliz", "nacionalidad", "sitac", "visa", "residente", "requisito")):
        return "Натурализация"
    return "Микротемы"


def table_names(db: sqlite3.Connection) -> list[str]:
    return [row["name"] for row in db.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")]


def table_count(db: sqlite3.Connection, table: str) -> int:
    return int(db.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0])


def suspicious_rows(db: sqlite3.Connection) -> dict[str, list[str]]:
    targets = {
        "questions": ("question_es", "question_ru", "answer_a", "answer_a_ru", "answer_b", "answer_b_ru", "answer_c", "answer_c_ru", "answer_d", "answer_d_ru", "topic", "explanation_es", "explanation_ru", "source_quote"),
        "material_pages": ("text",),
        "material_chapters": ("title",),
        "sources": ("title", "url", "document_type"),
    }
    found: dict[str, list[str]] = {}
    tables = set(table_names(db))
    for table, columns in targets.items():
        if table not in tables:
            continue
        existing = {row["name"] for row in db.execute(f"PRAGMA table_info({table})")}
        selected = [column for column in columns if column in existing]
        samples: list[str] = []
        for row in db.execute(f"SELECT id,{','.join(selected)} FROM {table}"):
            for column in selected:
                value = str(row[column] or "")
                if any(marker in value for marker in SUSPICIOUS_MARKERS):
                    samples.append(f"id={row['id']} column={column}: {value.replace(chr(10), ' ')[:140]}")
                    break
            if len(samples) >= 10:
                break
        found[table] = samples
    return found


def build_report() -> str:
    if not DB_PATH.exists():
        raise SystemExit(f"Database not found: {DB_PATH}")

    backups = sorted(DB_PATH.parent.glob("colombia_exam.backup-*.db"))
    with sqlite3.connect(DB_PATH) as db:
        db.row_factory = sqlite3.Row
        tables = table_names(db)
        counts = {table: table_count(db, table) for table in tables}
        statuses = [dict(row) for row in db.execute("SELECT status, COUNT(*) AS count FROM questions GROUP BY status ORDER BY status")]
        raw_topics = [dict(row) for row in db.execute("SELECT topic, COUNT(*) AS count FROM questions GROUP BY topic ORDER BY count DESC, topic")]
        module_counts = Counter()
        for item in raw_topics:
            module_counts[module_name(item["topic"])] += item["count"]
        source_rows = [dict(row) for row in db.execute("SELECT id,title,url,document_type FROM sources ORDER BY id")]
        settings = [dict(row) for row in db.execute("SELECT key,value FROM study_settings ORDER BY key")] if "study_settings" in tables else []
        suspicious = suspicious_rows(db)

    lines = [
        "# Database Audit",
        "",
        f"Generated: {datetime.now().isoformat(timespec='seconds')}",
        "",
        "## Files",
        "",
        f"- database: `{DB_PATH.relative_to(ROOT)}`",
        f"- database size: `{DB_PATH.stat().st_size}` bytes",
        f"- database sha256: `{sha256(DB_PATH)}`",
    ]
    current_hash = sha256(DB_PATH)
    current_backup_count = 0
    for backup in backups:
        same = sha256(backup) == current_hash
        if same:
            current_backup_count += 1
        lines.append(f"- backup: `{backup.relative_to(ROOT)}` sha256 `{sha256(backup)}` same_as_current `{str(same).lower()}`")
    lines.append(f"- current backup count: `{current_backup_count}`")

    lines += ["", "## Tables", ""]
    for table, count in counts.items():
        lines.append(f"- `{table}`: {count}")

    lines += ["", "## Question Status", ""]
    for row in statuses:
        lines.append(f"- `{row['status']}`: {row['count']}")

    lines += ["", "## Student Modules", ""]
    for module in MODULE_ORDER:
        lines.append(f"- `{module}`: {module_counts[module]}")

    lines += ["", "## Raw Topics", "", f"Raw topic count: `{len(raw_topics)}`", ""]
    for row in raw_topics[:40]:
        lines.append(f"- `{row['topic']}`: {row['count']}")
    if len(raw_topics) > 40:
        lines.append(f"- ... {len(raw_topics) - 40} more raw topics")

    lines += ["", "## Sources", ""]
    for row in source_rows:
        lines.append(f"- `{row['id']}` `{row['title']}` `{row['document_type']}`")
        lines.append(f"  {row['url']}")

    lines += ["", "## Study Settings", ""]
    if settings:
        for row in settings:
            lines.append(f"- `{row['key']}`: `{row['value']}`")
    else:
        lines.append("- none")

    lines += ["", "## Encoding Dry Run", ""]
    total_suspicious = sum(len(samples) for samples in suspicious.values())
    lines.append(f"Suspicious sample count: `{total_suspicious}`")
    for table, samples in suspicious.items():
        lines.append(f"- `{table}`: {len(samples)} samples")
        for sample in samples[:5]:
            lines.append(f"  - {sample}")

    lines += [
        "",
        "## Decision",
        "",
        "- No database write-fix is required when suspicious sample count is `0`.",
        "- At least one listed backup must match the current database before handoff.",
        "- Raw topics are intentionally preserved; student UI consumes the 7 aggregated modules.",
        "",
    ]
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--write", action="store_true", help="Write docs/DATABASE_AUDIT.md")
    args = parser.parse_args()
    report = build_report()
    if args.write:
        DOC_PATH.parent.mkdir(exist_ok=True)
        DOC_PATH.write_text(report, encoding="utf-8")
        print(f"Wrote {DOC_PATH}")
    else:
        print(report)


if __name__ == "__main__":
    main()
