# English and Simplified Chinese study content — 2026-10-24

The installed Colombia exam application has English and Simplified Chinese translations of all 646 existing practice questions, options and explanations, plus six full audio lessons per language.

- Translation uses the configured DeepSeek account and a second automated comparison with the source.
- This is machine translation for private study. No independent pedagogical approval or official endorsement is inferred.
- Spanish example words, verb forms and intentionally incorrect alternatives in grammar exercises stay in Spanish.
- Original IDs, A/B/C/D answer keys, source references and SQLite history are unchanged.
- The backend serves a translation only when its checksum matches the current source question, options, explanation and key.
- Authored question approval rules retain precedence; this catalog does not approve pending authored translations.
- Question lists never expose answer keys or explanations before an answer.
- English audio routes to /audio/en/ and Chinese to /audio/zh-Hans/. Progress is separate per language.
- Russian recordings remain available; other interface locales show the recording's actual Russian language.
- Translation does not assert that all source facts or legal requirements have been independently reverified.

Generation: run scripts/build_en_zh_content.py with backend dependencies and the existing ignored .env.
Completed batches and recordings are reused; source changes invalidate cached question batches.
Intermediate checkpoints are ignored; the final catalog, scripts and audio are tracked.

Validation:
- scripts/check_en_zh_content.py checks completeness, source hashes and preserved keys.
- scripts/test_question_locales.py checks locale rules, key privacy and stale-source fallback.
- scripts/test_speech_runtime.cjs checks cancellation and English/Chinese voice routing.
- scripts/test_en_zh_browser.py clones SQLite into a temporary directory, checks both question locales, plays real neural question audio and submits answers only in that clone. The original database hash must remain unchanged.

All twelve audio recordings were opened, decoded and played in Chrome. Locale switching, separate progress and absence of autoplay were checked. This is a playback check, not a full human listening review.
