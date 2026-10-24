"""Read-only validation of the repaired question/source catalog."""
import argparse
import json
import re
import sqlite3
from pathlib import Path
from repair_question_content import norm

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--db",type=Path,default=Path(__file__).resolve().parents[1]/"database/colombia_exam.db")
    args=parser.parse_args()
    db=sqlite3.connect(args.db.resolve().as_uri()+"?mode=ro",uri=True)
    db.row_factory=sqlite3.Row
    fields=["question_es","answer_a","answer_b","answer_c","answer_d","explanation_es"]
    problems=[];count=0;pdf_count=0
    for row in db.execute("SELECT * FROM questions"):
        q=dict(row);count+=1
        if any(re.search("[А-Яа-яЁё]",q[f] or "") for f in fields):
            problems.append([q["id"],"wrong_content_language"])
        source=db.execute("SELECT * FROM sources WHERE id=?",(q["source_id"],)).fetchone()
        if not source or not source["url"]:
            problems.append([q["id"],"missing_source"]);continue
        if q["source_id"] in [1,2]:
            page=db.execute("SELECT text FROM material_pages WHERE source_id=? AND page_number=?",(q["source_id"],q["source_page"])).fetchone()
            if not page or not norm(q["source_quote"]) or norm(q["source_quote"]) not in norm(page[0]):
                problems.append([q["id"],"quote_page_mismatch"])
            pdf_count+=1
    if db.execute("PRAGMA integrity_check").fetchone()[0]!="ok":
        problems.append(["database","integrity"])
    print(json.dumps({"questions":count,"pdf_references":pdf_count,"problems":problems,"answer_approval":"not_inferred_from_reference_checks"},ensure_ascii=False,indent=2))
    db.close()
    if problems:raise SystemExit(1)

if __name__=="__main__":
    main()
