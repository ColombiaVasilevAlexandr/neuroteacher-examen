# COLOMBIA EXAM: Source Of Truth

Дата аудита: 2026-08-22.

## Текущий источник истины

Рабочее приложение состоит из:

- `backend/main.py` - FastAPI API, SQLite schema migration, study plan, topics/modules, speech, AI chat, exam and review endpoints.
- `database/colombia_exam.db` - текущая рабочая SQLite база вопросов, попыток, материалов и настроек плана.
- `frontend/public/index.html` - единственный HTML entrypoint для пользовательского запуска.
- `frontend/public/legacy-app.bundle.js` - основной static UI bundle.
- `frontend/public/app.bundle.css` - основной static CSS bundle.
- `frontend/public/study-plan.js` - overlay daily plan and lesson session.
- `frontend/public/audio-library.js` - audio library and "module of the day" playback integration.
- `scripts/start-neuroteacher.ps1` - единственный поддерживаемый локальный запуск.
- `scripts/audit_db.py` - full read-only SQLite audit and report generator.
- `scripts/report_db_encoding.py` - dry-run audit script for suspected mojibake in SQLite text columns.
- `scripts/smoke_test.py` - runtime smoke test for API, frontend contract and database audit invariants.

Главный URL после запуска:

```text
http://127.0.0.1:5173/
```

Backend URL:

```text
http://127.0.0.1:8000/api
```

## Как запускать

Использовать только:

```powershell
powershell -ExecutionPolicy Bypass -File scripts\start-neuroteacher.ps1
```

Без открытия браузера:

```powershell
powershell -ExecutionPolicy Bypass -File scripts\start-neuroteacher.ps1 -NoBrowser
```

Скрипт запускает:

- backend: `python -m uvicorn main:app --host 127.0.0.1 --port 8000` из `backend`;
- frontend: `python -m http.server 5173 --bind 127.0.0.1` из `frontend/public`.

Vite не является рабочим запуском этого дерева.

## Frontend policy

Рабочий frontend - static-only.

Разрешено менять:

- `frontend/public/index.html`;
- подключенные static assets in `frontend/public`;
- `frontend/public/study-plan.js`;
- `frontend/public/audio-library.js`;
- `frontend/public/legacy-app.bundle.js`, если это осознанное обновление основного bundle.

Removed from the active tree:

- `frontend/index.html`;
- `frontend/src/*`;
- `frontend/package.json`;
- Vite config and TypeScript config files.

This repository now has one frontend runtime tree: `frontend/public`.

## Backend policy

Крупные учебные модули задаются в `MODULE_ORDER`:

- `География`
- `История`
- `Конституция`
- `Испанский`
- `Культура`
- `Натурализация`
- `Микротемы`

Сырые темы из вопросов остаются в `questions.topic`.

Публичные student-facing endpoints должны возвращать крупные модули:

- `/api/dashboard`
- `/api/topics/weak`
- `/api/study-plan/today`
- `/api/questions?topic=<module>`

Сырые темы допустимы внутри конкретного вопроса и в generation/audit tooling.

## Database policy

Не удалять и не массово переписывать:

- `database/colombia_exam.db`

Перед любыми write-fix операциями по базе:

1. создать backup рядом с базой:

```text
database/colombia_exam.backup-YYYYMMDD-HHMMSS.db
```

2. запустить dry-run:

```powershell
python scripts\report_db_encoding.py
```

3. применить fix только после просмотра количества строк и примеров.

Текущий backup:

```text
database/colombia_exam.backup-20260821-205537.db
```

## Git hygiene

Не коммитить:

- `.env`
- `backend/.venv/`
- `frontend/node_modules/`
- backup базы
- logs
- `__pycache__`
- build artifacts

Коммит текущего рабочего дерева должен включать только coherent static/backend state:

- `.gitignore`
- `backend/main.py`
- `database/colombia_exam.db`
- `frontend/public/index.html`
- `frontend/public/audio-library.js`
- `frontend/public/legacy-app.bundle.js`
- `frontend/public/study-plan.js`
- `scripts/start-neuroteacher.ps1`
- `scripts/report_db_encoding.py`
- this document
- README pointer/update, if changed

## Required checks before handoff

Syntax:

```powershell
python -m py_compile backend\main.py scripts\report_db_encoding.py scripts\audit_db.py scripts\smoke_test.py
```

Start:

```powershell
powershell -ExecutionPolicy Bypass -File scripts\start-neuroteacher.ps1 -NoBrowser
```

Backend health:

```powershell
Invoke-RestMethod http://127.0.0.1:8000/api/health
```

Static frontend contract:

```powershell
$r = Invoke-WebRequest -UseBasicParsing http://127.0.0.1:5173/
$r.Content.Contains('colombia-exam-static')
$r.Content.Contains('/legacy-app.bundle.js')
$r.Content.Contains('/study-plan.js')
$r.Content.Contains('/audio-library.js')
```

Module routing:

```powershell
python -c "import urllib.request,json,urllib.parse; mods=['География','История','Конституция','Испанский','Культура','Натурализация','Микротемы']; print({m: len(json.load(urllib.request.urlopen('http://127.0.0.1:8000/api/questions?limit=3&topic='+urllib.parse.quote(m)))) for m in mods})"
```

Study plan:

```powershell
python -c "import urllib.request,json; p=json.load(urllib.request.urlopen('http://127.0.0.1:8000/api/study-plan/today?exam_date=2026-12-01')); print(p['total_available'], len(p['modules']), p['audio_lesson'])"
```

Encoding dry-run:

```powershell
python scripts\report_db_encoding.py
```

Full database audit:

```powershell
python scripts\audit_db.py --write
```

Runtime smoke test:

```powershell
python scripts\smoke_test.py
```

Expected current facts:

- backend health: `ok`;
- frontend HTTP status: `200`;
- frontend static marker: present;
- all 7 modules return questions;
- study plan total: `646`;
- study plan modules: `7`;
- `audio_lesson`: not null;
- encoding dry-run: `0 suspicious rows`.
- database audit report: `docs/DATABASE_AUDIT.md`.
- smoke test: `Smoke test passed`.

## Audit findings

Current stable state:

- One runtime path exists: `scripts/start-neuroteacher.ps1` -> FastAPI + static `frontend/public`.
- Student-facing topics are normalized into 7 modules.
- Raw question topics are preserved inside question data.
- Daily plan is the primary block and links to audio lesson of the day.
- Encoding audit is dry-run only and currently reports no suspicious rows.

Risks to keep visible:

- `database/colombia_exam.db` is modified and should be committed only if the data delta is intentional.
- `frontend/public/legacy-app.bundle.js` is a generated/static bundle. If it becomes the long-term source, document how it is regenerated. If not, keep it as checked-in runtime artifact.
- A future React/Vite migration should be a separate project phase and should recreate source files deliberately instead of reintroducing the removed scaffold by accident.
- The launch script identifies old backend/frontend listeners by command-line heuristics. It should not be used to manage unrelated uvicorn/http.server processes on the same ports.

## Next allowed work

Safe:

- Improve static UI in `frontend/public/study-plan.js` and `frontend/public/audio-library.js`.
- Expand smoke tests around module routing and study plan.

Requires checkpoint:

- Any mass database update.
- Rebuilding or replacing `legacy-app.bundle.js`.
- Migrating back to React/Vite.
- GitHub push.
