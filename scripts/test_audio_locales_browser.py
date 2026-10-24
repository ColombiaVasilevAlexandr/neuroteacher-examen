"""Read-only browser playback acceptance for the four translated audio libraries."""
import argparse,json,sys
from pathlib import Path
sys.path.insert(0,str(Path.home()/'AppData/Local/Temp/colombia-audit-deps'))
from playwright.sync_api import sync_playwright
def main():
 parser=argparse.ArgumentParser(description=__doc__)
 parser.add_argument('--url',default='http://127.0.0.1:5173/')
 parser.add_argument('--chrome',default=r'C:\Program Files\Google\Chrome\Application\chrome.exe')
 parser.add_argument('--locales',nargs='+',default=['en','zh-Hans','fr','de'])
 args=parser.parse_args()
 with sync_playwright() as p:
  browser=p.chromium.launch(executable_path=args.chrome,headless=True)
  page=browser.new_page()
  errors=[];page.on('pageerror',lambda exc:errors.append(str(exc)))
  page.goto(args.url);page.locator('select.language').wait_for()
  for locale in args.locales:
   page.locator('select.language').select_option(locale)
   page.wait_for_function("document.querySelector('.audio-library audio')?.readyState>=1")
   assert page.locator('.audio-library audio').evaluate('(a)=>a.paused'),'Unexpected autoplay'
   # Continuous listening proceeds from the selected lesson; explicitly choose lesson 1.
   first=page.locator('.audio-lesson[data-index="0"]')
   if first.count():
    first.click()
    page.wait_for_function("document.querySelector('.audio-library audio')?.readyState>=2")
    page.locator('.audio-library .pause').click()
   page.locator('.audio-library .all').click()
   for index in range(6):
    page.wait_for_function("({locale,n})=>{const a=document.querySelector('.audio-library audio');return a.src.includes('/audio/'+locale+'/lesson-0'+n+'-')&&a.readyState>=2&&!a.paused&&a.currentTime>0}",arg={'locale':locale,'n':index+1},timeout=30000)
    info=page.locator('.audio-library audio').evaluate('(a)=>({duration:a.duration,error:a.error?.code||null})')
    assert info['duration']>180 and info['error'] is None
    print(json.dumps({'locale':locale,'lesson':index+1,'duration':info['duration'],'continuous_play':'PASS'}),flush=True)
    page.locator('.audio-library audio').evaluate('(a)=>a.currentTime=a.duration-.2')
    if index==5:page.wait_for_function("document.querySelector('.audio-library audio').ended",timeout=10000)
   page.locator('.audio-library .stop').click()
   assert page.locator('.audio-library audio').evaluate('(a)=>a.currentTime')==0
   page.locator('.audio-library audio').evaluate('(a)=>a.currentTime=17')
   page.locator('.audio-library .continue').click()
   page.wait_for_function("!document.querySelector('.audio-library audio').paused")
   page.locator('.audio-library .pause').click()
  for locale in args.locales:
   page.locator('select.language').select_option(locale)
   page.wait_for_function("document.querySelector('.audio-library audio').readyState>=1")
   assert page.locator('.audio-library audio').evaluate('(a)=>a.currentTime')>=17
   assert page.locator('.audio-library audio').evaluate('(a)=>a.paused')
  page.set_viewport_size({'width':390,'height':844})
  assert page.locator('select.language').is_visible()
  assert page.locator('select.language').evaluate('(e)=>parseFloat(getComputedStyle(e).fontSize)')>=14
  assert not errors,errors
  browser.close()
 print('PASS: audio locale routing, automatic transitions, stop, separate progress, mobile selector and no JS errors',flush=True)
if __name__=='__main__':main()
