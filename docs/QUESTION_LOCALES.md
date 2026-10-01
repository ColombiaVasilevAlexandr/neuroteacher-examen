# Question locale contract

Order: `es`, `ru`, `en`, `de`, `fr`, `zh-Hans`. GET `/api/locales` returns this order and native language labels. Unknown locale IDs return 422. Existing clients default to Spanish.

Question lists, study-plan questions, errors, attempts, explanations, bookmarks, due reviews and answers accept `locale`. Exam start accepts the body locale and an optional query override. Keys stay server-side until an answer is submitted; locale projection does not add keys or explanations to question lists or exam starts.

Safe display fields: `requested_locale`, `content_locale`, `translation_available`, `display_question`, `display_options` (A/B/C/D); `display_explanation` only on routes already exposing explanations. Authored translations require `review_status='approved'`; question admission remains the existing status policy. Pending, revoked or malformed translations fall back to the complete canonical Spanish question. Approved option text is matched by stable option IDs to the canonical answer positions, never by translated array order. Authored flat Russian aliases are cleared to prevent stale or pending text bypassing locale review.

Legacy Russian content is used only when the prompt, all four options and explanation exist. Other missing legacy locales fall back to Spanish. This technical approval gate does not independently approve content or translations.

The static frontend persists the language choice, updates document language and forwards it to question API requests, including localhost-to-LAN runtime URLs and Request objects. Core navigation/training/exam UI uses a six-language catalog. Question content is excluded from UI string substitution. Study/review overlays use escaped display fields and an explicit Spanish fallback notice. The old unconditional Russian translation script is no longer loaded.

This is not complete localization of every auxiliary legacy widget. Additional UI labels, content review, real browser rendering, TTS and PDF workflows remain open. No external translation service is called.

Validation: 6 locale HTTP cases, 9 exam cases and 5 admission cases; two Node harnesses for the actual frontend components/runtime; syntax and diff checks. A temporary copy of the 793-question candidate returns the same 646 admitted IDs for every locale. All 147 authored questions remain draft and all 882 locale records pending. Original and candidate database hashes remain unchanged. See the application book and locale runtime report for measured coverage.
