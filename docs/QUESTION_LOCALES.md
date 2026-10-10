# Question locale contract

Order: `es`, `ru`, `en`, `de`, `fr`, `zh-Hans`. GET `/api/locales` returns this order and native language labels. Unknown locale IDs return 422. Existing clients default to Spanish.

Question lists, study-plan questions, errors, attempts, explanations, bookmarks, due reviews and answers accept `locale`. Exam start accepts the body locale and an optional query override. Keys stay server-side until an answer is submitted; locale projection does not add keys or explanations to question lists or exam starts.

Safe display fields: `requested_locale`, `content_locale`, `translation_available`, `display_question`, `display_options` (A/B/C/D); `display_explanation` only on routes already exposing explanations. Authored translations require `review_status='approved'`; question admission remains the existing status policy. Pending, revoked or malformed translations fall back to the complete canonical Spanish question. Approved option text is matched by stable option IDs to the canonical answer positions, never by translated array order. Authored flat Russian aliases are cleared to prevent stale or pending text bypassing locale review.

Legacy Russian content is used only when the prompt, all four options and explanation exist. Other missing legacy locales fall back to Spanish. This technical approval gate does not independently approve content or translations.

The static frontend persists the language choice, updates document language and forwards it to question API requests, including localhost-to-LAN runtime URLs and Request objects. Core navigation/training/exam UI uses a six-language catalog. Question content is excluded from UI string substitution. Study/review overlays use escaped display fields and an explicit Spanish fallback notice. The old unconditional Russian translation script is no longer loaded.

This is not complete localization of every auxiliary legacy widget. Additional UI labels, content review, TTS and PDF workflows remain open. The core scenario was also checked in an isolated headless Chrome session against a temporary database copy. No external translation service is called.

Validation: 6 locale HTTP cases, 9 exam cases and 5 admission cases; two Node harnesses for the actual frontend components/runtime; syntax and diff checks. A temporary copy of the 793-question candidate returns the same 646 admitted IDs for every locale. All 147 authored questions remain draft and all 882 locale records pending. Original and candidate database hashes remain unchanged. See the application book and locale runtime report for measured coverage.

Browser regression: six language choices and persisted French selection; Spanish fallback rendered once with ES badge; training and review answers display server-projected explanations. Review attaches using the stable data-screen marker instead of translated heading text. A Forma D run with one correct answer and 64 skipped questions recovered from an injected 503 on save; retry retained the same payload, and an identical repeat returned the same result. The temporary copy had exactly three new attempts and one exam result, zero JavaScript page errors; both source database hashes stayed unchanged. Browser QA script and report are in the isolated ColombiaExamQA20261001 directory; no user browser profile or occupied application port was used.


## Auxiliary UI contract (2026-10-10)

`aux-locales.js` registers explicit six-language templates, validates placeholders and exposes `ui`, `dateLocale` and `messageKeys`. Locale changes emit `colombia:locale-changed` only when the choice changes. Study-plan lesson routing uses stable kind IDs; review uses stable screen IDs. Dynamic user and question text is escaped and excluded from catalog substitution.

Plan configuration, lesson headings/counts, review states, audio controls/module titles, calendar tooltips, history date formatting and PDF link labels use the selected interface locale. The 30-day calendar owns a separate container rather than replacing React-owned week elements. Changing the interface locale updates audio labels without replacing the player or its playback position. Audio recordings remain the existing six files; the interface locale does not change their spoken language. PDF choices remain Spanish and Russian; an explicit document choice and page fragment survive interface-language changes.

Regression: `scripts/test_auxiliary_ui_browser.py --candidate PATH --chrome CHROME_PATH --report REPORT_PATH` requires the 147-draft/882-pending candidate, backend dependencies, uvicorn and Playwright. It creates a temporary database and isolated headless browser on OS-assigned loopback ports, blocks external/provider requests, checks all six locales, study/review answers, real muted audio playback and locale preservation, calendar/history, empty review and both PDF HTTP headers. Source database hashes are checked. `scripts/test_locale_frontend.cjs` covers catalog templates, events and date-locale mappings.

These authored UI translations still need independent language review. Full legacy-widget coverage, TTS/provider behavior, audio seeking/resume across reload, and semantic review of recordings/PDFs are outside these checks. Publication and content admission are unchanged.
