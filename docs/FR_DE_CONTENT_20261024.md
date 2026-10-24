# French and German study content — 2026-10-24

Added complete French and German versions of the existing Colombia exam study content:
646 questions with all A/B/C/D options and explanations per language, plus six full audio lessons per language.

The existing English and Chinese content is retained in the unified data/question-translations.json catalog. The backend rejects stale translations when source questions, options, explanations or keys change. Pending authored translations remain subject to their existing approval rules.

Translations use the configured DeepSeek account and a second automated comparison with the source. They are machine translations for study, not independent editorial approval or official endorsement. Existing facts and legal requirements are translated rather than newly certified.

Spanish example words, verb forms and distractors remain in Spanish. Explicit checks lock the original options for 22 grammar/fill-in exercises. This also restores the original Spanish profession options in Chinese question 752 and original punctuation in question 359.

French audio uses fr-FR-DeniseNeural and German uses de-DE-KatjaNeural. The audio library selects /audio/fr/ or /audio/de/ from the chosen interface language and keeps separate playback state. Original Russian audio and the English/Chinese recordings remain available.

Generation:
- backend/.venv/Scripts/python.exe scripts/build_en_zh_content.py --locales fr de
- The historical generator filename is retained; --locales supports en, zh-Hans, fr and de.
- Completed batches are cached, and final catalogs are merged without replacing other languages.

Validation:
- scripts/check_en_zh_content.py checks all four languages, preserved source hashes, keys and Spanish alternatives.
- scripts/test_question_locales.py checks locale precedence, answer privacy and stale-source fallback.
- scripts/test_en_zh_browser.py checks all four question locales, actual neural speech and translated feedback using a temporary database clone.
- scripts/test_audio_locales_browser.py checks all 24 translated recordings, automatic transitions, stop, separate progress and the mobile language selector.
- Original SQLite questions, answer keys, attempts and learning history are not modified.

The recording checks verify decoding and playback, not full human listening review.
