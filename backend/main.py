from contextlib import asynccontextmanager
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
import sqlite3
import os
import json
import re
import hashlib
import secrets
import math
import edge_tts
from urllib import request as urlrequest
from urllib.error import HTTPError, URLError
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
from typing import Literal
from pydantic import BaseModel, ConfigDict, Field, field_validator
from question_locales import Locale, LOCALES, LOCALE_LABELS, localize_questions

ROOT = Path(__file__).resolve().parent.parent
load_dotenv(ROOT / ".env")
load_dotenv(Path(__file__).resolve().parent / ".env")
DB_PATH = ROOT / "database" / "colombia_exam.db"
SOURCE_URL = "https://www.cancilleria.gov.co/sites/default/files/FOTOS2025/Gu%C3%ADa%20de%20estudio_ajustada.pdf"

# Training seed: these questions require editorial verification against the PDF before an exam mode may use them.
QUESTIONS = [
    ("¿Cuál es la capital de Colombia?", "Bogotá", "Medellín", "Cali", "Cartagena", "A", "Geografía", "La capital de Colombia es Bogotá."),
    ("¿Qué océanos bañan las costas de Colombia?", "Atlántico y Pacífico", "Índico y Atlántico", "Pacífico y Ártico", "Solo Atlántico", "A", "Geografía", "Colombia tiene costas sobre el mar Caribe (Atlántico) y el océano Pacífico."),
    ("¿Cuál es el idioma oficial de Colombia?", "El castellano", "El inglés", "El portugués", "El francés", "A", "Castellano", "El castellano es el idioma oficial del país."),
    ("¿Cuál es la moneda oficial de Colombia?", "Peso colombiano", "Dólar colombiano", "Euro", "Sol colombiano", "A", "Cultura", "La moneda de Colombia es el peso colombiano."),
    ("¿Qué ciudad es conocida como la Ciudad de la Eterna Primavera?", "Medellín", "Bogotá", "Pasto", "Santa Marta", "A", "Geografía", "Medellín es conocida por este apodo."),
    ("¿Cuál es el río más importante de Colombia?", "Magdalena", "Amazonas", "Orinoco", "Cauca", "A", "Geografía", "El río Magdalena articula históricamente gran parte del país."),
    ("¿En qué fecha se celebra la independencia de Colombia?", "20 de julio", "7 de agosto", "12 de octubre", "11 de noviembre", "A", "Historia", "El 20 de julio se conmemora el inicio de la independencia en 1810."),
    ("¿Quién escribió Cien años de soledad?", "Gabriel García Márquez", "Jorge Isaacs", "Álvaro Mutis", "José Asunción Silva", "A", "Cultura", "Gabriel García Márquez escribió esta novela."),
    ("¿Cuál es la flor nacional de Colombia?", "La orquídea", "La rosa", "El girasol", "El clavel", "A", "Cultura", "La orquídea Cattleya trianae es la flor nacional."),
    ("¿Qué colores tiene la bandera de Colombia?", "Amarillo, azul y rojo", "Verde, blanco y rojo", "Azul y blanco", "Rojo y amarillo", "A", "Cultura", "La bandera está compuesta por amarillo, azul y rojo."),
    ("¿Qué requisito migratorio es indispensable para iniciar la naturalización?", "Visa de Residente vigente", "Visa de turismo", "Pasaporte vencido", "Visa de estudiante vencida", "A", "Naturalización", "La página oficial exige domicilio en Colombia y Visa de Residente vigente."),
    ("¿Cuántos años continuos de permanencia se exigen normalmente desde la Visa de Residente?", "Cinco años", "Un año", "Dos años", "Diez años", "A", "Naturalización", "La información oficial indica cinco años continuos en el caso general."),
    ("¿A cuánto puede reducirse el tiempo si la persona está casada con un colombiano?", "Dos años", "Un año", "Tres años", "No se reduce", "A", "Naturalización", "Puede reducirse a dos años en los casos señalados por Cancillería."),
    ("¿Qué documento de identidad vigente debe presentarse en el trámite?", "Cédula de extranjería", "Licencia de conducir", "Carné estudiantil", "Tarjeta bancaria", "A", "Naturalización", "Se requiere copia de la cédula de extranjería vigente."),
    ("Los documentos en otro idioma deben presentarse con…", "Traducción oficial al castellano", "Una traducción informal", "Solo una foto", "Ningún requisito", "A", "Naturalización", "La autoridad exige la traducción oficial al español."),
    ("¿Dónde se carga la documentación del trámite?", "En SITAC", "En una red social", "Por correo sin solicitud", "En un cajero", "A", "Naturalización", "La información oficial se refiere al trámite virtual en SITAC."),
    ("¿Qué estudia la geografía?", "El espacio geográfico", "Solo la gramática", "Los números", "La música", "A", "Geografía", "La geografía estudia el espacio geográfico y sus relaciones."),
    ("Completa: Yo ___ en Colombia.", "vivo", "vive", "viven", "vivimos", "A", "Castellano", "Con 'yo' se usa la forma 'vivo'."),
    ("¿Cuál es una forma correcta de saludo formal?", "Mucho gusto", "Yo gusto mucho", "Muchos gustas", "Gustar usted", "A", "Castellano", "'Mucho gusto' es una expresión habitual de cortesía."),
    ("¿Qué área aparece entre los conocimientos evaluados en el examen?", "Constitución Política", "Programación", "Física cuántica", "Diseño industrial", "A", "Naturalización", "Cancillería menciona Constitución, historia, geografía, cultura y castellano."),
]

# Keep the existing admission policy shared by every student question route.
QUESTION_ADMISSION_SQL = "status IN ('reviewed','verified','ai_reviewed')"

def admitted_questions(alias: str = "") -> str:
    return (alias + "." if alias else "") + QUESTION_ADMISSION_SQL

def conn():
    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row
    return connection

def initialize():
    DB_PATH.parent.mkdir(exist_ok=True)
    with conn() as db:
        db.executescript('''
        CREATE TABLE IF NOT EXISTS sources (id INTEGER PRIMARY KEY, title TEXT NOT NULL, url TEXT NOT NULL, document_type TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS questions (id INTEGER PRIMARY KEY, question_es TEXT, answer_a TEXT, answer_b TEXT, answer_c TEXT, answer_d TEXT, correct_answer TEXT, topic TEXT, explanation_es TEXT, status TEXT NOT NULL, source_id INTEGER, source_page INTEGER, FOREIGN KEY(source_id) REFERENCES sources(id));
        CREATE TABLE IF NOT EXISTS attempts (id INTEGER PRIMARY KEY, question_id INTEGER, answer TEXT, correct INTEGER, created_at TEXT DEFAULT CURRENT_TIMESTAMP);
        CREATE TABLE IF NOT EXISTS material_pages (id INTEGER PRIMARY KEY, source_id INTEGER NOT NULL, page_number INTEGER NOT NULL, text TEXT NOT NULL, FOREIGN KEY(source_id) REFERENCES sources(id));
        CREATE TABLE IF NOT EXISTS material_chapters (id INTEGER PRIMARY KEY, source_id INTEGER NOT NULL, title TEXT NOT NULL, page_number INTEGER NOT NULL, FOREIGN KEY(source_id) REFERENCES sources(id));
        CREATE TABLE IF NOT EXISTS exam_sessions (id INTEGER PRIMARY KEY, total_questions INTEGER NOT NULL, correct_answers INTEGER NOT NULL, created_at TEXT DEFAULT CURRENT_TIMESTAMP);
        CREATE TABLE IF NOT EXISTS bookmarks (question_id INTEGER PRIMARY KEY, created_at TEXT DEFAULT CURRENT_TIMESTAMP, FOREIGN KEY(question_id) REFERENCES questions(id));
        CREATE TABLE IF NOT EXISTS review_queue (question_id INTEGER PRIMARY KEY, due_at TEXT NOT NULL, step INTEGER NOT NULL DEFAULT 0, FOREIGN KEY(question_id) REFERENCES questions(id));
        CREATE TABLE IF NOT EXISTS study_settings (key TEXT PRIMARY KEY, value TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS exam_runs (
            token TEXT PRIMARY KEY, exam_format TEXT NOT NULL, started_at TEXT NOT NULL,
            submission_sha256 TEXT, result_json TEXT);
        CREATE TABLE IF NOT EXISTS exam_run_questions (
            run_token TEXT NOT NULL, question_id INTEGER NOT NULL, position INTEGER NOT NULL,
            correct_answer TEXT NOT NULL, question_json TEXT NOT NULL,
            PRIMARY KEY(run_token,question_id), UNIQUE(run_token,position),
            FOREIGN KEY(run_token) REFERENCES exam_runs(token));
        ''')
        try:
            db.execute("ALTER TABLE attempts ADD COLUMN response_time_seconds REAL")
        except sqlite3.OperationalError:
            pass
        for column in ("question_ru", "answer_a_ru", "answer_b_ru", "answer_c_ru", "answer_d_ru", "explanation_ru", "source_quote"):
            try:
                db.execute(f"ALTER TABLE questions ADD COLUMN {column} TEXT")
            except sqlite3.OperationalError:
                pass
        # Bring existing learning history into the review system once, without
        # overwriting dates that have already been scheduled by newer attempts.
        db.execute("""
            INSERT OR IGNORE INTO review_queue(question_id,due_at,step)
            SELECT question_id, date('now','localtime'), 0
            FROM attempts WHERE correct=0 GROUP BY question_id
        """)
        db.execute("""
            INSERT OR IGNORE INTO review_queue(question_id,due_at,step)
            SELECT question_id, date('now','localtime'), 0 FROM bookmarks
        """)
        db.execute("INSERT OR IGNORE INTO sources(id,title,url,document_type) VALUES(1,?,?,?)", ("Colombia, nuestra casa", SOURCE_URL, "official_study_guide"))
        if db.execute("SELECT COUNT(*) FROM questions").fetchone()[0] == 0:
            db.executemany("INSERT INTO questions(question_es,answer_a,answer_b,answer_c,answer_d,correct_answer,topic,explanation_es,status,source_id) VALUES(?,?,?,?,?,?,?,?,?,1)", [(*q, "reviewed") for q in QUESTIONS])

@asynccontextmanager
async def lifespan(app: FastAPI):
    initialize()
    yield

app = FastAPI(title="NeuroTeacher API", version="0.1.0", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://127.0.0.1:5173", "http://localhost:5173"],
    allow_origin_regex=r"https?://(localhost|127\.0\.0\.1|10\.\d+\.\d+\.\d+|192\.168\.\d+\.\d+|172\.(1[6-9]|2\d|3[01])\.\d+\.\d+)(:\d+)?",
    allow_methods=["*"],
    allow_headers=["*"],
)

class Answer(BaseModel):
    answer: Literal["A", "B", "C", "D"]
    response_time_seconds: float | None = Field(default=None, ge=0, allow_inf_nan=False)

    @field_validator("answer", mode="before")
    @classmethod
    def uppercase_answer(cls, value):
        return value.upper() if isinstance(value, str) else value

class ExamStart(BaseModel):
    model_config = ConfigDict(extra="forbid")
    exam_format: Literal["D", "B"]
    locale: Locale = "es"

class ExamAnswer(Answer):
    model_config = ConfigDict(extra="forbid")
    question_id: int = Field(gt=0, strict=True)

class ExamResult(BaseModel):
    model_config = ConfigDict(extra="forbid")
    session_id: str = Field(min_length=1, max_length=128)
    answers: list[ExamAnswer] = Field(max_length=75)

EXAM_FORMATS = {
    "D": {"id": "D", "questions": 65, "passing_score": 32, "minutes": 180, "includes_spanish": False},
    "B": {"id": "B", "questions": 75, "passing_score": 37, "minutes": 240, "includes_spanish": True},
}

class ChatMessage(BaseModel):
    role: str
    content: str

class ChatRequest(BaseModel):
    message: str
    history: list[ChatMessage] = []

def ai_provider_config() -> dict[str, str | None]:
    provider = os.getenv("AI_PROVIDER", "openai").lower()
    if provider == "deepseek":
        return {
            "provider": "deepseek",
            "key": os.getenv("DEEPSEEK_API_KEY"),
            "model": os.getenv("DEEPSEEK_MODEL", "deepseek-chat"),
        }
    return {
        "provider": "openai",
        "key": os.getenv("OPENAI_API_KEY"),
        "model": os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
    }

def ai_provider_health(timeout: int = 5) -> dict[str, object]:
    config = ai_provider_config()
    if not config["key"]:
        return {"provider": config["provider"], "configured": False, "available": False, "reason": "api_key_missing"}
    if config["provider"] == "deepseek":
        url = "https://api.deepseek.com/chat/completions"
        body = {"model": config["model"], "messages": [{"role": "user", "content": "ping"}], "temperature": 0, "max_tokens": 1}
    else:
        url = "https://api.openai.com/v1/responses"
        body = {"model": config["model"], "input": [{"role": "user", "content": "ping"}], "max_output_tokens": 16}
    req = urlrequest.Request(
        url,
        data=json.dumps(body).encode("utf-8"),
        headers={"Authorization": f"Bearer {config['key']}", "Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urlrequest.urlopen(req, timeout=timeout) as response:
            return {
                "provider": config["provider"],
                "configured": True,
                "available": 200 <= response.status < 300,
                "model": config["model"],
            }
    except HTTPError as exc:
        return {"provider": config["provider"], "configured": True, "available": False, "model": config["model"], "reason": f"http_{exc.code}"}
    except URLError:
        return {"provider": config["provider"], "configured": True, "available": False, "model": config["model"], "reason": "unreachable"}
    except Exception:
        return {"provider": config["provider"], "configured": True, "available": False, "model": config["model"], "reason": "probe_failed"}

def sanitize_ai_text(text: str) -> str:
    text = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", r"\1", text)
    text = re.sub(r"(?m)^\s{0,3}#{1,6}\s*", "", text)
    text = re.sub(r"(?m)^\s*-{3,}\s*$", "", text)
    text = re.sub(r"[*_`~]{1,3}", "", text)
    text = text.replace("#", "")
    return re.sub(r"\s+", " ", text).strip()

def local_ai_reply(message: str, reason: str = "provider_unavailable") -> str:
    asks_in_russian = bool(re.search(r"[\u0400-\u04FF]", message))
    spanish = (
        "Estoy en modo local porque el proveedor de IA no responde ahora. "
        "Puedo ayudarte con pr\u00e1ctica b\u00e1sica: responde en espa\u00f1ol con una frase corta y luego revisamos. "
        "Pregunta: \u00bfCu\u00e1l es la capital de Colombia?"
    )
    russian = (
        "\u0421\u0435\u0439\u0447\u0430\u0441 \u0432\u043a\u043b\u044e\u0447\u0435\u043d \u043b\u043e\u043a\u0430\u043b\u044c\u043d\u044b\u0439 \u0440\u0435\u0436\u0438\u043c: "
        "\u0432\u043d\u0435\u0448\u043d\u0438\u0439 AI-\u043f\u0440\u043e\u0432\u0430\u0439\u0434\u0435\u0440 \u043d\u0435\u0434\u043e\u0441\u0442\u0443\u043f\u0435\u043d. "
        "\u042f \u043c\u043e\u0433\u0443 \u0434\u0430\u0442\u044c \u0431\u0430\u0437\u043e\u0432\u0443\u044e \u0442\u0440\u0435\u043d\u0438\u0440\u043e\u0432\u043a\u0443 \u0431\u0435\u0437 \u0441\u0435\u0442\u0438: "
        "\u043e\u0442\u0432\u0435\u0442\u044c\u0442\u0435 \u043f\u043e-\u0438\u0441\u043f\u0430\u043d\u0441\u043a\u0438 \u043a\u043e\u0440\u043e\u0442\u043a\u043e\u0439 \u0444\u0440\u0430\u0437\u043e\u0439, "
        "\u0437\u0430\u0442\u0435\u043c \u043f\u0440\u043e\u0432\u0435\u0440\u0438\u043c. "
        "\u0412\u043e\u043f\u0440\u043e\u0441: \u043a\u0430\u043a\u0430\u044f \u0441\u0442\u043e\u043b\u0438\u0446\u0430 \u041a\u043e\u043b\u0443\u043c\u0431\u0438\u0438?"
    )
    if asks_in_russian:
        return f"{russian}\n\nES: {spanish}"
    return f"{spanish}\n\nRU: {russian}"

class SpeechRequest(BaseModel):
    text: str
    rate: str = "+0%"
    locale: str | None = None

class StudyPlanSettings(BaseModel):
    exam_date: date

class QuestionGenerationRequest(BaseModel):
    source_id: int = 1
    page_number: int
    count: int = 5
    force: bool = False

MODULE_ORDER = ("География", "История", "Конституция", "Испанский", "Культура", "Натурализация", "Микротемы")
AUDIO_LESSONS = {
    "География": {"id": "geography", "title": "География Колумбии", "file": "lesson-01-geography-full.mp3"},
    "История": {"id": "history", "title": "История Колумбии", "file": "lesson-02-history-full.mp3"},
    "Конституция": {"id": "constitution", "title": "Конституция и государство", "file": "lesson-03-constitution-full.mp3"},
    "Испанский": {"id": "spanish", "title": "Испанский язык", "file": "lesson-04-spanish-full.mp3"},
    "Культура": {"id": "culture", "title": "Культура Колумбии", "file": "lesson-05-culture-full.mp3"},
    "Натурализация": {"id": "naturalization", "title": "Натурализация", "file": "lesson-06-naturalization-full.mp3"},
}

def module_name(topic: str) -> str:
    if topic in MODULE_ORDER:
        return topic
    value = topic.casefold()
    if any(key in value for key in ("geograf", "hidrograf", "relieve", "cordillera", "amazon")) or "гидрограф" in value:
        return "География"
    if any(key in value for key in ("historia", "independencia", "colonial", "guerra", "violencia", "república", "republica")):
        return "История"
    if any(key in value for key in ("constituci", "tutela", "habeas", "rama ", "soberan", "plebiscito", "referendo", "legislativa", "control", "participación", "participacion", "ciudadano", "derecho")):
        return "Конституция"
    if any(key in value for key in ("castellano", "español", "espaã", "verbo", "adjet", "sustant", "pret", "futuro", "género", "genero", "palabra", "sílaba", "silaba", "vocabulario", "prepos")):
        return "Испанский"
    if any(key in value for key in ("cultura", "paz", "valores", "patrimonio", "afrocolomb", "indígen", "indigen", "turismo")):
        return "Культура"
    if any(key in value for key in ("naturaliz", "nacionalidad", "sitac", "visa", "residente", "requisito")):
        return "Натурализация"
    return "Микротемы"

@app.get('/api/locales')
def locales():
    return [{'id': locale, 'label': label} for locale, label in zip(LOCALES, LOCALE_LABELS)]

@app.get('/api/health')
def health(): return {"status": "ok"}

@app.post('/api/consultant/speech')
async def consultant_speech(payload: SpeechRequest):
    text = sanitize_ai_text(payload.text)
    if not text:
        raise HTTPException(400, "Text is required")
    voice = "ru-RU-DmitryNeural" if re.search(r"[А-Яа-яЁё]", text) else "es-CO-GonzaloNeural"
    if payload.locale == "es-CO":
        voice = "es-CO-GonzaloNeural"
    elif payload.locale == "ru-RU":
        voice = "ru-RU-DmitryNeural"
    try:
        audio = bytearray()
        communicate = edge_tts.Communicate(text, voice=voice, rate=payload.rate)
        async for chunk in communicate.stream():
            if chunk["type"] == "audio":
                audio.extend(chunk["data"])
        return Response(content=bytes(audio), media_type="audio/mpeg")
    except Exception:
        raise HTTPException(502, "Speech service is unavailable")

@app.get('/api/questions')
def questions(limit: int = 20, topic: str | None = None, exclude: str | None = None, locale: Locale = 'es'):
    excluded_ids = [int(value) for value in (exclude or '').split(',') if value.strip().isdigit()]
    excluded_sql = f" AND id NOT IN ({','.join('?' for _ in excluded_ids)})" if excluded_ids else ''
    filters = admitted_questions() + excluded_sql
    fields = "id,question_es,question_ru,answer_a,answer_a_ru,answer_b,answer_b_ru,answer_c,answer_c_ru,answer_d,answer_d_ru,topic,status,source_page"
    with conn() as db:
        if topic and topic in MODULE_ORDER:
            candidates = db.execute(f"SELECT {fields} FROM questions WHERE {filters} ORDER BY RANDOM()", (*excluded_ids,)).fetchall()
            rows = [row for row in candidates if module_name(row["topic"]) == topic][:limit]
        elif topic:
            rows = db.execute(f"SELECT {fields} FROM questions WHERE {filters} AND topic=? ORDER BY RANDOM() LIMIT ?", (*excluded_ids, topic, limit)).fetchall()
        else:
            rows = db.execute(f"SELECT {fields} FROM questions WHERE {filters} ORDER BY RANDOM() LIMIT ?", (*excluded_ids, limit)).fetchall()
    return localize_questions(db, rows, locale)

@app.get('/api/study-plan')
def study_plan(exam_date: date | None = None):
    """Create a daily plan that consumes unseen questions before any fallback repeats."""
    with conn() as db:
        if exam_date is None:
            saved = db.execute("SELECT value FROM study_settings WHERE key='exam_date'").fetchone()
            if not saved:
                return {"exam_date": None, "days_left": None, "message": "Укажите дату экзамена, чтобы составить план."}
            exam_date = date.fromisoformat(saved['value'])
        days_left = (exam_date - date.today()).days
        if days_left < 1:
            raise HTTPException(400, "Exam date must be in the future")

        allowed = admitted_questions()
        total = db.execute(f"SELECT COUNT(*) FROM questions WHERE {allowed}").fetchone()[0]
        unseen = db.execute(f'''SELECT COUNT(*) FROM questions q
            WHERE {admitted_questions("q")} AND NOT EXISTS (SELECT 1 FROM attempts a WHERE a.question_id=q.id)''').fetchone()[0]
        due = db.execute(f'''SELECT COUNT(*) FROM review_queue r JOIN questions q ON q.id=r.question_id
            WHERE {admitted_questions("q")} AND date(r.due_at) <= date('now','localtime')''').fetchone()[0]
        daily_new = max(1, (unseen + days_left - 1) // days_left) if unseen else 0
        daily_reviews = min(due, max(5, daily_new // 2))

        topic_rows = db.execute(f'''SELECT q.topic, COUNT(DISTINCT q.id) AS available,
            COUNT(DISTINCT CASE WHEN NOT EXISTS (SELECT 1 FROM attempts a WHERE a.question_id=q.id) THEN q.id END) AS unseen,
            ROUND(100.0 * AVG(CASE WHEN a.correct IS NULL THEN NULL ELSE a.correct END)) AS score
            FROM questions q LEFT JOIN attempts a ON a.question_id=q.id
            WHERE {admitted_questions("q")} GROUP BY q.topic ORDER BY q.topic''').fetchall()
    topics = []
    for row in topic_rows:
        if row['unseen']:
            weakness = 1.0 if row['score'] is None else 1 + (100 - row['score']) / 100
            topics.append({"topic": row['topic'], "available": row['available'], "unseen": row['unseen'], "score": row['score'], "priority": round(weakness, 2)})
    return {
        "exam_date": exam_date.isoformat(), "days_left": days_left, "daily_new": daily_new,
        "daily_reviews": daily_reviews, "total_available": total, "unseen": unseen,
        "topics": sorted(topics, key=lambda item: (-item['priority'], -item['unseen']))
    }

@app.get('/api/study-plan/today')
def today_study_plan(exam_date: date | None = None):
    plan = study_plan(exam_date)
    if not plan.get("exam_date"):
        return {
            **plan,
            "mode": "setup",
            "target_questions": 0,
            "estimated_minutes": 0,
            "modules": [],
            "focus_topics": [],
            "lesson": [],
        }

    days_left = plan["days_left"]
    daily_new = plan["daily_new"]
    daily_reviews = plan["daily_reviews"]
    target_questions = max(5, daily_new + daily_reviews)
    mini_test = min(15, max(5, round(target_questions * 0.35)))
    mode = "спокойный" if days_left > 60 else "нормальный" if days_left > 30 else "интенсивный" if days_left > 14 else "финальный рывок"

    modules = {name: {"module": name, "available": 0, "unseen": 0, "priority": 1.0} for name in MODULE_ORDER}
    with conn() as db:
        all_topics = db.execute(f"""
            SELECT topic, COUNT(*) AS available
            FROM questions
            WHERE {admitted_questions()}
            GROUP BY topic
        """).fetchall()
    for item in all_topics:
        modules[module_name(item["topic"])]["available"] += item["available"]
    for item in plan["topics"]:
        name = module_name(item["topic"])
        modules[name]["unseen"] += item["unseen"]
        modules[name]["priority"] = max(modules[name]["priority"], item["priority"])
    module_list = sorted(
        [item for item in modules.values() if item["available"] or item["unseen"]],
        key=lambda item: (MODULE_ORDER.index(item["module"]), -item["priority"], -item["unseen"]),
    )

    focus_topics = plan["topics"][:5]
    focus_name = module_name(focus_topics[0]["topic"]) if focus_topics else (module_list[0]["module"] if module_list else "Общий повтор")
    error_review = min(8, max(3, daily_reviews))
    lesson = [
        {"step": 1, "title": f"Теория: {focus_name}", "minutes": 10, "kind": "theory", "description": "Коротко повторить материал модуля и прослушать аудиоурок модуля дня."},
        {"step": 2, "title": "Новые вопросы", "minutes": max(8, daily_new), "kind": "new", "count": daily_new, "description": "Пройти новые вопросы, которых еще не было в попытках."},
        {"step": 3, "title": "Повторение", "minutes": max(6, daily_reviews), "kind": "review", "count": daily_reviews, "description": "Закрепить вопросы из очереди интервального повторения."},
        {"step": 4, "title": "Разбор ошибок", "minutes": error_review, "kind": "errors", "count": error_review, "description": "Открыть объяснения и понять причину ошибки."},
        {"step": 5, "title": "Мини-тест", "minutes": mini_test, "kind": "test", "count": mini_test, "description": "Ответить без подсказок и сохранить результат в прогресс."},
    ]
    if date.today().weekday() == 6 or days_left <= 14:
        lesson.append({"step": 6, "title": "Симуляция экзамена", "minutes": 35, "kind": "exam", "count": 30, "description": "Раз в неделю проходить длинный блок в режиме экзамена."})

    return {
        **plan,
        "mode": mode,
        "target_questions": target_questions,
        "estimated_minutes": sum(item["minutes"] for item in lesson),
        "modules": module_list,
        "focus_topics": focus_topics,
        "audio_lesson": AUDIO_LESSONS.get(focus_name),
        "lesson": lesson,
    }

@app.put('/api/study-plan')
def save_study_plan(payload: StudyPlanSettings):
    if payload.exam_date <= date.today():
        raise HTTPException(400, "Exam date must be in the future")
    with conn() as db:
        db.execute("INSERT INTO study_settings(key,value) VALUES('exam_date',?) ON CONFLICT(key) DO UPDATE SET value=excluded.value", (payload.exam_date.isoformat(),))
    return study_plan(payload.exam_date)

@app.get('/api/study-plan/questions')
def study_plan_questions(limit: int = 20, locale: Locale = 'es'):
    """Return due reviews first, then questions never answered by the learner."""
    limit = min(max(limit, 1), 50)
    fields = 'id,question_es,question_ru,answer_a,answer_a_ru,answer_b,answer_b_ru,answer_c,answer_c_ru,answer_d,answer_d_ru,topic,status,source_page'
    with conn() as db:
        due = db.execute(f'''SELECT q.{fields} FROM review_queue r JOIN questions q ON q.id=r.question_id
            WHERE {admitted_questions("q")} AND date(r.due_at) <= date('now','localtime')
            ORDER BY r.due_at, q.id LIMIT ?''', (limit,)).fetchall()
        remaining = limit - len(due)
        fresh = [] if remaining == 0 else db.execute(f'''SELECT {fields} FROM questions q
            WHERE {admitted_questions("q")} AND NOT EXISTS (SELECT 1 FROM attempts a WHERE a.question_id=q.id)
            ORDER BY RANDOM() LIMIT ?''', (remaining,)).fetchall()
    return {"questions": localize_questions(db, [*due, *fresh], locale), "due_reviews": len(due), "new_questions": len(fresh)}

@app.post('/api/questions/generate')
def generate_questions(payload: QuestionGenerationRequest):
    """Generate once from an official material page and persist the result for review."""
    count = min(max(payload.count, 1), 10)
    with conn() as db:
        page = db.execute("SELECT text FROM material_pages WHERE source_id=? AND page_number=?", (payload.source_id, payload.page_number)).fetchone()
        if not page:
            raise HTTPException(404, "Material page not found")
        existing = db.execute("SELECT COUNT(*) FROM questions WHERE source_id=? AND source_page=?", (payload.source_id, payload.page_number)).fetchone()[0]
        if existing >= count and not payload.force:
            return {"created": 0, "skipped": True, "existing": existing, "message": "Questions for this page are already saved."}
        needed = count if payload.force else count - existing

    provider = os.getenv("AI_PROVIDER", "openai").lower()
    key_name = "DEEPSEEK_API_KEY" if provider == "deepseek" else "OPENAI_API_KEY"
    key = os.getenv(key_name)
    if not key:
        raise HTTPException(503, f"{key_name} is not configured")
    source_text = page['text'][:12000]
    prompt = f'''Create exactly {needed} multiple-choice questions from the official Colombian nationality-study material below.
Use only facts explicitly stated in the source. Each question must have one correct answer and three plausible but false alternatives.
Write question and answers in Spanish, plus Russian translations and a short Russian explanation. Return JSON only, as an array of objects with keys: question_es, question_ru, answer_a, answer_a_ru, answer_b, answer_b_ru, answer_c, answer_c_ru, answer_d, answer_d_ru, correct_answer, topic, explanation_es, explanation_ru, source_quote.
correct_answer must be A, B, C, or D. source_quote must be a short supporting quote from this source.
Official source, page {payload.page_number}:
{source_text}'''
    try:
        if provider == "deepseek":
            request_body = {"model": os.getenv("DEEPSEEK_MODEL", "deepseek-chat"), "messages": [{"role": "user", "content": prompt}], "temperature": 0.2, "response_format": {"type": "json_object"}}
            req = urlrequest.Request("https://api.deepseek.com/chat/completions", data=json.dumps(request_body).encode("utf-8"), headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"}, method="POST")
            with urlrequest.urlopen(req, timeout=90) as response:
                raw = json.loads(response.read().decode("utf-8"))["choices"][0]["message"]["content"]
        else:
            request_body = {"model": os.getenv("OPENAI_MODEL", "gpt-4o-mini"), "input": [{"role": "developer", "content": "Return valid JSON only."}, {"role": "user", "content": prompt}], "text": {"format": {"type": "json_object"}}, "max_output_tokens": 5000}
            req = urlrequest.Request("https://api.openai.com/v1/responses", data=json.dumps(request_body).encode("utf-8"), headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"}, method="POST")
            with urlrequest.urlopen(req, timeout=90) as response:
                data = json.loads(response.read().decode("utf-8"))
                raw = "".join(part.get("text", "") for output in data.get("output", []) if output.get("type") == "message" for part in output.get("content", []) if part.get("type") == "output_text")
        generated = json.loads(raw)
        if isinstance(generated, dict):
            generated = generated.get("questions", [])
        if not isinstance(generated, list):
            raise ValueError("Expected a JSON array of questions")
    except (HTTPError, URLError, ValueError, KeyError, json.JSONDecodeError) as error:
        raise HTTPException(502, f"Question generation failed: {error}")

    required = (
        "question_es", "question_ru", "answer_a", "answer_a_ru", "answer_b", "answer_b_ru",
        "answer_c", "answer_c_ru", "answer_d", "answer_d_ru", "correct_answer", "topic",
        "explanation_es", "explanation_ru", "source_quote"
    )
    created = 0
    with conn() as db:
        for item in generated[:needed]:
            if not isinstance(item, dict) or any(not str(item.get(field, "")).strip() for field in required) or item.get("correct_answer") not in ("A", "B", "C", "D"):
                continue
            duplicate = db.execute("SELECT 1 FROM questions WHERE source_id=? AND source_page=? AND lower(question_es)=lower(?)", (payload.source_id, payload.page_number, item["question_es"].strip())).fetchone()
            if duplicate:
                continue
            db.execute('''INSERT INTO questions(question_es,question_ru,answer_a,answer_a_ru,answer_b,answer_b_ru,answer_c,answer_c_ru,answer_d,answer_d_ru,correct_answer,topic,explanation_es,explanation_ru,source_quote,status,source_id,source_page)
                VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)''', (
                item["question_es"].strip(), item.get("question_ru", "").strip(), item["answer_a"].strip(), item.get("answer_a_ru", "").strip(), item["answer_b"].strip(), item.get("answer_b_ru", "").strip(), item["answer_c"].strip(), item.get("answer_c_ru", "").strip(), item["answer_d"].strip(), item.get("answer_d_ru", "").strip(), item["correct_answer"], item["topic"].strip(), item["explanation_es"].strip(), item.get("explanation_ru", "").strip(), item.get("source_quote", "").strip(), "ai_reviewed", payload.source_id, payload.page_number))
            created += 1
    return {"created": created, "skipped": False, "status": "ai_reviewed", "source_page": payload.page_number}

@app.get('/api/exams/formats')
def exam_formats():
    with conn() as db:
        available = db.execute(f"SELECT COUNT(*) FROM questions WHERE {admitted_questions()}").fetchone()[0]
        verified = db.execute("SELECT COUNT(*) FROM questions WHERE status='verified'").fetchone()[0]
    return {
        "available_questions": available,
        "verified_questions": verified,
        "formats": list(EXAM_FORMATS.values()),
    }

def record_attempt(db, question_id: int, answer_value: str, correct: bool, response_time_seconds=None):
    db.execute("INSERT INTO attempts(question_id,answer,correct,response_time_seconds) VALUES(?,?,?,?)",
               (question_id, answer_value, correct, response_time_seconds))
    existing = db.execute("SELECT step FROM review_queue WHERE question_id=?", (question_id,)).fetchone()
    if correct:
        step = min((existing['step'] if existing else -1) + 1, 4)
        days = (1, 3, 7, 14, 30)[step]
    else:
        step, days = 0, 1
    due = (date.today() + timedelta(days=days)).isoformat()
    db.execute("INSERT INTO review_queue(question_id,due_at,step) VALUES(?,?,?) ON CONFLICT(question_id) DO UPDATE SET due_at=excluded.due_at, step=excluded.step", (question_id, due, step))

@app.post('/api/questions/{question_id}/answer')
def answer(question_id: int, payload: Answer, locale: Locale = 'es'):
    with conn() as db:
        q = db.execute(f"SELECT id, correct_answer, explanation_es, explanation_ru FROM questions WHERE id=? AND {admitted_questions()}", (question_id,)).fetchone()
        if not q: raise HTTPException(404, "Question not found")
        correct = payload.answer.upper() == q['correct_answer']
        record_attempt(db, question_id, payload.answer, correct, payload.response_time_seconds)
    result = localize_questions(db, [q], locale)[0]
    result.pop("id", None)
    result["correct"] = correct
    return result

@app.post('/api/exams/start')
def start_exam(payload: ExamStart, locale: Locale | None = None):
    config = EXAM_FORMATS[payload.exam_format]
    token = secrets.token_urlsafe(32)
    started_at = datetime.now(timezone.utc).isoformat()
    fields = "id,question_es,question_ru,answer_a,answer_a_ru,answer_b,answer_b_ru,answer_c,answer_c_ru,answer_d,answer_d_ru,topic,status,source_page,correct_answer"
    with conn() as db:
        db.execute("BEGIN IMMEDIATE")
        rows = db.execute(f"SELECT {fields} FROM questions WHERE {admitted_questions()} ORDER BY RANDOM() LIMIT ?", (config["questions"],)).fetchall()
        if not rows:
            raise HTTPException(409, "No admitted questions available")
        db.execute("INSERT INTO exam_runs(token,exam_format,started_at) VALUES(?,?,?)",
                   (token, payload.exam_format, started_at))
        questions = []
        rows = localize_questions(db, rows, locale or payload.locale)
        for position, row in enumerate(rows):
            question = dict(row)
            key = question.pop("correct_answer")
            db.execute("INSERT INTO exam_run_questions VALUES(?,?,?,?,?)",
                       (token, question["id"], position, key, json.dumps(question, ensure_ascii=False)))
            questions.append(question)
    return {"session_id": token, "exam_format": payload.exam_format, "started_at": started_at,
            "total_questions": len(questions), "minutes": config["minutes"], "questions": questions}

@app.post('/api/exams/complete')
def complete_exam(payload: ExamResult):
    answers = {item.question_id: item for item in payload.answers}
    if len(answers) != len(payload.answers):
        raise HTTPException(422, "Duplicate question IDs")
    canonical = json.dumps([item.model_dump() for item in sorted(payload.answers, key=lambda a: a.question_id)], sort_keys=True, separators=(",", ":"))
    submission_sha256 = hashlib.sha256(canonical.encode()).hexdigest()
    with conn() as db:
        # Serialize completion and retries so history and results are saved once.
        db.execute("BEGIN IMMEDIATE")
        run = db.execute("SELECT * FROM exam_runs WHERE token=?", (payload.session_id,)).fetchone()
        if not run:
            raise HTTPException(404, "Exam session not found")
        if run["result_json"]:
            if run["submission_sha256"] != submission_sha256:
                raise HTTPException(409, "Exam session already completed with different answers")
            return json.loads(run["result_json"])
        selected = db.execute(f"""SELECT s.question_id,s.correct_answer,q.id AS admitted_id
            FROM exam_run_questions s LEFT JOIN questions q ON q.id=s.question_id AND {admitted_questions("q")}
            WHERE s.run_token=? ORDER BY s.position""", (payload.session_id,)).fetchall()
        selected_ids = {row["question_id"] for row in selected}
        if not selected or not set(answers).issubset(selected_ids):
            raise HTTPException(422, "Answer contains a question outside this exam session")
        if any(row["admitted_id"] is None for row in selected):
            raise HTTPException(409, "A question in this exam session is no longer admitted")
        correct_answers = 0
        for row in selected:
            item = answers.get(row["question_id"])
            if item is None:
                continue  # Unanswered questions remain in the denominator.
            correct = item.answer == row["correct_answer"]
            correct_answers += int(correct)
            record_attempt(db, item.question_id, item.answer, correct, item.response_time_seconds)
        cursor = db.execute("INSERT INTO exam_sessions(total_questions,correct_answers) VALUES(?,?)",
                            (len(selected), correct_answers))
        duration_seconds = max(0, int((datetime.now(timezone.utc) - datetime.fromisoformat(run["started_at"])).total_seconds()))
        config = EXAM_FORMATS[run["exam_format"]]
        passing_score = math.ceil(len(selected) * config["passing_score"] / config["questions"])
        result = {"id": cursor.lastrowid, "saved": True, "total_questions": len(selected),
                  "correct_answers": correct_answers, "exam_format": run["exam_format"],
                  "duration_seconds": duration_seconds, "passing_score": passing_score,
                  "passed": correct_answers >= passing_score}
        db.execute("UPDATE exam_runs SET submission_sha256=?,result_json=? WHERE token=?",
                   (submission_sha256, json.dumps(result), payload.session_id))
    return result

@app.get('/api/ai/status')
def ai_status():
    status = ai_provider_health()
    status["mode"] = "remote" if status["available"] else "local_fallback"
    return status

@app.post('/api/ai/chat')
def ai_chat(payload: ChatRequest):
    config = ai_provider_config()
    provider = str(config["provider"])
    system = """Eres un profesor para el examen de nacionalidad colombiana. Habla principalmente en español claro, nivel A2-B1. Si el estudiante escribe en ruso, añade una explicación breve en ruso. Corrige errores con tacto. Haz una sola pregunta cada vez. No inventes datos oficiales; indica cuando algo requiere verificar la guía Colombia, nuestra casa."""
    system += " Always add a concise Russian translation after every Spanish explanation, question, or correction. Use clear plain text without Markdown or emoji."
    history = [{"role": item.role, "content": item.content} for item in payload.history[-10:]]
    def post_json(url: str, key: str, body: dict):
        req = urlrequest.Request(url, data=json.dumps(body).encode("utf-8"), headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"}, method="POST")
        with urlrequest.urlopen(req, timeout=60) as response:
            return json.loads(response.read().decode("utf-8"))
    try:
        if provider == "deepseek":
            key = config["key"]
            if not key:
                return {"provider": provider, "reply": local_ai_reply(payload.message, "api_key_missing"), "fallback": True, "reason": "api_key_missing"}
            data = post_json("https://api.deepseek.com/chat/completions", str(key), {"model": config["model"], "messages": [{"role":"system","content":system}, *history, {"role":"user","content":payload.message}], "temperature":0.35, "max_tokens":220})
            text = data["choices"][0]["message"]["content"]
        else:
            key = config["key"]
            if not key:
                return {"provider": provider, "reply": local_ai_reply(payload.message, "api_key_missing"), "fallback": True, "reason": "api_key_missing"}
            input_messages = [{"role":"developer","content":system}, *history, {"role":"user","content":payload.message}]
            data = post_json("https://api.openai.com/v1/responses", str(key), {"model": config["model"], "input": input_messages, "max_output_tokens":600})
            text = "".join(part.get("text", "") for output in data.get("output", []) if output.get("type") == "message" for part in output.get("content", []) if part.get("type") == "output_text")
        return {"provider": provider, "reply": sanitize_ai_text(text), "fallback": False}
    except HTTPError as exc:
        return {"provider": provider, "reply": local_ai_reply(payload.message, f"http_{exc.code}"), "fallback": True, "reason": f"http_{exc.code}"}
    except URLError:
        return {"provider": provider, "reply": local_ai_reply(payload.message, "unreachable"), "fallback": True, "reason": "unreachable"}
    except Exception:
        return {"provider": provider, "reply": local_ai_reply(payload.message, "request_failed"), "fallback": True, "reason": "request_failed"}

@app.get('/api/dashboard')
def dashboard():
    with conn() as db:
        total = db.execute("SELECT COUNT(*) FROM attempts").fetchone()[0]
        correct = db.execute("SELECT COUNT(*) FROM attempts WHERE correct=1").fetchone()[0]
        average_time = db.execute("SELECT AVG(response_time_seconds) FROM attempts WHERE response_time_seconds IS NOT NULL").fetchone()[0]
        exams = db.execute("SELECT COUNT(*) FROM exam_sessions").fetchone()[0]
        due_reviews = db.execute(f"SELECT COUNT(*) FROM review_queue r JOIN questions q ON q.id=r.question_id WHERE {admitted_questions('q')} AND date(r.due_at) <= date('now','localtime')").fetchone()[0]
        active_days = {date.fromisoformat(row[0]) for row in db.execute("SELECT DISTINCT date(created_at, 'localtime') FROM attempts")}
        recent = [dict(row) for row in db.execute(f'''
            SELECT q.question_es, q.topic, a.correct, a.created_at
            FROM attempts a JOIN questions q ON q.id=a.question_id
            WHERE {admitted_questions("q")}
            ORDER BY a.id DESC LIMIT 5
        ''').fetchall()]
        raw_topic_counts = [dict(row) for row in db.execute(f"SELECT topic, COUNT(*) AS count FROM questions WHERE {admitted_questions()} GROUP BY topic ORDER BY count DESC").fetchall()]
        module_counts = {name: 0 for name in MODULE_ORDER}
        for row in raw_topic_counts:
            module_counts[module_name(row["topic"])] += row["count"]
        topic_counts = [{"topic": name, "count": count} for name, count in module_counts.items() if count]
        trend = []
        today = date.today()
        for days_ago in range(4, -1, -1):
            day = today - timedelta(days=days_ago)
            row = db.execute("SELECT COUNT(*), COALESCE(SUM(correct),0) FROM attempts WHERE date(created_at,'localtime') = ?", (day.isoformat(),)).fetchone()
            trend.append({"date": day.isoformat(), "score": round(row[1] / row[0] * 100) if row[0] else None, "attempts": row[0]})
        calendar = []
        for days_ago in range(29, -1, -1):
            day = today - timedelta(days=days_ago)
            row = db.execute("SELECT COUNT(*), COALESCE(SUM(correct),0) FROM attempts WHERE date(created_at,'localtime') = ?", (day.isoformat(),)).fetchone()
            calendar.append({"date": day.isoformat(), "attempts": row[0], "score": round(row[1] / row[0] * 100) if row[0] else None})
    streak = 0
    cursor = date.today()
    while cursor in active_days:
        streak += 1
        cursor -= timedelta(days=1)
    return {
        "attempts": total, "correct": correct,
        "score": round(correct / total * 100) if total else 0,
        "streak": streak, "exams": exams, "average_time_seconds": round(average_time, 1) if average_time is not None else None,
        "recent_activity": recent, "trend": trend, "calendar": calendar,
        "topic_counts": topic_counts, "due_reviews": due_reviews,
    }

@app.get('/api/materials/chapters')
def material_chapters():
    # Curated learning map. Raw OCR/PDF headings remain in material_chapters,
    # but are deliberately not shown as course navigation.
    return [
        {"title": "Cultura y sociedad", "title_ru": "Культура и общество", "page_number": 4},
        {"title": "Geografía de Colombia", "title_ru": "География Колумбии", "page_number": 63},
        {"title": "Historia de Colombia: cronología", "title_ru": "История Колумбии: хронология", "page_number": 108},
        {"title": "Constitución y estructura del Estado", "title_ru": "Конституция и устройство государства", "page_number": 154},
        {"title": "Castellano: alfabeto y vocabulario", "title_ru": "Испанский язык: алфавит и словарь", "page_number": 160},
        {"title": "Castellano: nombres comunes y propios", "title_ru": "Испанский язык: нарицательные и собственные имена", "page_number": 170},
    ]

@app.get('/api/errors')
def errors(locale: Locale = 'es'):
    with conn() as db:
        rows = db.execute(f'''
            SELECT q.id, q.question_es, q.topic, q.explanation_es, COUNT(a.id) AS error_count
            FROM attempts a JOIN questions q ON q.id=a.question_id
            WHERE a.correct=0 AND {admitted_questions("q")} GROUP BY q.id ORDER BY error_count DESC, q.id
        ''').fetchall()
    return localize_questions(db, rows, locale)

@app.get('/api/attempts')
def attempts(correct_only: bool = False, limit: int = 50, locale: Locale = 'es'):
    where = " AND a.correct=1" if correct_only else ""
    with conn() as db:
        rows = db.execute(f'''
            SELECT a.id, q.id AS question_id, q.question_es, q.topic, a.answer, a.correct,
                   a.response_time_seconds, a.created_at
            FROM attempts a JOIN questions q ON q.id=a.question_id
            WHERE {admitted_questions("q")}{where} ORDER BY a.id DESC LIMIT ?
        ''', (min(max(limit, 1), 200),)).fetchall()
    return localize_questions(db, rows, locale)

@app.get('/api/explanations')
def explanations(locale: Locale = 'es'):
    with conn() as db:
        rows = db.execute(f'''
            SELECT id, question_es, topic, correct_answer, explanation_es,
                   status, source_page
            FROM questions WHERE {admitted_questions()} ORDER BY topic, id
        ''').fetchall()
    return localize_questions(db, rows, locale)

@app.get('/api/bookmarks')
def bookmarks(locale: Locale = 'es'):
    with conn() as db:
        rows = db.execute(f'''
            SELECT q.id, q.question_es, q.topic, b.created_at
            FROM bookmarks b JOIN questions q ON q.id=b.question_id
            WHERE {admitted_questions("q")}
            ORDER BY b.created_at DESC
        ''').fetchall()
    return localize_questions(db, rows, locale)

@app.get('/api/review/due')
def due_reviews(limit: int = 20, locale: Locale = 'es'):
    with conn() as db:
        rows = db.execute(f'''
            SELECT q.id,q.question_es,q.question_ru,q.answer_a,q.answer_a_ru,q.answer_b,q.answer_b_ru,
                   q.answer_c,q.answer_c_ru,q.answer_d,q.answer_d_ru,q.topic,q.source_page,r.due_at
            FROM review_queue r JOIN questions q ON q.id=r.question_id
            WHERE {admitted_questions("q")} AND date(r.due_at) <= date('now','localtime')
            ORDER BY r.due_at, q.id LIMIT ?
        ''', (min(max(limit, 1), 50),)).fetchall()
    return localize_questions(db, rows, locale)

@app.post('/api/bookmarks/{question_id}')
def add_bookmark(question_id: int):
    with conn() as db:
        exists = db.execute(f"SELECT 1 FROM questions WHERE id=? AND {admitted_questions()}", (question_id,)).fetchone()
        if not exists: raise HTTPException(404, "Question not found")
        db.execute("INSERT OR IGNORE INTO bookmarks(question_id) VALUES(?)", (question_id,))
        db.execute("INSERT OR IGNORE INTO review_queue(question_id,due_at,step) VALUES(?,date('now','localtime'),0)", (question_id,))
    return {"saved": True}

@app.delete('/api/bookmarks/{question_id}')
def delete_bookmark(question_id: int):
    with conn() as db:
        db.execute("DELETE FROM bookmarks WHERE question_id=?", (question_id,))
    return {"saved": False}

@app.get('/api/topics/weak')
def weak_topics():
    with conn() as db:
        rows = db.execute(f'''
            SELECT q.topic, COUNT(a.id) AS attempts,
            ROUND(100.0 * SUM(a.correct) / COUNT(a.id)) AS score
            FROM attempts a JOIN questions q ON q.id=a.question_id
            WHERE {admitted_questions("q")}
            GROUP BY q.topic HAVING COUNT(a.id) > 0
            ORDER BY score ASC, attempts DESC LIMIT 5
        ''').fetchall()
    modules = {}
    for row in rows:
        name = module_name(row["topic"])
        current = modules.setdefault(name, {"topic": name, "attempts": 0, "correct_weighted": 0.0})
        current["attempts"] += row["attempts"]
        current["correct_weighted"] += (row["score"] or 0) * row["attempts"]
    result = []
    for item in modules.values():
        result.append({
            "topic": item["topic"],
            "attempts": item["attempts"],
            "score": round(item["correct_weighted"] / item["attempts"]) if item["attempts"] else 0,
        })
    return sorted(result, key=lambda item: (item["score"], -item["attempts"]))[:5]
