"""Public web adapter: immutable shared question bank, isolated visitor progress."""
from contextvars import ContextVar
from pathlib import Path
import hashlib,hmac,os,re,secrets,sqlite3
from fastapi import Request
from fastapi.responses import JSONResponse
import main as core

BANK=Path(os.getenv('COLOMBIA_BANK_PATH',str(core.DB_PATH)))
STATE=Path(os.getenv('COLOMBIA_STATE_DIR',str(core.ROOT/'web-state')))
SECRET=os.environ.get('COLOMBIA_SESSION_SECRET','')
ORIGIN=os.getenv('COLOMBIA_PUBLIC_ORIGIN','https://nt.es-pro.org')
if len(SECRET)<32:
    raise RuntimeError('A private web session signing key is required')
PROGRESS={'attempts','exam_sessions','bookmarks','review_queue','study_settings','exam_runs','exam_run_questions'}
session_context=ContextVar('colombia_web_session',default=None)
connection_context=ContextVar('colombia_web_connections',default=None)
with sqlite3.connect(BANK.resolve().as_uri()+'?mode=ro',uri=True) as bank:
    schema={name:sql for name,sql in bank.execute("SELECT name,sql FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")}
if not PROGRESS <= set(schema):
    raise RuntimeError('The published bank does not have the expected progress schema')
CONTENT=set(schema)-PROGRESS

def connection():
    session_id=session_context.get()
    if not session_id:
        raise RuntimeError('Progress database requested outside a visitor session')
    STATE.mkdir(parents=True,exist_ok=True)
    db=sqlite3.connect(STATE/(session_id+'.db'),timeout=15,check_same_thread=False,uri=True)
    db.row_factory=sqlite3.Row
    try:
        for table in sorted(PROGRESS):
            db.execute(schema[table].replace('CREATE TABLE ','CREATE TABLE IF NOT EXISTS ',1))
        db.commit()
        db.execute('ATTACH DATABASE ? AS bank',(BANK.resolve().as_uri()+'?mode=ro&immutable=1',))
        for table in sorted(CONTENT):
            db.execute('CREATE TEMP VIEW "'+table+'" AS SELECT * FROM bank."'+table+'"')
        connection_context.get().append(db)
        return db
    except Exception:
        db.close()
        raise

# This release already contains a migrated bank. Startup must not mutate it.
core.initialize=lambda:None
core.conn=connection
app=core.app
app.openapi_url=None
app.docs_url=None
app.redoc_url=None

@app.get('/api/session')
def visitor_session():
    return {'status':'ok','progress':'private_to_this_browser'}

def signed(session_id):
    return session_id+'.'+hmac.new(SECRET.encode(),session_id.encode(),hashlib.sha256).hexdigest()

def parse_cookie(value):
    if not isinstance(value,str) or not re.fullmatch(r'[a-f0-9]{32}\.[a-f0-9]{64}',value):
        return None
    session_id=value.split('.')[0]
    return session_id if hmac.compare_digest(value,signed(session_id)) else None

@app.middleware('http')
async def private_progress(request:Request,call_next):
    if request.url.path in ('/docs','/redoc','/openapi.json','/api/questions/generate'):
        return JSONResponse({'detail':'Not available in the public study application'},status_code=404)
    if request.method not in ('GET','HEAD','OPTIONS') and request.headers.get('origin') not in (None,ORIGIN):
        return JSONResponse({'detail':'Origin is not allowed'},status_code=403)
    if int(request.headers.get('content-length','0') or 0)>262144:
        return JSONResponse({'detail':'Request is too large'},status_code=413)
    current=parse_cookie(request.cookies.get('colombia_session'))
    session_id=current or secrets.token_hex(16)
    session_token=session_context.set(session_id)
    connections_token=connection_context.set([])
    try:
        response=await call_next(request)
        response.headers['Cache-Control']='no-store'
        if not current:
            response.set_cookie('colombia_session',signed(session_id),max_age=31536000,
                                httponly=True,secure=True,samesite='lax',path='/colombia')
        return response
    finally:
        for db in connection_context.get():
            db.close()
        connection_context.reset(connections_token)
        session_context.reset(session_token)
