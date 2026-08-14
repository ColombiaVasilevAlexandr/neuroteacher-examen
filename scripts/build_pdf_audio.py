from pathlib import Path
import asyncio
import re
import subprocess
import edge_tts
import imageio_ffmpeg

ROOT = Path('/tmp/pdf_audio_texts')
WORK = Path('/tmp/pdf_native_audio')
SEG = WORK / 'segments'
SEG.mkdir(parents=True, exist_ok=True)
OUT = Path('uchebnoe_posobie_kolumbiya_RU_ES_native_full.mp3')

RU = 'ru-RU-DmitryNeural'
ES = 'es-CO-GonzaloNeural'
RATE = '-8%'
MAX = 1450
CONCURRENCY = 6

CYR = re.compile(r'[А-Яа-яЁё]')
LAT = re.compile(r'[A-Za-zÁÉÍÓÚÜÑáéíóúüñ]')
URL = re.compile(r'https?://\S+|www\.\S+', re.I)


def normalize(s):
    s = URL.sub('', s)
    s = s.replace('•', ' ').replace('·', ' ')
    return re.sub(r'\s+', ' ', s).strip()


def split_long(text, max_chars=MAX):
    text = normalize(text)
    if not text:
        return []
    sentences = re.split(r'(?<=[.!?…])\s+|(?<=:)\s+(?=[А-ЯA-ZÁÉÍÓÚÜÑ¿¡])', text)
    chunks, cur = [], ''
    for sent in sentences:
        sent = sent.strip()
        if not sent:
            continue
        if len(sent) > max_chars:
            if cur:
                chunks.append(cur)
                cur = ''
            while len(sent) > max_chars:
                cut = sent.rfind(' ', 0, max_chars)
                if cut < 350:
                    cut = max_chars
                chunks.append(sent[:cut].strip())
                sent = sent[cut:].strip()
            if sent:
                cur = sent
        elif not cur:
            cur = sent
        elif len(cur) + len(sent) + 1 <= max_chars:
            cur += ' ' + sent
        else:
            chunks.append(cur)
            cur = sent
    if cur:
        chunks.append(cur)
    return chunks


def counts(s):
    return len(CYR.findall(s)), len(LAT.findall(s))


def classify(s, default='ru'):
    cy, la = counts(s)
    if cy == 0 and la >= 2:
        return 'es'
    if la == 0 and cy >= 1:
        return 'ru'
    if ('¿' in s or '¡' in s) and la >= 3:
        return 'es'
    if cy >= max(4, la * 0.45):
        return 'ru'
    if la >= max(5, cy * 2.0):
        return 'es'
    return default


def split_bilingual(line, default='ru'):
    line = normalize(line)
    if not line:
        return []
    parts = re.split(r'\s+(?:—|–|→|=>|->)\s+|\s+-\s+(?=[«“¿¡A-Za-zÁÉÍÓÚÜÑА-ЯЁ])', line)
    out = []
    for part in parts:
        part = part.strip()
        if not part:
            continue
        cy, la = counts(part)
        if ':' in part and cy and la:
            a, b = part.split(':', 1)
            ca, _ = counts(a)
            cb, lab = counts(b)
            if ca >= 3 and lab >= 4 and cb <= max(1, lab // 8):
                out.append(('ru', a.strip() + '.'))
                out.append(('es', b.strip()))
                continue
        m = re.search(r'(?<=[A-Za-zÁÉÍÓÚÜÑáéíóúüñ.!?])\s+(?=[А-ЯЁ])', part)
        if m and cy >= 4 and la >= 4:
            a, b = part[:m.start()].strip(), part[m.end():].strip()
            if classify(a, 'es') == 'es' and classify(b, 'ru') == 'ru':
                out.extend([('es', a), ('ru', b)])
                continue
        m = re.search(r'(?<=[А-Яа-яЁё.!?])\s+(?=[¿¡A-ZÁÉÍÓÚÜÑ])', part)
        if m and cy >= 4 and la >= 4:
            a, b = part[:m.start()].strip(), part[m.end():].strip()
            if classify(a, 'ru') == 'ru' and classify(b, 'es') == 'es':
                out.extend([('ru', a), ('es', b)])
                continue
        out.append((classify(part, default), part))
    return out


segments = []
chapter_marks = []
for chapter in ['01_geography', '02_history', '03_constitution']:
    chapter_marks.append(len(segments))
    text = ROOT.joinpath(chapter + '.txt').read_text(encoding='utf-8')
    for chunk in split_long(text):
        segments.append(('ru', chunk, chapter))

chapter = '04_spanish_bilingual'
chapter_marks.append(len(segments))
text = ROOT.joinpath(chapter + '.txt').read_text(encoding='utf-8')
small = []
default = 'ru'
for raw in text.splitlines():
    line = raw.strip()
    if not line:
        continue
    for lang, piece in split_bilingual(line, default):
        for chunk in split_long(piece, max_chars=900 if lang == 'es' else MAX):
            small.append((lang, chunk))
            default = lang
merged = []
for lang, text in small:
    if merged and merged[-1][0] == lang and len(merged[-1][1]) + len(text) + 1 <= MAX:
        merged[-1] = (lang, merged[-1][1] + ' ' + text)
    else:
        merged.append((lang, text))
for lang, text in merged:
    segments.append((lang, text, chapter))

ru_chars = sum(len(t) for l, t, _ in segments if l == 'ru')
es_chars = sum(len(t) for l, t, _ in segments if l == 'es')
print('segments=', len(segments), 'ru_chars=', ru_chars, 'es_chars=', es_chars, 'chapter_starts=', chapter_marks, flush=True)
if ru_chars < 150000:
    raise SystemExit(f'Russian text unexpectedly short: {ru_chars}')
if es_chars < 1200:
    raise SystemExit(f'Spanish examples unexpectedly short: {es_chars}')

sem = asyncio.Semaphore(CONCURRENCY)


async def render(i, lang, text, chapter):
    voice = RU if lang == 'ru' else ES
    target = SEG / f'{i:04d}_{chapter}_{lang}.mp3'
    async with sem:
        last = None
        for attempt in range(7):
            try:
                await edge_tts.Communicate(text, voice, rate=RATE).save(str(target))
                if target.exists() and target.stat().st_size > 800:
                    return target
            except Exception as exc:
                last = exc
                await asyncio.sleep(min(2 * (attempt + 1), 12))
        raise RuntimeError(f'render failed segment={i} lang={lang}: {last}')


async def render_all():
    tasks = [asyncio.create_task(render(i, l, t, ch)) for i, (l, t, ch) in enumerate(segments, 1)]
    done = 0
    for fut in asyncio.as_completed(tasks):
        await fut
        done += 1
        if done % 20 == 0 or done == len(tasks):
            print('rendered', done, '/', len(tasks), flush=True)
    return [SEG / f'{i:04d}_{ch}_{l}.mp3' for i, (l, t, ch) in enumerate(segments, 1)]


files = asyncio.run(render_all())
ffmpeg = imageio_ffmpeg.get_ffmpeg_exe()
silence_short = WORK / 'silence_short.mp3'
silence_chapter = WORK / 'silence_chapter.mp3'
for path, seconds in [(silence_short, 0.16), (silence_chapter, 1.6)]:
    subprocess.run([ffmpeg, '-y', '-f', 'lavfi', '-i', 'anullsrc=r=24000:cl=mono', '-t', str(seconds), '-c:a', 'libmp3lame', '-b:a', '48k', str(path)], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

chapter_start_set = set(chapter_marks[1:])
concat = WORK / 'concat.txt'
with concat.open('w', encoding='utf-8') as f:
    for idx, p in enumerate(files):
        f.write("file '" + str(p.resolve()).replace("'", "'\\''") + "'\n")
        if idx + 1 < len(files):
            pause = silence_chapter if (idx + 1) in chapter_start_set else silence_short
            f.write("file '" + str(pause.resolve()) + "'\n")

subprocess.run([ffmpeg, '-y', '-f', 'concat', '-safe', '0', '-i', str(concat), '-ar', '24000', '-ac', '1', '-c:a', 'libmp3lame', '-b:a', '64k', '-metadata', 'title=Учебное пособие по гражданству Колумбии', '-metadata', 'artist=Russian + Colombian Spanish neural narration', str(OUT)], check=True)
if not OUT.exists() or OUT.stat().st_size < 20_000_000:
    raise SystemExit(f'Final MP3 missing or too small: {OUT.stat().st_size if OUT.exists() else 0}')
print('FINAL', OUT, 'bytes=', OUT.stat().st_size, flush=True)
