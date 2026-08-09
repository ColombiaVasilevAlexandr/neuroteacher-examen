from contextlib import asynccontextmanager
from datetime import date, timedelta
from pathlib import Path
import sqlite3
import os
import json
import re
import edge_tts
from urllib import request as urlrequest
from urllib.error import HTTPError, URLError
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
from pydantic import BaseModel

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
        db.execute("INSERT OR IGNORE INTO sources(id,title,url,document_type) VALUES(1,?,?,?)", ("Colombia, nuestra casa", SOURCE_URL, "official_study_guide"))
        if db.execute("SELECT COUNT(*) FROM questions").fetchone()[0] == 0:
            db.executemany("INSERT INTO questions(question_es,answer_a,answer_b,answer_c,answer_d,correct_answer,topic,explanation_es,status,source_id) VALUES(?,?,?,?,?,?,?,?,?,1)", [(*q, "reviewed") for q in QUESTIONS])

@asynccontextmanager
async def lifespan(app: FastAPI):
    initialize()
    yield

app = FastAPI(title="NeuroTeacher API", version="0.1.0", lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=["http://127.0.0.1:5173", "http://localhost:5173"], allow_methods=["*"], allow_headers=["*"])

class Answer(BaseModel):
    answer: str
    response_time_seconds: float | None = None

class ExamResult(BaseModel):
    total_questions: int
    correct_answers: int
    exam_format: str = "practice"
    duration_seconds: int | None = None

class ChatMessage(BaseModel):
    role: str
    content: str

class ChatRequest(BaseModel):
    message: str
    history: list[ChatMessage] = []

class SpeechRequest(BaseModel):
    text: str
    rate: str = "+0%"

@app.get('/api/health')
def health(): return {"status": "ok"}

@app.post('/api/consultant/speech')
async def consultant_speech(payload: SpeechRequest):
    text = payload.text.strip()
    if not text:
        raise HTTPException(400, "Text is required")
    voice = "ru-RU-DmitryNeural" if re.search(r"[А-Яа-яЁё]", text) else "es-CO-GonzaloNeural"
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
def questions(limit: int = 20, topic: str | None = None):
    with conn() as db:
        if topic:
            rows = db.execute("SELECT id,question_es,question_ru,answer_a,answer_a_ru,answer_b,answer_b_ru,answer_c,answer_c_ru,answer_d,answer_d_ru,topic,status,source_page FROM questions WHERE status IN ('reviewed','verified','ai_reviewed') AND topic=? ORDER BY RANDOM() LIMIT ?", (topic, limit)).fetchall()
        else:
            rows = db.execute("SELECT id,question_es,question_ru,answer_a,answer_a_ru,answer_b,answer_b_ru,answer_c,answer_c_ru,answer_d,answer_d_ru,topic,status,source_page FROM questions WHERE status IN ('reviewed','verified','ai_reviewed') ORDER BY RANDOM() LIMIT ?", (limit,)).fetchall()
    return [dict(r) for r in rows]

@app.get('/api/exams/formats')
def exam_formats():
    with conn() as db:
        available = db.execute("SELECT COUNT(*) FROM questions WHERE status IN ('reviewed','verified','ai_reviewed')").fetchone()[0]
        verified = db.execute("SELECT COUNT(*) FROM questions WHERE status='verified'").fetchone()[0]
    return {
        "available_questions": available,
        "verified_questions": verified,
        "formats": [
            {"id": "D", "questions": 65, "passing_score": 32, "minutes": 180, "includes_spanish": False},
            {"id": "B", "questions": 75, "passing_score": 37, "minutes": 240, "includes_spanish": True},
        ],
    }

@app.post('/api/questions/{question_id}/answer')
def answer(question_id: int, payload: Answer):
    with conn() as db:
        q = db.execute("SELECT correct_answer, explanation_es, explanation_ru FROM questions WHERE id=?", (question_id,)).fetchone()
        if not q: raise HTTPException(404, "Question not found")
        correct = payload.answer.upper() == q['correct_answer']
        db.execute("INSERT INTO attempts(question_id,answer,correct,response_time_seconds) VALUES(?,?,?,?)", (question_id, payload.answer.upper(), correct, payload.response_time_seconds))
    return {"correct": correct, "correct_answer": q['correct_answer'], "explanation_es": q['explanation_es'], "explanation_ru": q['explanation_ru']}

@app.post('/api/exams/complete')
def complete_exam(payload: ExamResult):
    with conn() as db:
        cursor = db.execute("INSERT INTO exam_sessions(total_questions,correct_answers) VALUES(?,?)", (payload.total_questions, payload.correct_answers))
    return {"id": cursor.lastrowid, "saved": True}

@app.get('/api/ai/status')
def ai_status():
    provider = os.getenv("AI_PROVIDER", "openai").lower()
    available = bool(os.getenv("OPENAI_API_KEY")) if provider == "openai" else bool(os.getenv("DEEPSEEK_API_KEY"))
    return {"provider": provider, "available": available}

@app.post('/api/ai/chat')
def ai_chat(payload: ChatRequest):
    provider = os.getenv("AI_PROVIDER", "openai").lower()
    system = """Eres un profesor para el examen de nacionalidad colombiana. Habla principalmente en español claro, nivel A2-B1. Si el estudiante escribe en ruso, añade una explicación breve en ruso. Corrige errores con tacto. Haz una sola pregunta cada vez. No inventes datos oficiales; indica cuando algo requiere verificar la guía Colombia, nuestra casa."""
    history = [{"role": item.role, "content": item.content} for item in payload.history[-10:]]
    def post_json(url: str, key: str, body: dict):
        req = urlrequest.Request(url, data=json.dumps(body).encode("utf-8"), headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"}, method="POST")
        with urlrequest.urlopen(req, timeout=60) as response:
            return json.loads(response.read().decode("utf-8"))
    try:
        if provider == "deepseek":
            key = os.getenv("DEEPSEEK_API_KEY")
            if not key: raise HTTPException(503, "DEEPSEEK_API_KEY is not configured")
            data = post_json("https://api.deepseek.com/chat/completions", key, {"model": os.getenv("DEEPSEEK_MODEL", "deepseek-chat"), "messages": [{"role":"system","content":system}, *history, {"role":"user","content":payload.message}], "temperature":0.4, "max_tokens":600})
            text = data["choices"][0]["message"]["content"]
        else:
            key = os.getenv("OPENAI_API_KEY")
            if not key: raise HTTPException(503, "OPENAI_API_KEY is not configured")
            input_messages = [{"role":"developer","content":system}, *history, {"role":"user","content":payload.message}]
            data = post_json("https://api.openai.com/v1/responses", key, {"model": os.getenv("OPENAI_MODEL", "gpt-4o-mini"), "input": input_messages, "max_output_tokens":600})
            text = "".join(part.get("text", "") for output in data.get("output", []) if output.get("type") == "message" for part in output.get("content", []) if part.get("type") == "output_text")
        return {"provider": provider, "reply": text}
    except HTTPException:
        raise
    except HTTPError as exc:
        raise HTTPException(502, f"AI provider returned HTTP {exc.code}")
    except URLError:
        raise HTTPException(502, "AI provider is unreachable")
    except Exception:
        raise HTTPException(502, "AI provider request failed")

@app.get('/api/dashboard')
def dashboard():
    with conn() as db:
        total = db.execute("SELECT COUNT(*) FROM attempts").fetchone()[0]
        correct = db.execute("SELECT COUNT(*) FROM attempts WHERE correct=1").fetchone()[0]
        average_time = db.execute("SELECT AVG(response_time_seconds) FROM attempts WHERE response_time_seconds IS NOT NULL").fetchone()[0]
        exams = db.execute("SELECT COUNT(*) FROM exam_sessions").fetchone()[0]
        active_days = {date.fromisoformat(row[0]) for row in db.execute("SELECT DISTINCT date(created_at, 'localtime') FROM attempts")}
        recent = [dict(row) for row in db.execute('''
            SELECT q.question_es, q.topic, a.correct, a.created_at
            FROM attempts a JOIN questions q ON q.id=a.question_id
            ORDER BY a.id DESC LIMIT 5
        ''').fetchall()]
        topic_counts = [dict(row) for row in db.execute("SELECT topic, COUNT(*) AS count FROM questions WHERE status IN ('reviewed','verified') GROUP BY topic ORDER BY count DESC").fetchall()]
        trend = []
        today = date.today()
        for weeks_ago in range(4, -1, -1):
            end = today - timedelta(days=weeks_ago * 7)
            start = end - timedelta(days=6)
            row = db.execute("SELECT COUNT(*), COALESCE(SUM(correct),0) FROM attempts WHERE date(created_at,'localtime') BETWEEN ? AND ?", (start.isoformat(), end.isoformat())).fetchone()
            trend.append({"date": end.isoformat(), "score": round(row[1] / row[0] * 100) if row[0] else None, "attempts": row[0]})
    streak = 0
    cursor = date.today()
    while cursor in active_days:
        streak += 1
        cursor -= timedelta(days=1)
    return {
        "attempts": total, "correct": correct,
        "score": round(correct / total * 100) if total else 0,
        "streak": streak, "exams": exams, "average_time_seconds": round(average_time, 1) if average_time is not None else None,
        "recent_activity": recent, "trend": trend,
        "topic_counts": topic_counts,
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
def errors():
    with conn() as db:
        rows = db.execute('''
            SELECT q.id, q.question_es, q.topic, q.explanation_es, COUNT(a.id) AS error_count
            FROM attempts a JOIN questions q ON q.id=a.question_id
            WHERE a.correct=0 GROUP BY q.id ORDER BY error_count DESC, q.id
        ''').fetchall()
    return [dict(row) for row in rows]

@app.get('/api/attempts')
def attempts(correct_only: bool = False, limit: int = 50):
    where = "WHERE a.correct=1" if correct_only else ""
    with conn() as db:
        rows = db.execute(f'''
            SELECT a.id, q.id AS question_id, q.question_es, q.topic, a.answer, a.correct,
                   a.response_time_seconds, a.created_at
            FROM attempts a JOIN questions q ON q.id=a.question_id
            {where} ORDER BY a.id DESC LIMIT ?
        ''', (min(max(limit, 1), 200),)).fetchall()
    return [dict(row) for row in rows]

@app.get('/api/explanations')
def explanations():
    with conn() as db:
        rows = db.execute('''
            SELECT id, question_es, topic, correct_answer, explanation_es,
                   status, source_page
            FROM questions ORDER BY topic, id
        ''').fetchall()
    return [dict(row) for row in rows]

@app.get('/api/bookmarks')
def bookmarks():
    with conn() as db:
        rows = db.execute('''
            SELECT q.id, q.question_es, q.topic, b.created_at
            FROM bookmarks b JOIN questions q ON q.id=b.question_id
            ORDER BY b.created_at DESC
        ''').fetchall()
    return [dict(row) for row in rows]

@app.post('/api/bookmarks/{question_id}')
def add_bookmark(question_id: int):
    with conn() as db:
        exists = db.execute("SELECT 1 FROM questions WHERE id=?", (question_id,)).fetchone()
        if not exists: raise HTTPException(404, "Question not found")
        db.execute("INSERT OR IGNORE INTO bookmarks(question_id) VALUES(?)", (question_id,))
    return {"saved": True}

@app.delete('/api/bookmarks/{question_id}')
def delete_bookmark(question_id: int):
    with conn() as db:
        db.execute("DELETE FROM bookmarks WHERE question_id=?", (question_id,))
    return {"saved": False}

@app.get('/api/topics/weak')
def weak_topics():
    with conn() as db:
        rows = db.execute('''
            SELECT q.topic, COUNT(a.id) AS attempts,
            ROUND(100.0 * SUM(a.correct) / COUNT(a.id)) AS score
            FROM attempts a JOIN questions q ON q.id=a.question_id
            GROUP BY q.topic HAVING COUNT(a.id) > 0
            ORDER BY score ASC, attempts DESC LIMIT 5
        ''').fetchall()
    return [dict(row) for row in rows]
