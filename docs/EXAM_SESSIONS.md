# Server-scored practice exams

The static exam component starts a server session and submits selected answers.
The server selects admitted questions, stores a snapshot of the displayed question
and its answer key, and computes the score. Client totals are rejected.

## API

- `POST /api/exams/start`: `{ "exam_format": "D" }` or `"B"`.
  Returns `session_id`, `questions`, `total_questions`, `minutes`, and `started_at`.
  No answer keys or explanations are included in the question response.
- `POST /api/exams/complete`: `{ "session_id": "...", "answers": [
  { "question_id": 123, "answer": "A" } ] }`.
  Returns the saved result ID, server totals, elapsed seconds, and practice threshold.
  An optional nonnegative finite `response_time_seconds` is accepted per answer.
- Omit unanswered questions from `answers`; they remain in the score denominator.
- Same session and same normalized answer set returns the original result.
  Changed answers after completion return 409. Ordering of answers does not matter.
- Duplicate IDs, questions outside the session, invalid choices, and forged totals
  return 422. Unknown session tokens return 404.
- If a selected question loses admission before completion, completion returns 409
  without storing any attempts or exam result. Start a new session.

## Storage and compatibility

`initialize()` adds `exam_runs` and `exam_run_questions` without rewriting old tables.
Completed results still append to `exam_sessions`; submitted answers append to
`attempts` and update `review_queue`. Completion uses one SQLite transaction with
`BEGIN IMMEDIATE`, preventing duplicate writes during concurrent retries.

The session snapshot preserves the answer key presented at start. Existing
`reviewed`, `verified`, and `ai_reviewed` admission policy is unchanged. This does
not imply independent approval of AI-reviewed content.

The former client-total `/api/exams/complete` payload is no longer supported.
Deploy backend and the static bundle together. No migration has been applied to
the restored source database during isolated verification.

Format sizes, thresholds, and minutes retain the existing app configuration.
They have not been newly verified as current official exam rules. The elapsed
duration is measured by the server; this change does not add a server-enforced
deadline or certification features. The app remains a local practice tool.

## Verification

With backend dependencies and `httpx` installed:

```powershell
python scripts/test_question_admission.py
python scripts/test_exam_sessions.py
node scripts/test_exam_frontend.cjs
```

The Python suites use temporary databases. The Node suite checks the actual
checked-in exam component using deterministic hook and HTTP stubs; it does not
replace a browser rendering or full desktop launch check.
