"""Repair content provenance without changing question IDs or learning history.
Run with --db <path> --apply after reviewing --dry-run output.
"""
import argparse
import hashlib
import json
import logging
import re
import sqlite3
import unicodedata
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PATCH = ROOT / "data/content-corrections-20261024.json"

def norm(text):
    text = unicodedata.normalize("NFKD", str(text or "")).casefold()
    return " ".join("".join(c if c.isalnum() else " " for c in text if not unicodedata.combining(c)).split())

def digest_rows(db, table):
    return hashlib.sha256(json.dumps([tuple(r) for r in db.execute("SELECT * FROM " + table + " ORDER BY 1")], ensure_ascii=False).encode()).hexdigest()

def select_quote(text, question, language):
    text = re.sub(r"\s+", " ", text).strip()
    suffix = "_ru" if language == "ru" else ""
    correct = question.get("answer_" + question["correct_answer"].lower() + suffix) or ""
    query = norm((question.get("question" + suffix if suffix else "question_es") or "") + " " + correct + " " + (question.get("explanation" + suffix if suffix else "explanation_es") or ""))
    stop = set("que cual cuales como para por los las del una uno unos unas con este esta esto cual es son segun texto guia qué какой какая какие согласно пособие тексте это для или при".split())
    words = {w for w in query.split() if len(w) > 3 and w not in stop}
    sentences = re.split(r"(?<=[.!?])\s+(?=[A-ZА-ЯЁ¿¡])", text)
    spans = [s for s in sentences if len(s) >= 25]
    if not spans:
        return text[:900], False
    def score(span):
        found = words & set(norm(span).split())
        key = norm(correct)
        return len(found) + (6 if len(key) > 2 and key in norm(span) else 0)
    best = max(spans, key=score)
    return best, score(best) >= 3

def repair(db, spanish_pages, patches):
    db.row_factory = sqlite3.Row
    db.execute("BEGIN IMMEDIATE")
    history_tables = ["attempts", "bookmarks", "review_queue", "exam_sessions", "study_settings"]
    saved = {table: digest_rows(db, table) for table in history_tables}
    original_ids = [r[0] for r in db.execute("SELECT id FROM questions ORDER BY id")]
    existing = [dict(r) for r in db.execute("SELECT * FROM material_pages WHERE source_id=1 ORDER BY page_number")]
    is_old_import = bool(existing and sum(bool(re.search("[А-Яа-яЁё]", r["text"])) for r in existing) > len(existing)//2)
    if is_old_import:
        db.execute("UPDATE material_pages SET source_id=2 WHERE source_id=1")
        db.execute("UPDATE material_chapters SET source_id=2 WHERE source_id=1")
        db.execute("UPDATE questions SET source_id=2 WHERE id>=409")
    db.execute("INSERT OR REPLACE INTO sources(id,title,url,document_type) VALUES(1,?,?,?)",
               ("Colombia, nuestra casa — guía española 2024 (190 páginas)", "/colombia_nuestra_casa.pdf", "official_study_guide"))
    db.execute("INSERT OR REPLACE INTO sources(id,title,url,document_type) VALUES(2,?,?,?)",
               ("Guía 2021 — traducción rusa (179 páginas, archivo)", "/colombia_nuestra_casa_ru.pdf", "archived_study_guide_translation"))
    db.execute("INSERT OR REPLACE INTO sources(id,title,url,document_type) VALUES(3,?,?,?)",
               ("Cancillería — requisitos del trámite de nacionalidad", "https://www.cancilleria.gov.co/taxonomy/term/3744", "official_web_reference"))
    db.execute("INSERT OR REPLACE INTO sources(id,title,url,document_type) VALUES(4,?,?,?)",
               ("Notas didácticas — geografía y español", "/study-notes.html", "editorial_study_note"))
    db.execute("INSERT OR REPLACE INTO sources(id,title,url,document_type) VALUES(5,?,?,?)",
               ("Constitución, artículo 2 — Gaceta del Congreso 678, página 16", "https://www.secretariasenado.gov.co/PDF/Camara/678.pdf#page=16", "official_web_reference"))
    db.execute("INSERT OR REPLACE INTO sources(id,title,url,document_type) VALUES(6,?,?,?)",
               ("IGAC — Análisis Geográficos 52: superficie terrestre", "https://biblioteca.igac.gov.co/janium/Documentos/revista_analisis_geograficos_52_2017.pdf", "official_web_reference"))
    db.execute("DELETE FROM material_pages WHERE source_id=1")
    db.executemany("INSERT INTO material_pages(source_id,page_number,text) VALUES(1,?,?)", enumerate(spanish_pages, 1))
    if not db.execute("SELECT 1 FROM material_chapters WHERE source_id=1 LIMIT 1").fetchone():
        db.executemany("INSERT INTO material_chapters(source_id,title,page_number) VALUES(1,?,?)",
                       [("Cultura y sociedad",4),("Geografía de Colombia",57),("Historia de Colombia",106),("Constitución",137),("Castellano",158)])
    fields = ["question_es","answer_a","answer_b","answer_c","answer_d","explanation_es"]
    changed=set()
    for row in db.execute("SELECT * FROM questions").fetchall():
        q=dict(row)
        for field in fields:
            value=q[field] or ""
            cleaned=value.replace("[видео]","[video]").replace("[подкаст]","[pódcast]")
            if cleaned!=value:
                db.execute(f"UPDATE questions SET {field}=? WHERE id=?",(cleaned,q["id"]));changed.add(q["id"])
    for key, values in patches.items():
        if not values:
            continue
        db.execute("UPDATE questions SET "+",".join(field+"=?" for field in values)+" WHERE id=?",
                   [*values.values(),int(key)])
        changed.add(int(key))
    # References for the original seed questions; web references have no PDF page.
    pages_by_id={1:180,3:3,4:12,6:70,7:117,8:43,9:11,10:9,20:3}
    for question_id,page in pages_by_id.items():
        db.execute("UPDATE questions SET source_id=1,source_page=? WHERE id=?",(page,question_id))
    for question_id in [2,5,17,18,19]:
        db.execute("UPDATE questions SET source_id=4,source_page=NULL WHERE id=?",(question_id,))
    for question_id in [11,12,13,14,15,16,418]:
        db.execute("UPDATE questions SET source_id=3,source_page=NULL WHERE id=?",(question_id,))
    # Keep edition-specific questions explicitly historical.
    for question_id, es, ru in [
        (423,"Según los créditos de la guía de 2021, ¿quién era el Presidente de la República mencionado en esa edición?","Кто указан президентом республики в выходных данных пособия издания 2021 года?"),
        (424,"¿Cuál es la fecha de la primera edición de la guía de 2021 utilizada como archivo?","Какова дата первого издания архивного пособия 2021 года?"),
        (425,"¿Cuántas páginas tiene la guía de 2021 utilizada como archivo?","Сколько страниц в архивном пособии 2021 года?")
    ]:
        db.execute("UPDATE questions SET question_es=?,question_ru=? WHERE id=?",(es,ru,question_id));changed.add(question_id)
    catalog={}
    for row in db.execute("SELECT source_id,page_number,text FROM material_pages"):
        catalog[(row["source_id"],row["page_number"])]=row["text"]
    moves=[];replaced=[];pending=[]
    db.execute("CREATE TABLE IF NOT EXISTS content_reference_audit(question_id INTEGER PRIMARY KEY, result TEXT NOT NULL, note TEXT NOT NULL, audited_at TEXT NOT NULL)")
    now=datetime.now().isoformat(timespec="seconds")
    for row in db.execute("SELECT * FROM questions").fetchall():
        q=dict(row);source=q["source_id"];page=q["source_page"];quote=q["source_quote"] or ""
        if source in [3,4,5,6]:
            result="editorial_note" if source==4 else "web_reference"
            db.execute("INSERT OR REPLACE INTO content_reference_audit VALUES(?,?,?,?)",(q["id"],result,"Reference is not a numbered page of the Spanish guide.",now))
            continue
        candidates={n:t for (s,n),t in catalog.items() if s==source}
        quoted=norm(quote);current=candidates.get(page,"")
        if quoted and len(quoted.split())>=8 and quoted not in norm(current):
            hits=[n for n,t in candidates.items() if quoted in norm(t)]
            if len(hits)==1:
                new_page=hits[0];moves.append([q["id"],page,new_page]);page=new_page
                db.execute("UPDATE questions SET source_page=? WHERE id=?",(page,q["id"]));current=candidates[page];changed.add(q["id"])
        # Correct source quotations only by taking a verbatim passage from that source.
        if not quoted or quoted not in norm(current):
            if current:
                quote,supported=select_quote(current,q,"ru" if source==2 else "es")
                if supported:
                    db.execute("UPDATE questions SET source_quote=? WHERE id=?",(quote,q["id"]));replaced.append(q["id"]);changed.add(q["id"])
                else:
                    pending.append(q["id"])
            else:
                pending.append(q["id"])
        result="needs_semantic_review" if q["id"] in pending else "verbatim_source_reference"
        db.execute("INSERT OR REPLACE INTO content_reference_audit VALUES(?,?,?,?)",(q["id"],result,"Source match is not independent approval of the answer.",now))
    remaining=db.execute("SELECT * FROM questions").fetchall()
    mixed=[r["id"] for r in remaining if any(re.search("[А-Яа-яЁё]",r[f] or "") for f in fields)]
    if mixed:
        raise ValueError("Russian text remains in Spanish fields: "+str(mixed))
    if original_ids!=[r[0] for r in db.execute("SELECT id FROM questions ORDER BY id")]:
        raise ValueError("Question IDs changed")
    if saved!={table:digest_rows(db,table) for table in history_tables}:
        raise ValueError("Learning history changed")
    if db.execute("PRAGMA integrity_check").fetchone()[0]!="ok":
        raise ValueError("Integrity failed")
    return {"questions":len(remaining),"changed_questions":len(changed),"page_corrections":moves,"verbatim_passage_replacements":len(replaced),"needs_semantic_review":pending,"spanish_fields_with_cyrillic":mixed,"history_unchanged":True,"independent_approval_added":False}

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--db",type=Path,default=ROOT/"database/colombia_exam.db")
    parser.add_argument("--spanish-pages",type=Path)
    parser.add_argument("--apply",action="store_true")
    args=parser.parse_args()
    if args.spanish_pages:
        pages=json.loads(args.spanish_pages.read_text(encoding="utf-8"))
    else:
        from pypdf import PdfReader
        logging.getLogger("pypdf").setLevel(logging.ERROR)
        pages=[p.extract_text() or "" for p in PdfReader(ROOT/"frontend/public/colombia_nuestra_casa.pdf").pages]
    if len(pages)!=190:
        raise ValueError("Wrong Spanish guide edition")
    db=sqlite3.connect(args.db)
    try:
        if args.apply:
            backup=args.db.with_name(args.db.stem+".backup-content-"+datetime.now().strftime("%Y%m%d-%H%M%S")+".db")
            with sqlite3.connect(backup) as target:
                db.backup(target)
            print("BACKUP",str(backup),flush=True)
        report=repair(db,pages,json.loads(PATCH.read_text(encoding="utf-8")))
        if args.apply:db.commit()
        else:db.rollback()
        print(json.dumps(report,ensure_ascii=False,indent=2),flush=True)
    finally:
        db.close()

if __name__=="__main__":
    main()
