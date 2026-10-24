"""Read-only completeness and source-integrity check for the four translated study locales."""
import hashlib,json,sqlite3,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'backend'))
from question_locales import translation_source_hash
def main():
 db_path=Path(sys.argv[1]) if len(sys.argv)>1 else ROOT/'database/colombia_exam.db'
 db=sqlite3.connect(db_path.resolve().as_uri()+'?mode=ro',uri=True);db.row_factory=sqlite3.Row
 rows=[dict(row) for row in db.execute('SELECT * FROM questions')];db.close()
 catalog=json.loads((ROOT/'data/question-translations.json').read_text(encoding='utf-8'))
 assert catalog['independent_approval'] is False
 result={}
 for locale in ['en','zh-Hans','fr','de']:
  items=catalog['locales'][locale]
  assert set(items)=={str(q['id']) for q in rows}
  for q in rows:
   t=items[str(q['id'])]
   assert t['source_hash']==translation_source_hash(q),(locale,q['id'],'stale source')
   assert t['correct_answer']==q['correct_answer'],(locale,q['id'],'answer changed')
   assert set(t['options'])==set('ABCD')
   assert all(isinstance(v,str) and v.strip() for v in [t['question'],t['explanation'],*t['options'].values()])
   assert t['independent_approval'] is False
   if q['id'] in [18,19,352,359,367,371,373,375,377,689,691,696,698,699,700,704,705,706,716,717,718,752]:
    assert t['options']=={key:q['answer_'+key.lower()] for key in 'ABCD'},(locale,q['id'],'Spanish exercise alternatives changed')
  audio=list((ROOT/'frontend/public/audio'/locale).glob('lesson-*-full.mp3'))
  scripts=list((ROOT/'data/audio_scripts'/locale).glob('lesson-*.txt'))
  assert len(audio)==len(scripts)==6
  assert all(p.stat().st_size>10000 for p in audio)
  result[locale]={'questions':len(items),'full_audio_lessons':len(audio),'answer_keys_preserved':True,'source_hashes_valid':True}
 print(json.dumps(result,indent=2))
if __name__=='__main__':main()
