"""Check web visitor isolation against a temporary, history-free bank."""
import hashlib,os,sqlite3,sys,tempfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'backend'))
source=Path(sys.argv[1]) if len(sys.argv)>1 else ROOT/'database/colombia_exam.db'
before=hashlib.sha256(source.read_bytes()).hexdigest()
with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as folder:
    bank=Path(folder)/'bank.db'
    src=sqlite3.connect(source.resolve().as_uri()+'?mode=ro',uri=True)
    dst=sqlite3.connect(bank);src.backup(dst);src.close()
    progress=['attempts','exam_sessions','bookmarks','review_queue','study_settings','exam_runs','exam_run_questions']
    for table in progress:dst.execute('DELETE FROM '+table)
    dst.commit();dst.execute('VACUUM');dst.close()
    bank_before=hashlib.sha256(bank.read_bytes()).hexdigest()
    os.environ.update(COLOMBIA_BANK_PATH=str(bank),COLOMBIA_STATE_DIR=str(Path(folder)/'state'),
                      COLOMBIA_SESSION_SECRET='isolated-test-key-'+'x'*32)
    import web_app
    from fastapi.testclient import TestClient
    with TestClient(web_app.app,base_url='https://testserver') as client:
        first=client.get('/api/session')
        second=client.get('/api/session')
        a=first.cookies.get('colombia_session');b=second.cookies.get('colombia_session')
        assert a and b and a!=b
        cookie_a={'Cookie':'colombia_session='+a}
        cookie_b={'Cookie':'colombia_session='+b}
        questions=client.get('/api/questions?limit=1000&locale=fr',headers=cookie_a).json()
        assert len(questions)==646 and all(q['content_locale']=='fr' for q in questions)
        assert all('correct_answer' not in q and 'display_explanation' not in q for q in questions)
        assert client.post('/api/questions/1/answer?locale=fr',json={'answer':'A'},headers=cookie_a).status_code==200
        assert len(client.get('/api/attempts',headers=cookie_a).json())==1
        assert client.get('/api/attempts',headers=cookie_b).json()==[]
        forged={'Cookie':'colombia_session='+a[:-1]+('0' if a[-1]!='0' else '1')}
        assert client.get('/api/attempts',headers=forged).json()==[]
        assert client.get('/openapi.json',headers=cookie_a).status_code==404
        assert client.post('/api/questions/generate',json={},headers=cookie_a).status_code==404
        bad={**cookie_a,'Origin':'https://outside.invalid'}
        assert client.post('/api/questions/1/answer',json={'answer':'A'},headers=bad).status_code==403
        assert len(client.get('/api/attempts',headers=cookie_a).json())==1
    assert hashlib.sha256(bank.read_bytes()).hexdigest()==bank_before
    assert max(p.stat().st_size for p in (Path(folder)/'state').glob('*.db'))<200000
assert hashlib.sha256(source.read_bytes()).hexdigest()==before
print('PASS: visitor isolation, signed cookies, hidden keys, immutable bank, disabled authoring and unchanged original history')
