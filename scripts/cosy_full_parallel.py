from __future__ import annotations

import argparse
import asyncio
import base64
import gzip
import hashlib
import json
import re
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
URL_RE = re.compile(r'https?://\S+|www\.\S+', re.I)
CYR_RE = re.compile(r'[А-Яа-яЁё]')
LAT_RE = re.compile(r'[A-Za-zÁÉÍÓÚÜÑáéíóúüñ]')
UNDERSCORE_RE = re.compile(r'_ {0,1}_|_{3,}')

PAYLOADS = {
    '01_geography': {
        'files': ['pdf_payload_v2/01_geography.gz.b64'],
        'b64_len': 13148,
        'sha256': '841593971c089fe82b6e2c4767f46fef9eddf143ed092c2020c0a985857c35f1',
        'chars': 19080,
    },
    '02_history': {
        'glob': 'pdf_payload_v2/02_history.gz.b64.part*',
        'b64_len': 42064,
        'sha256': '4d6a22bb423ade23bfd2b525afd77affc533a0b95d2da4154c5befb72d06fe94',
        'chars': 63218,
    },
    '03_constitution': {
        'glob': 'cosy_clean_payload4k/03_constitution.part*.txt',
        'b64_len': 27792,
        'sha256': '59f4a758edcc40cf31e6f4c3915589c0cb1eaa0bfc70fc1f6415341c75c918da',
        'chars': 49577,
    },
    '04_spanish_bilingual': {
        'glob': 'cosy_clean_payload4k/04_spanish_bilingual.part*.txt',
        'b64_len': 39336,
        'sha256': '0fe8b42d05a422254989fa405e267cc7cfa4f13d78d5d044b8ea405a721d5076',
        'chars': 64391,
    },
}


def clean_b64(s: str) -> str:
    return ''.join(s.split())


def load_payload(spec: dict) -> str:
    if 'files' in spec:
        paths = [ROOT / x for x in spec['files']]
    else:
        paths = sorted(ROOT.glob(spec['glob']))
    if not paths:
        raise FileNotFoundError(spec)
    payload = ''.join(clean_b64(p.read_text(encoding='ascii')) for p in paths)
    if len(payload) != spec['b64_len']:
        raise ValueError(f'payload length {len(payload)} != {spec["b64_len"]}: {[str(p) for p in paths]}')
    digest = hashlib.sha256(payload.encode('ascii')).hexdigest()
    if digest != spec['sha256']:
        raise ValueError(f'payload sha256 {digest} != {spec["sha256"]}: {[str(p) for p in paths]}')
    text = gzip.decompress(base64.b64decode(payload, validate=True)).decode('utf-8')
    if len(text) != spec['chars']:
        raise ValueError(f'text chars {len(text)} != {spec["chars"]}')
    return text


def normalize_line(line: str) -> str:
    line = URL_RE.sub('', line)
    line = line.replace('•', ' ').replace('·', ' ')
    line = UNDERSCORE_RE.sub(' ', line)
    line = re.sub(r'\s+', ' ', line).strip(' \t-–—')
    if not line:
        return ''
    if re.fullmatch(r'(?:Аудио(?:\s+[^:]*)?|Аудиозапись(?:\s+[^:]*)?):?', line, re.I):
        return ''
    return line


def counts(s: str) -> tuple[int, int]:
    return len(CYR_RE.findall(s)), len(LAT_RE.findall(s))


def classify_lang(s: str, default: str = 'ru') -> str:
    cy, la = counts(s)
    if cy == 0 and la >= 2:
        return 'es'
    if ('¿' in s or '¡' in s) and la >= 3:
        return 'es'
    if la >= max(5, cy * 1.6):
        return 'es'
    return default


def split_parenthetical_translation(part: str):
    m = re.match(r'^(.*[A-Za-zÁÉÍÓÚÜÑáéíóúüñ])\s*\(([^()]*)\)\.?$', part)
    if m and CYR_RE.search(m.group(2)) and len(LAT_RE.findall(m.group(1))) >= 2:
        return [('es', m.group(1).strip()), ('ru', m.group(2).strip())]
    return None


def split_mixed_line(line: str) -> list[tuple[str, str]]:
    line = normalize_line(line)
    if not line:
        return []
    if re.search(r'(?:\b[A-ZÑ]\s*-\s*){2,}[A-ZÑ]\b', line):
        m = re.search(r'\s*-\s*[«“]([^»”]*[А-Яа-яЁё][^»”]*)[»”]\.?$', line)
        if m:
            left = line[:m.start()].strip()
            right = m.group(1).strip()
            return [(classify_lang(left), left), ('ru', right)]
    parts = re.split(r'\s+(?:—|–|→|=>|->)\s+|\s+-\s+(?=[«“¿¡A-Za-zÁÉÍÓÚÜÑА-ЯЁ])', line)
    out: list[tuple[str, str]] = []
    for part in parts:
        part = part.strip(' «»“”')
        if not part:
            continue
        par = split_parenthetical_translation(part)
        if par:
            out.extend(par)
            continue
        cy, la = counts(part)
        if ':' in part and cy and la:
            a, b = part.split(':', 1)
            ca, _ = counts(a)
            cb, lb = counts(b)
            if ca >= 2 and lb >= 3 and cb <= max(1, lb // 7):
                if a.strip():
                    out.append(('ru', a.strip() + '.'))
                if b.strip():
                    out.append(('es', b.strip()))
                continue
        m = re.search(r'(?<=[A-Za-zÁÉÍÓÚÜÑáéíóúüñ.!?])\s+(?=[А-ЯЁ])', part)
        if m and cy >= 2 and la >= 2:
            a, b = part[:m.start()].strip(), part[m.end():].strip()
            if classify_lang(a, 'es') == 'es':
                out.extend([('es', a), ('ru', b)])
                continue
        m = re.search(r'(?<=[А-Яа-яЁё.!?])\s+(?=[¿¡A-ZÁÉÍÓÚÜÑ])', part)
        if m and cy >= 2 and la >= 2:
            a, b = part[:m.start()].strip(), part[m.end():].strip()
            if classify_lang(b, 'es') == 'es':
                out.extend([('ru', a), ('es', b)])
                continue
        out.append((classify_lang(part), part))
    return [(lang, text) for lang, text in out if normalize_line(text)]


def sentence_units(text: str) -> list[str]:
    lines = [normalize_line(x) for x in text.splitlines()]
    text = '\n'.join(x for x in lines if x)
    units = re.split(r'(?<=[.!?…])\s+|\n+', text)
    return [normalize_line(x) for x in units if normalize_line(x)]


def pack_units(units: list[str], max_chars: int = 1050) -> list[str]:
    out, cur = [], ''
    for unit in units:
        if not unit:
            continue
        while len(unit) > max_chars:
            cut = unit.rfind(' ', 0, max_chars)
            if cut < max_chars * 0.55:
                cut = max_chars
            first, unit = unit[:cut].strip(), unit[cut:].strip()
            if cur:
                out.append(cur)
                cur = ''
            if first:
                out.append(first)
        if not cur:
            cur = unit
        elif len(cur) + 1 + len(unit) <= max_chars:
            cur += ' ' + unit
        else:
            out.append(cur)
            cur = unit
    if cur:
        out.append(cur)
    return out


def make_segments() -> list[dict]:
    texts = {name: load_payload(spec) for name, spec in PAYLOADS.items()}
    segs: list[dict] = []
    chapter_titles = {
        '01_geography': 'География Колумбии',
        '02_history': 'Отечественная история Колумбии',
        '03_constitution': 'Политическая конституция Колумбии',
        '04_spanish_bilingual': 'Испанский язык',
    }
    for chapter in ['01_geography', '02_history', '03_constitution']:
        chunks = pack_units(sentence_units(texts[chapter]), 1050)
        for txt in chunks:
            segs.append({'chapter': chapter, 'chapter_title': chapter_titles[chapter], 'lang': 'ru', 'text': txt, 'pause_after': 0.16})
        if segs:
            segs[-1]['pause_after'] = 1.5

    chapter = '04_spanish_bilingual'
    frags: list[tuple[str, str]] = []
    for line in texts[chapter].splitlines():
        frags.extend(split_mixed_line(line))
    merged: list[tuple[str, str]] = []
    max_lang = {'ru': 950, 'es': 700}
    for lang, raw in frags:
        txt = normalize_line(raw)
        if not txt:
            continue
        subunits = re.split(r'(?<=[.!?…])\s+', txt)
        for unit in subunits:
            unit = normalize_line(unit)
            if not unit:
                continue
            if merged and merged[-1][0] == lang and len(merged[-1][1]) + len(unit) + 1 <= max_lang[lang]:
                merged[-1] = (lang, merged[-1][1] + ' ' + unit)
            else:
                for chunk in pack_units([unit], max_lang[lang]):
                    merged.append((lang, chunk))
    for lang, txt in merged:
        segs.append({'chapter': chapter, 'chapter_title': chapter_titles[chapter], 'lang': lang, 'text': txt, 'pause_after': 0.18})
    if segs:
        segs[-1]['pause_after'] = 0.0
    for i, seg in enumerate(segs):
        seg['index'] = i
    return segs


def assign_shards(segs: list[dict], shards: int):
    total = sum(max(1, len(s['text'])) for s in segs)
    target = total / shards
    shard = 0
    acc = 0
    next_cut = target
    for seg in segs:
        if shard < shards - 1 and acc >= next_cut:
            shard += 1
            next_cut = target * (shard + 1)
        seg['shard'] = shard
        acc += max(1, len(seg['text']))
    return total


def prepare(out: Path, shards: int):
    segs = make_segments()
    total = assign_shards(segs, shards)
    stats = {'total_segments': len(segs), 'total_chars': total, 'shards': shards, 'langs': {}, 'chapters': {}}
    for seg in segs:
        stats['langs'][seg['lang']] = stats['langs'].get(seg['lang'], 0) + len(seg['text'])
        stats['chapters'][seg['chapter']] = stats['chapters'].get(seg['chapter'], 0) + len(seg['text'])
    shard_stats = []
    for i in range(shards):
        ss = [s for s in segs if s['shard'] == i]
        shard_stats.append({'shard': i, 'segments': len(ss), 'chars': sum(len(s['text']) for s in ss), 'first': ss[0]['index'] if ss else None, 'last': ss[-1]['index'] if ss else None})
    stats['shard_stats'] = shard_stats
    if stats['langs'].get('ru', 0) < 150000:
        raise RuntimeError(stats)
    if stats['langs'].get('es', 0) < 5000:
        raise RuntimeError('Spanish text unexpectedly small: ' + json.dumps(stats, ensure_ascii=False))
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps({'stats': stats, 'segments': segs}, ensure_ascii=False), encoding='utf-8')
    print(json.dumps(stats, ensure_ascii=False, indent=2))


def make_refs(work: Path):
    import edge_tts

    work.mkdir(parents=True, exist_ok=True)
    ru_prompt = 'Добрый день. Это спокойный мужской голос для учебной аудиокниги о Колумбии.'
    es_prompt = 'Buenos días. Esta es una voz masculina tranquila para un audiolibro educativo sobre Colombia.'

    async def go():
        await edge_tts.Communicate(ru_prompt, 'ru-RU-DmitryNeural', rate='-8%').save(str(work / 'ru_ref.mp3'))
        await edge_tts.Communicate(es_prompt, 'es-CO-GonzaloNeural', rate='-8%').save(str(work / 'es_ref.mp3'))

    asyncio.run(go())
    for lang in ['ru', 'es']:
        subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-i', str(work / f'{lang}_ref.mp3'), '-ar', '24000', '-ac', '1', '-c:a', 'pcm_s16le', str(work / f'{lang}_ref.wav')], check=True)
    return ru_prompt, es_prompt


def render(plan: Path, shard: int, out: Path, model_dir: Path):
    data = json.loads(plan.read_text(encoding='utf-8'))
    segs = [s for s in data['segments'] if s['shard'] == shard]
    if not segs:
        raise RuntimeError(f'No segments for shard {shard}')
    work = out.parent / 'refs'
    ru_prompt, es_prompt = make_refs(work)
    sys.path.insert(0, '/tmp/CosyVoice')
    sys.path.append('/tmp/CosyVoice/third_party/Matcha-TTS')
    import torch
    import torchaudio
    from cosyvoice.cli.cosyvoice import AutoModel

    t0 = time.time()
    model = AutoModel(model_dir=str(model_dir), load_trt=False, load_vllm=False, fp16=False)
    print('MODEL_LOAD_SEC', time.time() - t0, flush=True)
    prefix = 'You are a helpful assistant.<|endofprompt|>'
    ru_full = prefix + ru_prompt
    es_full = prefix + es_prompt
    model.add_zero_shot_spk(ru_full, str(work / 'ru_ref.wav'), 'ru_book')
    model.add_zero_shot_spk(es_full, str(work / 'es_ref.wav'), 'es_book')
    pieces = []
    silence_cache = {}

    def silence(sec: float):
        n = int(round(sec * model.sample_rate))
        if n not in silence_cache:
            silence_cache[n] = torch.zeros((1, n), dtype=torch.float32)
        return silence_cache[n]

    t1 = time.time()
    for k, seg in enumerate(segs, 1):
        lang = seg['lang']
        txt = seg['text']
        full = ru_full if lang == 'ru' else es_full
        ref = str(work / f'{lang}_ref.wav')
        sid = 'ru_book' if lang == 'ru' else 'es_book'
        outs = []
        for item in model.inference_zero_shot(txt, full, ref, zero_shot_spk_id=sid, stream=False, speed=0.92):
            outs.append(item['tts_speech'].cpu())
        if not outs:
            raise RuntimeError(f'No audio for segment {seg["index"]}')
        audio = torch.cat(outs, dim=1)
        pieces.append(audio)
        if seg.get('pause_after', 0) > 0:
            pieces.append(silence(float(seg['pause_after'])))
        print(f'SHARD {shard} SEG {k}/{len(segs)} idx={seg["index"]} lang={lang} chars={len(txt)} audio_sec={audio.shape[1] / model.sample_rate:.2f}', flush=True)
    audio = torch.cat(pieces, dim=1)
    out.parent.mkdir(parents=True, exist_ok=True)
    torchaudio.save(str(out), audio, model.sample_rate, encoding='PCM_S', bits_per_sample=16)
    elapsed = time.time() - t1
    audio_sec = audio.shape[1] / model.sample_rate
    print('SHARD_DONE', shard, 'segments', len(segs), 'audio_sec', audio_sec, 'elapsed_sec', elapsed, 'rtf', elapsed / audio_sec, 'bytes', out.stat().st_size, flush=True)


def main():
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest='cmd', required=True)
    prep = sub.add_parser('prepare')
    prep.add_argument('--out', required=True)
    prep.add_argument('--shards', type=int, default=20)
    rnd = sub.add_parser('render')
    rnd.add_argument('--plan', required=True)
    rnd.add_argument('--shard', type=int, required=True)
    rnd.add_argument('--out', required=True)
    rnd.add_argument('--model-dir', required=True)
    args = parser.parse_args()
    if args.cmd == 'prepare':
        prepare(Path(args.out), args.shards)
    else:
        render(Path(args.plan), args.shard, Path(args.out), Path(args.model_dir))


if __name__ == '__main__':
    main()
