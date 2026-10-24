"""Build English/Chinese learning translations and complete audio lessons.
Uses the configured DeepSeek account. Keeps progress so reruns resume.
Never modifies the exam database or marks translations human-approved.
"""
import asyncio, concurrent.futures, hashlib, json, os, re, sqlite3, sys, threading, time
from pathlib import Path
from urllib import request, error
from dotenv import load_dotenv
import edge_tts

ROOT=Path(__file__).resolve().parents[1]
ACTIVE=Path('F:/видио материалы/examen-de-colombia')
OUT=ROOT/'data/localized-content'
OUT.mkdir(parents=True,exist_ok=True)
load_dotenv(ROOT/'.env')
KEY=os.getenv('DEEPSEEK_API_KEY')
if not KEY: raise SystemExit('Configured translation API key is missing')
MODEL=os.getenv('DEEPSEEK_MODEL','deepseek-chat')
LOCK=threading.Lock()
LANGS={'en':('English','en-US-JennyNeural'),'zh-Hans':('Simplified Chinese','zh-CN-XiaoxiaoNeural')}
def atomic(path,data):
 path.parent.mkdir(parents=True,exist_ok=True)
 tmp=path.with_suffix(path.suffix+'.tmp')
 tmp.write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding='utf-8')
 tmp.replace(path)
def api(system,payload):
 body=json.dumps({'model':MODEL,'messages':[{'role':'system','content':system},{'role':'user','content':json.dumps(payload,ensure_ascii=False)}],'temperature':0,'max_tokens':8192,'response_format':{'type':'json_object'}}).encode()
 req=request.Request('https://api.deepseek.com/chat/completions',data=body,headers={'Authorization':'Bearer '+KEY,'Content-Type':'application/json'})
 last=None
 for attempt in range(4):
  try:
   with request.urlopen(req,timeout=220) as response: data=json.load(response)
   choice=data['choices'][0]
   if choice.get('finish_reason')!='stop':raise ValueError('Incomplete model output')
   return json.loads(choice['message']['content'])
  except Exception as exc:
   last=exc
   if attempt<3:time.sleep(2*(attempt+1))
 raise RuntimeError(type(last).__name__+' during translation')
def source_hash(q):
 fields={k:q[k] for k in ['question_es','answer_a','answer_b','answer_c','answer_d','explanation_es','correct_answer']}
 return hashlib.sha256(json.dumps(fields,ensure_ascii=False,sort_keys=True).encode()).hexdigest()
def valid(items,rows,locale):
 if not isinstance(items,list) or len(items)!=len(rows):raise ValueError('Wrong translation count')
 result={int(x['id']):x for x in items}
 if set(result)!={x['id'] for x in rows}:raise ValueError('Question IDs changed')
 for q in rows:
  t=result[q['id']]
  if set(t.get('options',{}))!=set('ABCD'):raise ValueError('Option keys changed')
  values=[t.get('question'),t.get('explanation'),*t['options'].values()]
  if not all(isinstance(v,str) and v.strip() for v in values):raise ValueError('Empty translated field')
  if re.search('[А-Яа-яЁё]',' '.join(values)):raise ValueError('Russian leaked into target')
  if locale=='zh-Hans' and not re.search('[\u3400-\u9fff]',t['question']):raise ValueError('Missing Chinese prompt')
  if t.get('correct_answer')!=q['correct_answer']:raise ValueError('Answer key changed')
  t['source_hash']=source_hash(q)
  t['translation_method']='machine_translation_with_second_pass'
  t['independent_approval']=False
 return result
def questions_job(locale,index,rows):
 path=OUT/f'questions-{locale}-{index:03}.json'
 if path.exists():
  try:
   data=json.loads(path.read_text(encoding='utf-8'))
   if all(data[str(q['id'])]['source_hash']==source_hash(q) for q in rows):return ('questions',locale,len(rows),'cached')
  except Exception:pass
 name=LANGS[locale][0]
 payload=[{'id':q['id'],'question':q['question_es'],'options':{k:q['answer_'+k.lower()] for k in 'ABCD'},'explanation':q['explanation_es'],'correct_answer':q['correct_answer']} for q in rows]
 rules=f"""Translate the supplied Colombian citizenship practice questions faithfully into {name}. Return JSON {{"items":[{{"id":1,"question":"...","options":{{"A":"...","B":"...","C":"...","D":"..."}},"explanation":"...","correct_answer":"A"}}]}}.
Keep every ID, all four option identities and their order, and correct_answer exactly unchanged. Translate all explanations and question instructions completely. Preserve names, dates, quantities, source edition years, and negations. Do NOT correct facts or add new facts.
CRITICAL for Spanish-language grammar/spelling questions: retain Spanish example words, sentences, verb forms, spelling alternatives and fill-in blanks VERBATIM (including intentionally wrong distractors). Translate only the instruction/explanation around them. Otherwise translating the options would destroy the exercise. Geographic names may retain their Spanish spelling. Do not insert clues or explain the right answer inside the question/options. Never summarize or omit a question."""
 first=api(rules,payload)
 valid(first.get('items'),rows,locale)
 review=api(rules+f"\nYou are the second-pass translator. Compare the proposed translations below against the Spanish originals. Fix omissions, meaning/negation errors and accidental translation of Spanish exercise examples. Return the entire corrected items array in the same schema. This is a machine translation check, not independent approval of the question bank.",{'original':payload,'proposed':first['items']})
 result=valid(review.get('items'),rows,locale)
 atomic(path,result)
 with LOCK:print('QUESTIONS',locale,index,len(result),flush=True)
 return ('questions',locale,len(result),'generated')
def audio_job(locale,path):
 name,voice=LANGS[locale]
 dest=ROOT/'data/audio_scripts'/locale/path.name
 source=path.read_text(encoding='utf-8-sig')
 # Source text is fully translated, never replaced with a short summary.
 checksum=hashlib.sha256(source.encode()).hexdigest()
 meta=dest.with_suffix('.json')
 if not(dest.exists() and meta.exists() and json.loads(meta.read_text(encoding='utf-8')).get('source_hash')==checksum):
  rules=f"""Translate the WHOLE Russian audio lesson into {name}. Return JSON {{"text":"full translated lesson"}}. Preserve all sections, all substantive statements, numbers, dates and names. Do not summarize, shorten or introduce new facts. Spanish grammar examples and deliberately incorrect examples MUST remain verbatim Spanish while their surrounding explanations are translated. Render as natural narration with headings. This is a translation of an existing study lesson, not current legal advice. Retain any historical date qualifiers. Do not invent an official endorsement."""
  first=api(rules,{'text':source})['text']
  if len(first)<len(source)*.22:raise ValueError('Audio translation too short')
  # Second pass sees both source and translation, with complete output.
  translated=api(rules+'\nCheck the proposed translation against the source and correct it. Return the entire final text, never only corrections.',{'source':source,'proposed':first})['text']
  if len(translated)<len(source)*.22 or re.search('[А-Яа-яЁё]',translated):raise ValueError('Invalid translated lesson')
  dest.parent.mkdir(parents=True,exist_ok=True);dest.write_text(translated,encoding='utf-8')
  atomic(meta,{'source_hash':checksum,'translation_method':'machine_translation_with_second_pass','independent_approval':False})
 text=dest.read_text(encoding='utf-8')
 filename=path.stem+'-full.mp3'
 audio=ROOT/'frontend/public/audio'/locale/filename
 if not audio.exists():
  from audio_text import clean_for_tts
  audio.parent.mkdir(parents=True,exist_ok=True)
  tmp=audio.with_suffix('.tmp.mp3')
  async def synth():
   for attempt in range(3):
    try:
     await asyncio.wait_for(edge_tts.Communicate(clean_for_tts(text),voice=voice,rate='-5%').save(str(tmp)),timeout=240)
     if tmp.stat().st_size<10000:raise ValueError('Empty lesson audio')
     tmp.replace(audio);return
    except Exception:
     if attempt==2:raise
     await asyncio.sleep(2)
  asyncio.run(synth())
 with LOCK:print('AUDIO',locale,path.stem,audio.stat().st_size,flush=True)
 return ('audio',locale,str(audio.relative_to(ROOT)),len(text))
def main():
 db=sqlite3.connect((ACTIVE/'database/colombia_exam.db').resolve().as_uri()+'?mode=ro',uri=True);db.row_factory=sqlite3.Row
 rows=[dict(q) for q in db.execute("SELECT id,question_es,answer_a,answer_b,answer_c,answer_d,explanation_es,correct_answer FROM questions ORDER BY id")];db.close()
 jobs=[]
 with concurrent.futures.ThreadPoolExecutor(max_workers=6) as pool:
  for locale in LANGS:
   for path in sorted((ROOT/'data/audio_scripts').glob('lesson-*.txt')):jobs.append(pool.submit(audio_job,locale,path))
  for locale in LANGS:
   for i,start in enumerate(range(0,len(rows),10)):jobs.append(pool.submit(questions_job,locale,i,rows[start:start+10]))
  results=[];failures=[]
  for job in concurrent.futures.as_completed(jobs):
   try:results.append(job.result())
   except Exception as exc:
    failures.append(str(exc));print('FAILED',type(exc).__name__,str(exc),flush=True)
 catalog={'version':1,'translation_method':'machine_translation_with_second_pass','independent_approval':False,'locales':{}}
 for locale in LANGS:
  merged={}
  for path in sorted(OUT.glob(f'questions-{locale}-*.json')):merged.update(json.loads(path.read_text(encoding='utf-8')))
  if set(merged)!={str(q['id']) for q in rows}:failures.append('Incomplete '+locale)
  catalog['locales'][locale]=merged
 atomic(OUT/'generation-report.json',{'results':results,'failures':failures})
 if failures:raise SystemExit(f'{len(failures)} jobs failed; rerun resumes completed tasks')
 atomic(ROOT/'data/question-translations-en-zh.json',catalog)
 print('COMPLETE',len(rows),'questions per locale; 12 full audio lessons',flush=True)
if __name__=='__main__':main()
