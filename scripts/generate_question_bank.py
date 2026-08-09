"""Generate a bilingual, source-linked review bank from imported guide pages.

Generated questions are deliberately marked ai_reviewed, never verified. Run this
script again safely: normalized Spanish question text prevents duplicates.
"""
from __future__ import annotations

import json
import os
import re
import sqlite3
import time
import unicodedata
from pathlib import Path
from urllib import request

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent.parent
DB = ROOT / "database" / "colombia_exam.db"
load_dotenv(ROOT / ".env")
load_dotenv(ROOT / "backend" / ".env")

RANGES = [
    (5, 17, "Cultura"), (18, 30, "Cultura"), (31, 43, "Geografía"),
    (44, 56, "Geografía"), (57, 69, "Geografía"), (70, 82, "Geografía"),
    (83, 95, "Geografía"), (96, 108, "Historia"), (109, 121, "Historia"),
    (122, 134, "Historia"), (135, 147, "Historia"), (148, 159, "Constitución"),
    (160, 170, "Castellano"), (171, 180, "Castellano"), (181, 190, "Castellano"),
]
TARGET_PER_RANGE = 15

SCHEMA = {
    "type": "object",
    "properties": {
        "questions": {
            "type": "array", "minItems": TARGET_PER_RANGE, "maxItems": TARGET_PER_RANGE,
            "items": {
                "type": "object",
                "properties": {
                    "question_es": {"type": "string"}, "question_ru": {"type": "string"},
                    "answer_a": {"type": "string"}, "answer_a_ru": {"type": "string"},
                    "answer_b": {"type": "string"}, "answer_b_ru": {"type": "string"},
                    "answer_c": {"type": "string"}, "answer_c_ru": {"type": "string"},
                    "answer_d": {"type": "string"}, "answer_d_ru": {"type": "string"},
                    "correct_answer": {"type": "string", "enum": ["A", "B", "C", "D"]},
                    "topic": {"type": "string"}, "explanation_es": {"type": "string"},
                    "explanation_ru": {"type": "string"}, "source_page": {"type": "integer"},
                    "source_quote": {"type": "string"},
                },
                "required": ["question_es","question_ru","answer_a","answer_a_ru","answer_b","answer_b_ru","answer_c","answer_c_ru","answer_d","answer_d_ru","correct_answer","topic","explanation_es","explanation_ru","source_page","source_quote"],
                "additionalProperties": False,
            },
        }
    },
    "required": ["questions"], "additionalProperties": False,
}

def normalize(value: str) -> str:
    value = unicodedata.normalize("NFKD", value.casefold())
    return re.sub(r"[^a-z0-9]+", " ", "".join(c for c in value if not unicodedata.combining(c))).strip()

def migrate(db: sqlite3.Connection) -> None:
    columns = {row[1] for row in db.execute("PRAGMA table_info(questions)")}
    additions = {
        "question_ru": "TEXT", "answer_a_ru": "TEXT", "answer_b_ru": "TEXT",
        "answer_c_ru": "TEXT", "answer_d_ru": "TEXT", "explanation_ru": "TEXT",
        "source_quote": "TEXT",
    }
    for name, kind in additions.items():
        if name not in columns:
            db.execute(f"ALTER TABLE questions ADD COLUMN {name} {kind}")
    db.commit()

def call_openai(key: str, model: str, prompt: str) -> dict:
    payload = {
        "model": model,
        "input": [
            {"role": "developer", "content": "Create rigorous study questions using only the supplied official-guide excerpts. Never use outside knowledge. Return the requested JSON."},
            {"role": "user", "content": prompt},
        ],
        "max_output_tokens": 12000,
        "text": {"format": {"type": "json_schema", "name": "question_batch", "strict": True, "schema": SCHEMA}},
    }
    body = json.dumps(payload, ensure_ascii=False).encode()
    for attempt in range(1, 4):
        try:
            req = request.Request("https://api.openai.com/v1/responses", data=body, headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"}, method="POST")
            with request.urlopen(req, timeout=90) as response:
                data = json.loads(response.read().decode())
            break
        except Exception:
            if attempt == 3:
                raise
            print(f"API connection retry {attempt}/2...", flush=True)
            time.sleep(attempt * 5)
    text = "".join(part.get("text", "") for item in data.get("output", []) if item.get("type") == "message" for part in item.get("content", []) if part.get("type") == "output_text")
    return json.loads(text)

def main() -> None:
    key = os.getenv("OPENAI_API_KEY")
    if not key:
        raise SystemExit("OPENAI_API_KEY is not configured")
    # Keep bulk generation independent from the conversational tutor model.
    model = os.getenv("QUESTION_GENERATION_MODEL", "gpt-5-nano")
    db = sqlite3.connect(DB)
    db.row_factory = sqlite3.Row
    migrate(db)
    existing = {normalize(row[0]) for row in db.execute("SELECT question_es FROM questions")}
    inserted_total = 0
    for start, end, topic in RANGES:
        already = db.execute("SELECT COUNT(*) FROM questions WHERE status='ai_reviewed' AND source_page BETWEEN ? AND ?", (start, end)).fetchone()[0]
        if already >= TARGET_PER_RANGE:
            print(f"pages {start}-{end}: already complete ({already})", flush=True)
            continue
        pages = db.execute("SELECT page_number,text FROM material_pages WHERE page_number BETWEEN ? AND ? ORDER BY page_number", (start, end)).fetchall()
        source = "\n\n".join(f"[PAGE {p['page_number']}]\n{p['text']}" for p in pages)
        prompt = f"""Create exactly {TARGET_PER_RANGE} unique multiple-choice study questions from the excerpts below.
Primary topic: {topic}. Allowed topic labels: Constitución, Historia, Geografía, Cultura, Castellano.
Requirements:
- Every correct answer must be stated explicitly on its cited source_page.
- source_quote must be a short exact supporting excerpt from that page.
- Write natural Spanish plus an accurate Russian translation for question, all four answers, and explanation.
- Exactly one option is correct; distractors must be plausible but unambiguously wrong according to the excerpt.
- Distribute correct letters across A/B/C/D. Avoid trick wording and avoid asking about page numbers or document layout.
- Do not claim these are official exam questions.
- source_page must be from {start} through {end}.

OFFICIAL GUIDE EXCERPTS:
{source[:90000]}"""
        print(f"pages {start}-{end}: generating with {model}...", flush=True)
        data = call_openai(key, model, prompt)
        batch = 0
        for q in data["questions"]:
            if not start <= int(q["source_page"]) <= end or normalize(q["question_es"]) in existing:
                continue
            values = [q[k] for k in ("question_es","question_ru","answer_a","answer_a_ru","answer_b","answer_b_ru","answer_c","answer_c_ru","answer_d","answer_d_ru","correct_answer","topic","explanation_es","explanation_ru","source_page","source_quote")]
            db.execute("""INSERT INTO questions(question_es,question_ru,answer_a,answer_a_ru,answer_b,answer_b_ru,answer_c,answer_c_ru,answer_d,answer_d_ru,correct_answer,topic,explanation_es,explanation_ru,source_page,source_quote,status,source_id) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?, 'ai_reviewed',1)""", values)
            existing.add(normalize(q["question_es"])); batch += 1
        db.commit(); inserted_total += batch
        print(f"pages {start}-{end}: inserted {batch}", flush=True)
        time.sleep(1)
    print(f"Done. Inserted {inserted_total}; database total {db.execute('SELECT COUNT(*) FROM questions').fetchone()[0]}")

if __name__ == "__main__":
    main()
