"""Student-facing locale projection; pending authored translations stay private."""
import json
from typing import Literal

Locale = Literal['es', 'ru', 'en', 'de', 'fr', 'zh-Hans']
LOCALES = ['es', 'ru', 'en', 'de', 'fr', 'zh-Hans']
LOCALE_LABELS = ['Español', 'Русский', 'English', 'Deutsch', 'Français', '简体中文']
QUESTION_FIELDS = 'id,question_es,question_ru,answer_a,answer_a_ru,answer_b,answer_b_ru,answer_c,answer_c_ru,answer_d,answer_d_ru,explanation_es,explanation_ru,source_id,source_page,correct_answer'

TRANSLATION_FILE = __import__('pathlib').Path(__file__).resolve().parents[1] / 'data/question-translations.json'

def translation_source_hash(question):
    import hashlib
    fields = {key: question[key] for key in (
        'question_es','answer_a','answer_b','answer_c','answer_d','explanation_es','correct_answer')}
    return hashlib.sha256(json.dumps(fields, ensure_ascii=False, sort_keys=True).encode()).hexdigest()

from functools import lru_cache
@lru_cache(maxsize=2)
def _load_learning_translations(path, modified):
    try:
        return json.loads(__import__('pathlib').Path(path).read_text(encoding='utf-8')).get('locales', {})
    except (OSError, ValueError):
        return {}

def learning_translation(question, locale):
    try:
        catalog = _load_learning_translations(str(TRANSLATION_FILE), TRANSLATION_FILE.stat().st_mtime_ns)
        value = catalog.get(locale, {}).get(str(question['id']))
        if not value or value.get('source_hash') != translation_source_hash(question):
            return None
        if value.get('correct_answer') != question['correct_answer']:
            return None
        if set(value.get('options', {})) != set('ABCD'):
            return None
        if not all(isinstance(text, str) and text.strip() for text in [
                value.get('question'), value.get('explanation'), *value['options'].values()]):
            return None
        return value
    except (OSError, KeyError, TypeError):
        return None


def localize_questions(db, rows, locale: Locale = 'es'):
    items = [dict(row) for row in rows]
    ids = {item.get('question_id', item.get('id')) for item in items}
    ids.discard(None)
    if not ids:
        return items
    marks = ','.join('?' for _ in ids)
    base = {row['id']: dict(row) for row in db.execute(
        f'SELECT {QUESTION_FIELDS} FROM questions WHERE id IN ({marks})', tuple(ids))}
    tables = {row[0] for row in db.execute("SELECT name FROM sqlite_master WHERE type='table'")}
    sources = {row['id']: dict(row) for row in db.execute('SELECT * FROM sources')}
    authored = set()
    translations = {}
    if {'authored_imports', 'authored_localizations'} <= tables:
        authored = {row[0] for row in db.execute(
            f'SELECT question_id FROM authored_imports WHERE question_id IN ({marks})', tuple(ids))}
        for row in db.execute(f'''SELECT i.question_id,i.payload_json,l.* FROM authored_imports i
                JOIN authored_localizations l ON l.external_id=i.external_id
                WHERE i.question_id IN ({marks}) AND l.locale=? AND l.review_status='approved' ''',
                (*ids, locale)):
            translations[row['question_id']] = dict(row)
    for item in items:
        question_id = item.get('question_id', item.get('id'))
        question = base.get(question_id)
        if question is None:
            continue
        source = sources.get(question.get('source_id'), {})
        url = source.get('url', '')
        if question.get('source_page') and url.endswith('.pdf'):
            url += '#page=' + str(question['source_page'])
        item.update(source_id=question.get('source_id'), source_page=question.get('source_page'),
                    source_title=source.get('title', ''), source_url=url,
                    source_kind=source.get('document_type', ''))
        if question_id in authored:
            for field in ('question_ru', 'answer_a_ru', 'answer_b_ru', 'answer_c_ru', 'answer_d_ru', 'explanation_ru'):
                if field in item:
                    item[field] = None
        prompt = question['question_es']
        options = {key: question['answer_'+key.lower()] for key in 'ABCD'}
        explanation = question['explanation_es']
        content_locale = 'es'
        translation = translations.get(question_id)
        if locale != 'es' and translation:
            try:
                choices = json.loads(translation['options_json'])
                ids_in_order = [option['id'] for option in json.loads(translation['payload_json'])['options']]
                by_id = {option['id']: option for option in choices}
                if len(ids_in_order) == 4 and len(choices) == len(by_id) == 4 and set(by_id) == set(ids_in_order) and all(isinstance(o.get('text'), str) and o['text'].strip() for o in choices) and translation['prompt'].strip() and translation['explanation'].strip():
                    prompt = translation['prompt']
                    options = {key: by_id[ids_in_order[i]]['text'] for i, key in enumerate('ABCD')}
                    explanation = translation['explanation']
                    content_locale = locale
            except (ValueError, TypeError, AttributeError, KeyError):
                pass  # Incomplete/malformed locale records fall back as one whole question.
        elif locale == 'ru' and question_id not in authored:
            required = ['question_ru', 'answer_a_ru', 'answer_b_ru', 'answer_c_ru', 'answer_d_ru', 'explanation_ru']
            if all(isinstance(question[f], str) and question[f].strip() for f in required):
                prompt = question['question_ru']
                options = {key: question['answer_'+key.lower()+'_ru'] for key in 'ABCD'}
                explanation = question['explanation_ru']
                content_locale = 'ru'
        # Existing authored approval rules retain precedence; legacy study translations
        # are explicitly machine-translated and invalidated when their source changes.
        method = None
        if question_id not in authored and locale in ('en', 'zh-Hans', 'fr', 'de'):
            study = learning_translation(question, locale)
            if study:
                prompt, options, explanation = study['question'], study['options'], study['explanation']
                content_locale = locale
                method = study['translation_method']
        item['translation_method'] = method
        item.update(requested_locale=locale, content_locale=content_locale,
                    translation_available=content_locale == locale,
                    display_question=prompt, display_options=options)
        # Question lists must not reveal explanations/keys before an answer.
        if 'explanation_es' in item or 'explanation_ru' in item:
            item['display_explanation'] = explanation
    return items
