"""Extract the official study guide into traceable local data.

This importer does not create questions. It preserves page numbers so editorial
review can cite a page before marking any question as verified.
"""
import json
import sqlite3
import sys
from pathlib import Path
from pypdf import PdfReader

ROOT = Path(__file__).resolve().parent.parent
PDF = ROOT / "data" / "official_sources" / "colombia_nuestra_casa_ru.pdf"
DB = ROOT / "database" / "colombia_exam.db"
OUT = ROOT / "data" / "imports" / "colombia_nuestra_casa_pages.json"

def is_heading(line: str) -> bool:
    compact = ' '.join(line.split())
    letters = [c for c in compact if c.isalpha()]
    return 4 <= len(compact) <= 110 and len(letters) > 3 and compact == compact.upper()

def main():
    if not PDF.exists():
        raise SystemExit(f"PDF not found: {PDF}")
    OUT.parent.mkdir(exist_ok=True)
    reader = PdfReader(PDF)
    pages, chapters = [], []
    for number, page in enumerate(reader.pages, start=1):
        text = page.extract_text() or ""
        pages.append({"page": number, "text": text})
        for line in text.splitlines():
            if is_heading(line):
                chapters.append({"title": ' '.join(line.split()), "page": number})
    OUT.write_text(json.dumps({"source": "Колумбия — наш дом (русский перевод)", "pages": pages, "chapters": chapters}, ensure_ascii=False), encoding="utf-8")
    with sqlite3.connect(DB) as db:
        db.execute("DELETE FROM material_pages WHERE source_id=1")
        db.execute("DELETE FROM material_chapters WHERE source_id=1")
        db.executemany("INSERT INTO material_pages(source_id,page_number,text) VALUES(1,?,?)", [(x["page"], x["text"]) for x in pages])
        db.executemany("INSERT INTO material_chapters(source_id,title,page_number) VALUES(1,?,?)", [(x["title"], x["page"]) for x in chapters])
    print(f"Imported {len(pages)} pages and indexed {len(chapters)} chapter headings.")

if __name__ == "__main__":
    main()
