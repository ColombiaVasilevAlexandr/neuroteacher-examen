"""Prepare a history-free, prefixed static/API release off the production host."""
import argparse,hashlib,json,re,shutil,sqlite3,subprocess,tarfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
PROGRESS=['attempts','exam_sessions','bookmarks','review_queue','study_settings','exam_runs','exam_run_questions']
def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--database',type=Path,required=True)
    parser.add_argument('--output-root',type=Path,default=ROOT/'data/imports')
    parser.add_argument('--vendor-root',type=Path,default=ROOT/'backend/.venv/Lib/site-packages')
    args=parser.parse_args()
    sha=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()
    stage=args.output_root/('web-release-'+sha[:12])
    if stage.exists():raise SystemExit('Release directory already exists; preserve it and choose a new source commit')
    (stage/'backend').mkdir(parents=True)
    for p in (ROOT/'backend').glob('*.py'):shutil.copy2(p,stage/'backend'/p.name)
    (stage/'data').mkdir()
    shutil.copy2(ROOT/'data/question-translations.json',stage/'data/question-translations.json')
    public=ROOT/'frontend/public';target=stage/'frontend/public';target.mkdir(parents=True)
    names=[p.name for p in public.iterdir() if p.is_dir() or p.suffix.lower() in ('.html','.js','.css','.pdf','.svg','.png','.jpg','.jpeg')]
    quotes=chr(34)+chr(39)+chr(96)
    pattern=re.compile('(?<=['+quotes+'(])/('+'|'.join(re.escape(n) for n in sorted(names,key=len,reverse=True))+')(?=[/?#'+quotes+')]|$)')
    for source in public.rglob('*'):
        if not source.is_file() or any(part.startswith('.') for part in source.relative_to(public).parts):continue
        if source.suffix.lower() not in ('.html','.js','.css','.pdf','.svg','.png','.jpg','.jpeg','.mp3'):continue
        if '.backup-' in source.name or '.tmp.' in source.name:continue
        dest=target/source.relative_to(public);dest.parent.mkdir(parents=True,exist_ok=True)
        if source.suffix.lower() in ('.html','.js','.css'):
            text=pattern.sub(r'/colombia/\1',source.read_text(encoding='utf-8'))
            if source.name=='index.html':
                marker='<script src='+chr(34)+'/colombia/runtime-config.js'
                position=text.index(marker)
                text=text[:position]+'<script>window.COLOMBIA_API_BASE=window.location.origin+'+chr(39)+'/colombia/api'+chr(39)+';</script>\n    '+text[position:]
                marker_end=text.index('</script>',text.index(marker))+len('</script>')
                text=text[:marker_end]+'\n    <script src='+chr(34)+'/colombia/web-session.js'+chr(34)+'></script>'+text[marker_end:]
            dest.write_text(text,encoding='utf-8')
        else:shutil.copy2(source,dest)
    (stage/'database').mkdir()
    src=sqlite3.connect(args.database.resolve().as_uri()+'?mode=ro',uri=True)
    db=sqlite3.connect(stage/'database/colombia_exam.db');src.backup(db);src.close()
    db.execute('PRAGMA secure_delete=ON')
    for table in PROGRESS:db.execute('DELETE FROM '+table)
    db.execute("UPDATE sources SET url='/colombia'||url WHERE url LIKE '/%'")
    db.commit();db.execute('VACUUM')
    assert all(db.execute('SELECT count(*) FROM '+table).fetchone()[0]==0 for table in PROGRESS)
    assert db.execute('PRAGMA integrity_check').fetchone()[0]=='ok'
    count=db.execute('SELECT count(*) FROM questions').fetchone()[0];db.close()
    vendor=stage/'deps';vendor.mkdir()
    for prefix in ['edge_tts','dotenv','python_dotenv','pypdf']:
        for source in args.vendor_root.glob(prefix+'*'):
            if source.is_dir():shutil.copytree(source,vendor/source.name,ignore=shutil.ignore_patterns('__pycache__','*.pyc'))
    for name,version in [('edge_tts','7.3.1'),('python_dotenv','1.2.2'),('pypdf','6.15.0')]:
        wheel=vendor/(name+'-'+version+'.dist-info')/'WHEEL'
        assert 'py3-none-any' in wheel.read_text(encoding='utf-8'),name
    manifest={'source_sha':sha,'questions':count,'private_progress_rows':0,'base_path':'/colombia/','files':{}}
    for p in sorted(stage.rglob('*')):
        if p.is_file():manifest['files'][p.relative_to(stage).as_posix()]=hashlib.sha256(p.read_bytes()).hexdigest()
    (stage/'release.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8')
    archive=stage.with_suffix('.tar')
    with tarfile.open(archive,'w') as tar:tar.add(stage,arcname='.')
    print(json.dumps({'stage':str(stage),'archive':str(archive),'archive_bytes':archive.stat().st_size,'sha256':hashlib.sha256(archive.read_bytes()).hexdigest(),'questions':count,'private_progress_rows':0}))
if __name__=='__main__':main()
