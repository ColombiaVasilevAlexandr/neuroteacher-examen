"""Import one guide edition into its own source namespace."""
import argparse
import json
import logging
import sqlite3
from datetime import datetime
from pathlib import Path
from pypdf import PdfReader

ROOT = Path(__file__).resolve().parents[1]

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--locale", choices=["es", "ru"], default="es")
    parser.add_argument("--db", type=Path, default=ROOT / "database/colombia_exam.db")
    args = parser.parse_args()
    spanish = args.locale == "es"
    source_id = 1 if spanish else 2
    filename = "colombia_nuestra_casa.pdf" if spanish else "colombia_nuestra_casa_ru.pdf"
    pdf = ROOT / "frontend/public" / filename
    logging.getLogger("pypdf").setLevel(logging.ERROR)
    reader = PdfReader(pdf)
    expected = 190 if spanish else 179
    if len(reader.pages) != expected:
        raise ValueError("Unexpected guide edition; existing data was not changed")
    pages = [(i, page.extract_text() or "") for i, page in enumerate(reader.pages, 1)]
    db = sqlite3.connect(args.db)
    backup = args.db.with_name(args.db.stem + ".backup-import-" + datetime.now().strftime("%Y%m%d-%H%M%S") + ".db")
    with sqlite3.connect(backup) as target:
        db.backup(target)
    with db:
        db.execute("INSERT OR REPLACE INTO sources(id,title,url,document_type) VALUES(?,?,?,?)",
                   (source_id, "Colombia, nuestra casa — 2024" if spanish else "Guía 2021 — traducción rusa (archivo)",
                    "/" + filename, "official_study_guide" if spanish else "archived_study_guide_translation"))
        db.execute("DELETE FROM material_pages WHERE source_id=?", (source_id,))
        db.executemany("INSERT INTO material_pages(source_id,page_number,text) VALUES(?,?,?)",
                       [(source_id, page, text) for page, text in pages])
    db.close()
    print(f"Imported {len(pages)} pages into source {source_id}; other editions and questions preserved.")

if __name__ == "__main__":
    main()
