# NeuroTeacher

Локальное веб-приложение для подготовки к экзамену на гражданство Колумбии.

## Источник истины

Актуальная архитектура, рабочий запуск, список файлов, правила работы с базой и обязательные проверки зафиксированы в [docs/SOURCE_OF_TRUTH.md](docs/SOURCE_OF_TRUTH.md).

## Запуск

Самый простой запуск в Windows: дважды нажмите `start-neuroteacher.bat` в корне проекта.

Для запуска на телефоне в той же Wi-Fi сети используйте `start-neuroteacher-lan.bat`.

```powershell
powershell -ExecutionPolicy Bypass -File scripts\start-neuroteacher.ps1
```

Приложение открывается на `http://127.0.0.1:5173/`.

API доступен на `http://127.0.0.1:8000/api`.

## Android в той же Wi-Fi сети

```powershell
powershell -ExecutionPolicy Bypass -File scripts\start-neuroteacher.ps1 -Lan
```

Откройте на Android адрес, который скрипт покажет как `Android/LAN URL`. Если телефон не открывает страницу, проверьте Windows Firewall для портов `5173` и `8000`.

Текущий рабочий frontend - static из `frontend/public`. Vite не является основным запуском этого дерева.

В `database/colombia_exam.db` хранится рабочая база вопросов, попыток, материалов и настроек плана. Перед массовыми правками базы нужен backup и dry-run отчет.

## Импорт официальной методички

PDF `data/official_sources/colombia_nuestra_casa.pdf` сохранён локально. Чтобы повторно извлечь текст 190 страниц и индекс глав в SQLite, выполните:

```powershell
cd backend
.\.venv\Scripts\python ..\scripts\import_official_material.py
```

Импортёр не генерирует вопросы и не меняет их статусы: это защищает экзаменационный режим от непроверенных данных.

## Официальный источник данных

Основной источник для будущей базы знаний: [Guía de estudio «Colombia, nuestra casa»](https://www.cancilleria.gov.co/sites/default/files/FOTOS2025/Gu%C3%ADa%20de%20estudio_ajustada.pdf) от Cancillería de Colombia.

### Question generation model

Bulk question generation uses `gpt-5-nano` by default. Override it without
changing the conversational tutor by setting `QUESTION_GENERATION_MODEL` in
`.env`.
