"""Isolated browser acceptance for English/Chinese content; never writes the user DB."""
import gc,functools,hashlib,http.server,json,socket,sqlite3,sys,tempfile,threading,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
for folder in [ROOT/'backend',Path(r'C:\Users\user\AppData\Local\Temp\colombia-audit-deps')]:
 sys.path.insert(0,str(folder))
import uvicorn
from playwright.sync_api import sync_playwright
import main
class Quiet(http.server.SimpleHTTPRequestHandler):
 def log_message(self,*args):pass
 def copyfile(self,source,out):
  try:super().copyfile(source,out)
  except (BrokenPipeError,ConnectionResetError):pass
def run():
 source=Path(sys.argv[1]) if len(sys.argv)>1 else ROOT/'database/colombia_exam.db'
 before=hashlib.sha256(source.read_bytes()).hexdigest()
 original=main.DB_PATH
 with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as folder:
  main.DB_PATH=Path(folder)/'browser.db'
  src=sqlite3.connect(source.resolve().as_uri()+'?mode=ro',uri=True);dest=sqlite3.connect(main.DB_PATH);src.backup(dest);src.close();dest.close()
  sock=socket.socket();sock.bind(('127.0.0.1',0));port=sock.getsockname()[1]
  server=uvicorn.Server(uvicorn.Config(main.app,host='127.0.0.1',port=port,log_level='error'))
  thread=threading.Thread(target=lambda:server.run(sockets=[sock]),daemon=True);thread.start()
  web=http.server.ThreadingHTTPServer(('127.0.0.1',0),functools.partial(Quiet,directory=str(ROOT/'frontend/public')))
  threading.Thread(target=web.serve_forever,daemon=True).start()
  with sync_playwright() as p:
   browser=p.chromium.launch(executable_path=r'C:\Program Files\Google\Chrome\Application\chrome.exe',headless=True)
   try:
    context=browser.new_context()
    for _ in range(40):
     try:
      if context.request.get(f'http://127.0.0.1:{port}/api/health').ok:break
     except Exception:pass
     time.sleep(.25)
    # Settings changed only in the temporary clone.
    with main.conn() as db:
     db.execute("INSERT OR REPLACE INTO study_settings(key,value) VALUES('exam_date','2026-12-01')")
    for locale,voice in [('en','en-US'),('zh-Hans','zh-CN')]:
     rows=context.request.get(f'http://127.0.0.1:{port}/api/questions?limit=1000&locale={locale}').json()
     assert len(rows)==646
     assert all(q['content_locale']==locale and q['translation_available'] for q in rows)
     assert all('correct_answer' not in q and 'display_explanation' not in q for q in rows)
     page=context.new_page();errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
     page.add_init_script("localStorage.setItem('neuroteacher-language',"+json.dumps(locale)+");window.voicePlayed=false;const nativePlay=HTMLMediaElement.prototype.play;HTMLMediaElement.prototype.play=function(){this.addEventListener('timeupdate',()=>{if(this.currentTime>0)window.voicePlayed=true});return nativePlay.call(this)}")
     page.route('**/runtime-config.js*',lambda route:route.fulfill(content_type='application/javascript',body=f"window.COLOMBIA_API_BASE='http://127.0.0.1:{port}/api';"))
     page.goto(f'http://127.0.0.1:{web.server_port}/')
     page.locator('.study-plan-card .start').wait_for()
     with page.expect_response(lambda r:'/study-plan/questions' in r.url) as response:
      page.locator('.study-plan-card .start').click()
     item=response.value.json()['questions'][0]
     button=page.locator('.study-session .localized-question-speech');button.wait_for()
     assert page.locator('.study-session h2').inner_text()==item['display_question']
     with page.expect_request(lambda req:'/consultant/speech' in req.url) as speech:
      button.click()
     assert speech.value.post_data_json['locale']==voice
     page.wait_for_function('window.voicePlayed',timeout=30000)
     button.click() # Stop while speech is playing.
     with page.expect_response(lambda r:'/answer' in r.url and r.request.method=='POST') as answer:
      page.locator('.study-session [data-answer]').first.click()
     result=answer.value.json()
     assert result['content_locale']==locale and result['display_explanation']
     assert not errors,errors
     print(json.dumps({'locale':locale,'all_questions_translated':len(rows),'hidden_keys':True,'question_audio':voice,'translated_answer':True,'js_errors':errors}),flush=True)
     page.close()
    context.close()
   finally:browser.close();server.should_exit=True;thread.join(timeout=10);web.shutdown()
  main.DB_PATH=original
  gc.collect()
 assert hashlib.sha256(source.read_bytes()).hexdigest()==before
 print('PASS isolated English/Chinese question UI, real TTS playback, hidden answers and unchanged original database',flush=True)
if __name__=='__main__':run()
