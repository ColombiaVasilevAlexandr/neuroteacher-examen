import argparse, functools, gc, hashlib, http.server, json, sqlite3, sys, tempfile, threading, time, socket
from pathlib import Path
import uvicorn
from playwright.sync_api import sync_playwright
parser=argparse.ArgumentParser(description='Isolated auxiliary UI regression against the 147-question candidate; requires Playwright, Chrome and backend dependencies.')
parser.add_argument('--candidate',type=Path,required=True)
parser.add_argument('--chrome',required=True)
parser.add_argument('--report',type=Path,required=True)
args=parser.parse_args()
root=Path(__file__).resolve().parents[1]
args.report.parent.mkdir(parents=True,exist_ok=True)
sys.path.insert(0,str(root/'backend'))
import main
class QuietHandler(http.server.SimpleHTTPRequestHandler):
    def log_message(self,*args):pass
    def copyfile(self,source,outputfile):
        try:super().copyfile(source,outputfile)
        except (ConnectionResetError,BrokenPipeError):pass
original_db=main.DB_PATH
candidate=args.candidate
hashes={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in (original_db,candidate)}
with tempfile.TemporaryDirectory() as folder:
    main.DB_PATH=Path(folder)/'browser.db'
    src=sqlite3.connect(candidate.resolve().as_uri()+'?mode=ro',uri=True)
    dest=sqlite3.connect(main.DB_PATH);src.backup(dest);src.close();dest.close()
    api_socket=socket.socket();api_socket.bind(('127.0.0.1',0))
    api_port=api_socket.getsockname()[1]
    api=uvicorn.Server(uvicorn.Config(main.app,host='127.0.0.1',port=api_port,log_level='error'))
    thread=threading.Thread(target=lambda:api.run(sockets=[api_socket]),daemon=True);thread.start()
    web=http.server.ThreadingHTTPServer(('127.0.0.1',0),functools.partial(QuietHandler,directory=str(root/'frontend/public')))
    threading.Thread(target=web.serve_forever,daemon=True).start()
    for _ in range(100):
        if api.started:break
        time.sleep(.05)
    assert api.started,'isolated API did not start'
    try:
        with sync_playwright() as p:
            browser=p.chromium.launch(executable_path=args.chrome,headless=True,args=["--mute-audio"])
            context=browser.new_context(viewport={'width':1280,'height':900})
            context.add_init_script('window.COLOMBIA_API_BASE='+json.dumps(f'http://127.0.0.1:{api_port}/api')+';')
            allowed=(f'http://127.0.0.1:{web.server_port}',f'http://127.0.0.1:{api_port}')
            def guard(route):
                url=route.request.url
                if not any(url.startswith(origin+'/') for origin in allowed):route.abort();return
                if '/api/ai/' in url or '/api/consultant/' in url or '/api/tts' in url:
                    route.fulfill(status=200,content_type='application/json',body='{"available":false,"mode":"local_fallback"}');return
                route.continue_()
            context.route('**/*',guard)
            page=context.new_page();errors=[]
            page.on('pageerror',lambda error:errors.append(str(error)))
            page.goto(f'http://127.0.0.1:{web.server_port}',wait_until='networkidle')
            page.locator('select.language').wait_for(timeout=15000)
            from datetime import date,timedelta
            assert context.request.put(f'http://127.0.0.1:{api_port}/api/study-plan',data={'exam_date':(date.today()+timedelta(days=35)).isoformat()}).ok
            page.reload(wait_until='networkidle')
            page.locator('.audio-library audio').wait_for()
            page.wait_for_function('Number.isFinite(document.querySelector(".audio-library audio").duration)',timeout=12000)
            duration=page.locator('.audio-library audio').evaluate('(a)=>a.duration')
            def track_player():
                page.locator('.audio-library .continue').click()
                page.wait_for_function('document.querySelector(".audio-library audio").currentTime>2.5',timeout=12000)
                page.locator('.audio-library .pause').click()
                value=page.locator('.audio-library audio').evaluate('(a)=>a.currentTime')
                page.evaluate('window.qaAudio=document.querySelector(".audio-library audio")')
                return value
            position=track_player()
            print(json.dumps({'audio_duration':duration,'played_and_paused_at':position}),flush=True)
            observed=[]
            for locale in main.LOCALES:
                page.select_option('select.language',locale)
                page.wait_for_function('(locale)=>document.documentElement.lang===locale && document.querySelector(".streak .calendar-history")?.dataset.historyLoaded===locale',arg=locale)
                def ui(key,values=None):return page.evaluate('([key,values])=>window.ColombiaLocales.ui(key,values)',[key,values or {}])
                assert page.locator('.study-plan-card h2').inner_text()==ui('today')
                assert page.locator('.study-plan-card .save').inner_text()==ui('save')
                assert page.locator('.audio-library h2').inner_text()==ui('audioTitle')
                assert page.locator('.audio-library .continue').inner_text()==ui('audioContinue')
                assert page.evaluate('document.querySelector(".audio-library audio")===window.qaAudio')
                print(json.dumps({'audio_state':page.locator('.audio-library audio').evaluate('(a)=>({time:a.currentTime,duration:a.duration,seeking:a.seeking,ready:a.readyState})'),'locale':locale}),flush=True)
                assert abs(page.locator('.audio-library audio').evaluate('(a)=>a.currentTime')-position)<1
                titles=page.locator('.study-plan-step strong').all_text_contents()
                assert ui('new') in titles and ui('reviewStep') in titles and ui('test') in titles
                expected=page.evaluate('()=>new Intl.DateTimeFormat(window.ColombiaLocales.dateLocale,{day:"numeric",month:"short"}).format(new Date(new Date().toISOString().slice(0,10)+"T12:00:00"))')
                print(json.dumps({'calendar_expected':expected,'calendar_actual':page.locator('.streak .calendar-history b').last.inner_text(),'api_last':context.request.get(f'http://127.0.0.1:{api_port}/api/dashboard').json()['calendar'][-1]}),flush=True)
                assert page.locator('.streak .calendar-history b').last.inner_text()==expected
                calendar_title=page.locator('.streak .calendar-history i').last.get_attribute('title')
                assert calendar_title==ui('sessions',{'count':context.request.get(f'http://127.0.0.1:{api_port}/api/dashboard').json()['calendar'][-1]['attempts']})
                with page.expect_response(lambda r:'/study-plan/questions' in r.url) as lesson:
                    page.locator('.study-plan-card .start').click()
                lesson_total=len(lesson.value.json()['questions'])
                page.locator('.study-session h2').wait_for()
                assert page.locator('.study-session .study-plan-muted').first.inner_text().split(' · ')[0]==ui('questionCount',{'index':1,'total':lesson_total})
                if locale=='fr':
                    with page.expect_response(lambda r:'/answer' in r.url and r.request.method=='POST') as saved:
                        page.locator('.study-session [data-answer]').first.click()
                    assert saved.value.ok
                page.locator('.study-session .close').click()
                page.locator('[data-plan-action="review"]').click()
                page.locator('.review-session').wait_for()
                page.locator('.review-session .review-answers button').first.wait_for()
                assert page.locator('main header b').inner_text()==ui('reviewHeading')
                if locale=='fr':
                    with page.expect_response(lambda r:'/answer' in r.url and r.request.method=='POST') as saved:
                        page.locator('.review-session .review-answers button').first.click()
                    result=saved.value.json()
                    page.wait_for_function('document.querySelector(".review-result")?.textContent.length>5')
                    assert result['display_explanation'] in page.locator('.review-result').inner_text()
                review_caption=page.locator('.review-session small').first.inner_text()
                assert review_caption==ui('reviewCount',{'index':1,'total':20})
                page.locator('main button.back').click()
                page.get_by_role('button',name=__import__('re').compile('^'+__import__('re').escape(page.evaluate('window.ColombiaLocales.text("Respuestas correctas")')))).first.click()
                page.locator('main[data-screen="Respuestas correctas"] .activity-row').first.wait_for()
                history_dates=page.locator('main .activity-row small').all_text_contents()
                assert history_dates
                page.locator('main button.back').click()
                observed.append({'locale':locale,'plan':'PASS','audio_labels_and_player_preserved':'PASS','calendar':'PASS','review':'PASS','history':'PASS'})
                print(json.dumps({'completed_locale':locale}),flush=True)
                # The homepage creates a new player after navigating back; track that instance.
                page.locator('.audio-library audio').wait_for()
                page.wait_for_function('Number.isFinite(document.querySelector(".audio-library audio").duration)')
                position=track_player()
            page.evaluate("(()=>{const a=document.createElement('a');a.id='qa-pdf';a.className='language-mark';a.href='/colombia_nuestra_casa.pdf#page=25';document.body.append(a)})()")
            page.locator('#qa-pdf + .pdf-language-switcher').wait_for()
            assert page.locator('#qa-pdf').get_attribute('href')=='/colombia_nuestra_casa.pdf#page=25'
            page.locator('#qa-pdf + .pdf-language-switcher [data-pdf="ru"]').click()
            assert page.locator('#qa-pdf').get_attribute('href')=='/colombia_nuestra_casa_ru.pdf#page=1'
            page.select_option('select.language','fr')
            assert page.locator('#qa-pdf').inner_text()==ui('pdfRussian')+' · 2021'
            assert page.locator('#qa-pdf').get_attribute('href')=='/colombia_nuestra_casa_ru.pdf#page=1'
            pdf_headers=[]
            for name in ('colombia_nuestra_casa.pdf','colombia_nuestra_casa_ru.pdf'):
                response=context.request.head(f'http://127.0.0.1:{web.server_port}/{name}')
                assert response.ok and response.headers['content-type']=='application/pdf'
                pdf_headers.append({'asset':name,'status':response.status,'bytes':int(response.headers['content-length'])})
            context.route('**/api/review/due?*',lambda route:route.fulfill(status=200,content_type='application/json',body='[]'))
            page.locator('[data-plan-action="review"]').click()
            page.locator('.review-done h2').wait_for()
            assert page.locator('.review-done h2').inner_text()==ui('reviewEmpty')
            page.locator('main button.back').click()
            assert not errors,errors
            with main.conn() as db:
                assert db.execute("SELECT COUNT(*) FROM questions WHERE status='draft'").fetchone()[0]==147
                assert db.execute("SELECT COUNT(*) FROM authored_localizations WHERE review_status='pending'").fetchone()[0]==882
                assert db.execute('PRAGMA integrity_check').fetchone()[0]=='ok'
            del db
            report={'result':'PASS','browser':browser.version,'locales':observed,'catalog_messages':page.evaluate('window.ColombiaLocales.messageKeys.length'),'audio_metadata_duration_seconds':duration,'audio_language_or_content_changed':False,'pdf_switch_and_http_headers':pdf_headers,'empty_review':'PASS','js_errors':errors,'source_sha256':hashes,'source_databases_unchanged':True,'independent_review':'pending','production_changed':False,'published':False}
            args.report.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
            print(json.dumps(report,ensure_ascii=True),flush=True)
            browser.close()
    finally:
        web.shutdown();web.server_close();api.should_exit=True;thread.join(timeout=10)
        main.DB_PATH=original_db
        gc.collect()
assert all(hashlib.sha256(Path(path).read_bytes()).hexdigest()==value for path,value in hashes.items())
print('PASS: isolated browser launch; source databases unchanged')
