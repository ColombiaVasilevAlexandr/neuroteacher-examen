# NeuroTeacher

Локальное веб-приложение для подготовки к экзамену на гражданство Колумбии.

## Что готово

- Адаптивный React-интерфейс стартового экрана в тёмной неоновой стилистике.
- Навигация, план занятия, прогресс, статистика и быстрые действия на моковых данных.
- Архитектурное направление: React + FastAPI + SQLite; без Docker и локальных моделей на первом этапе.

## Запуск интерфейса

```powershell
cd frontend
npm install
npm run dev
```

Откройте адрес, который покажет Vite (обычно `http://localhost:5173`).

## Запуск API и базы

```powershell
cd backend
.\.venv\Scripts\Activate.ps1
uvicorn main:app --reload
```

API будет доступен по адресу `http://127.0.0.1:8000`, а документация — по `http://127.0.0.1:8000/docs`.

В `database/colombia_exam.db` создаются таблицы источников, вопросов и попыток. В стартовой базе 20 тренировочных вопросов. Их статус — `reviewed`: перед попаданием в будущий экзаменационный режим каждый вопрос должен быть сверён с методичкой и переведён в `verified`.

## Импорт официальной методички

PDF `data/official_sources/colombia_nuestra_casa.pdf` сохранён локально. Чтобы повторно извлечь текст 190 страниц и индекс глав в SQLite, выполните:

```powershell
cd backend
.\.venv\Scripts\python ..\scripts\import_official_material.py
```

Импортёр не генерирует вопросы и не меняет их статусы: это защищает экзаменационный режим от непроверенных данных.

## Официальный источник данных

Основной источник для будущей базы знаний: [Guía de estudio «Colombia, nuestra casa»](https://www.cancilleria.gov.co/sites/default/files/FOTOS2025/Gu%C3%ADa%20de%20estudio_ajustada.pdf) от Cancillería de Colombia.

Следующий этап — добавить FastAPI, SQLite и импортёр PDF, который создаёт материалы для проверки, но не публикует автоматически сгенерированные вопросы как верифицированные.
### Question generation model

Bulk question generation uses `gpt-5-nano` by default. Override it without
changing the conversational tutor by setting `QUESTION_GENERATION_MODEL` in
`.env`.
