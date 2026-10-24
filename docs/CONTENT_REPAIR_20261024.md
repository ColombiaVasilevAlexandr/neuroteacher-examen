# Content and source repair — 24 October 2026

The Spanish 2024 guide (190 pages) and the archived Russian translation of the
2021 guide (179 pages) use separate source IDs. Question references and the
reader's chapter navigation follow the selected edition. Switching to another
edition opens its first page instead of reusing an unrelated page number.

The migration preserves question IDs, answer keys, attempts, bookmarks, review
dates and exam history. It does not promote AI-reviewed content to verified.

Apply with the application's Python:
```
python scripts/repair_question_content.py --db database/colombia_exam.db --apply
python scripts/check_content_catalog.py --db database/colombia_exam.db
```

The migration creates a SQLite backup before any writes. Without --apply, the
transaction is rolled back. Reference matching checks evidence provenance; it
does not constitute independent editorial approval of every answer.

Importing source text defaults to the Spanish edition. The archived Russian
edition requires --locale ru and is stored under source 2, preserving source 1.
