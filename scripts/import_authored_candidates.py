"""Import an authored bundle into an isolated SQLite candidate; never edit the source DB."""
import argparse, hashlib, json, sqlite3
from pathlib import Path

LOCALES = ['es', 'ru', 'en', 'de', 'fr', 'zh-Hans']
def digest(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def canonical(value): return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':'))
def question_hash(q): return hashlib.sha256(canonical(q).encode()).hexdigest()
def readonly(p): return sqlite3.connect(p.resolve().as_uri() + '?mode=ro', uri=True)
def counts(db):
    return {name: db.execute('SELECT COUNT(*) FROM '+name).fetchone()[0] for name in ['questions','attempts','exam_sessions','bookmarks','review_queue']}

def run(source, candidate, bundle, report):
    if candidate.resolve()==source.resolve(): raise ValueError('Candidate must differ from source')
    entries=[json.loads(line) for line in bundle.read_text(encoding='utf-8').splitlines() if line.strip()]
    manifest=entries[0]; rows=[x for x in entries if x.get('type')=='question']
    assert manifest['locales']==LOCALES and len(rows)==147
    assert len({r['payload']['id'] for r in rows})==147
    for r in rows:
        q=r['payload']; assert question_hash(q)==r['question_sha256']
        assert len(q['options'])==4 and len({o['id'] for o in q['options']})==4
        assert q['correct_option_id'] in {o['id'] for o in q['options']}
        for locale in LOCALES:
            assert q['prompt'][locale] and q['explanation'][locale]
            assert len({o['text'][locale] for o in q['options']})==4
    source_hash=digest(source)
    with readonly(source) as src:
        before=counts(src)
        if not candidate.exists():
            candidate.parent.mkdir(parents=True,exist_ok=True)
            with sqlite3.connect(candidate) as dest: src.backup(dest)
    if not candidate.exists(): raise ValueError('Copy failed')
    with sqlite3.connect(candidate) as db:
        db.execute('PRAGMA foreign_keys=ON')
        db.executescript('''
        CREATE TABLE IF NOT EXISTS authored_imports (
          external_id TEXT PRIMARY KEY, question_id INTEGER UNIQUE NOT NULL,
          question_sha256 TEXT NOT NULL, chapter_file TEXT NOT NULL,
          chapter_revision INTEGER NOT NULL, chapter_sha256 TEXT NOT NULL,
          payload_json TEXT NOT NULL, FOREIGN KEY(question_id) REFERENCES questions(id));
        CREATE TABLE IF NOT EXISTS authored_localizations (
          external_id TEXT NOT NULL, locale TEXT NOT NULL, prompt TEXT NOT NULL,
          options_json TEXT NOT NULL, explanation TEXT NOT NULL,
          review_status TEXT NOT NULL DEFAULT 'pending', PRIMARY KEY(external_id,locale),
          FOREIGN KEY(external_id) REFERENCES authored_imports(external_id));
        ''')
        imported=skipped=0
        for r in rows:
            q=r['payload']; found=db.execute('SELECT question_sha256 FROM authored_imports WHERE external_id=?',(q['id'],)).fetchone()
            if found:
                if found[0]!=r['question_sha256']: raise ValueError('Immutable ID changed: '+q['id'])
                skipped+=1; continue
            ref=q['source_ref']; guide_url=ref.get('guide_url') or ref.get('url')
            src=db.execute('SELECT id FROM sources WHERE url=?',(guide_url,)).fetchone()
            if not src: raise ValueError('Unknown source URL')
            labels=[o['id'] for o in q['options']]; key='ABCD'[labels.index(q['correct_option_id'])]
            values=[q['prompt']['es'],q['prompt']['ru']]
            for o in q['options']: values.extend([o['text']['es'],o['text']['ru']])
            values.extend([key,r['module'],q['explanation']['es'],q['explanation']['ru'],'draft',src[0],ref['guide_page']])
            cur=db.execute('''INSERT INTO questions(question_es,question_ru,answer_a,answer_a_ru,
                answer_b,answer_b_ru,answer_c,answer_c_ru,answer_d,answer_d_ru,correct_answer,
                topic,explanation_es,explanation_ru,status,source_id,source_page)
                VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)''',values)
            db.execute('INSERT INTO authored_imports VALUES(?,?,?,?,?,?,?)',
                (q['id'],cur.lastrowid,r['question_sha256'],r['chapter_file'],r['chapter_revision'],r['chapter_sha256'],canonical(q)))
            db.executemany('INSERT INTO authored_localizations VALUES(?,?,?,?,?,?)',
                [(q['id'],l,q['prompt'][l],canonical([{'id':o['id'],'text':o['text'][l]} for o in q['options']]),q['explanation'][l],'pending') for l in LOCALES])
            imported+=1
        after=counts(db)
        assert after['questions']==before['questions']+147
        assert all(after[k]==before[k] for k in before if k!='questions')
        assert db.execute('SELECT COUNT(*) FROM authored_localizations').fetchone()[0]==882
        assert db.execute("SELECT COUNT(*) FROM questions q JOIN authored_imports i ON q.id=i.question_id WHERE q.status!='draft'").fetchone()[0]==0
        assert db.execute("SELECT COUNT(*) FROM authored_localizations WHERE review_status!='pending'").fetchone()[0]==0
        assert db.execute("SELECT COUNT(*) FROM questions q JOIN authored_imports i ON q.id=i.question_id WHERE q.status IN ('reviewed','verified','ai_reviewed')").fetchone()[0]==0
        mapping=[]
        for r in rows:
            q=r['payload']; row=db.execute('SELECT q.id,q.correct_answer,i.payload_json FROM questions q JOIN authored_imports i ON q.id=i.question_id WHERE i.external_id=?',(q['id'],)).fetchone()
            assert json.loads(row[2])==q
            assert q['options']['ABCD'.index(row[1])]['id']==q['correct_option_id']
            mapping.append({'external_id':q['id'],'sqlite_id':row[0],'correct_letter':row[1],'correct_option_id':q['correct_option_id']})
        assert db.execute('PRAGMA integrity_check').fetchone()[0]=='ok'
        assert not db.execute('PRAGMA foreign_key_check').fetchall()
    assert digest(source)==source_hash
    result={'result':'PASS','source_database_sha256':source_hash,'candidate':str(candidate),'bundle_sha256':digest(bundle),'inserted':imported,'skipped':skipped,'before':before,'after':after,'candidate_questions':147,'localized_rows':882,'student_question_selection_matches':0,'keys_roundtrip':'PASS','integrity':'ok','source_database_unchanged':True,'independent_review':'pending','published':False,'runtime_status':'not_started','mapping':mapping}
    report.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({k:v for k,v in result.items() if k!='mapping'},ensure_ascii=False))

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--source',type=Path,required=True);parser.add_argument('--candidate',type=Path,required=True);parser.add_argument('--bundle',type=Path,required=True);parser.add_argument('--report',type=Path,required=True)
    args=parser.parse_args();run(args.source,args.candidate,args.bundle,args.report)
