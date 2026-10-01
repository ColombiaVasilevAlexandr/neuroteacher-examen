"""Server-scored exam HTTP tests; uses temporary SQLite files only."""
import gc
import sys
import tempfile
import unittest
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / 'backend'))
import main
from fastapi.testclient import TestClient


class ExamSessionTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.original_path = main.DB_PATH
        main.DB_PATH = Path(self.temp.name) / 'exam.db'
        self.client = TestClient(main.app)
        self.client.__enter__()
        with main.conn() as db:
            db.execute("UPDATE questions SET status=CASE WHEN id<=3 THEN 'reviewed' ELSE 'draft' END")

    def tearDown(self):
        self.client.__exit__(None, None, None)
        main.DB_PATH = self.original_path
        gc.collect()
        self.temp.cleanup()

    def start(self, exam_format='D'):
        response = self.client.post('/api/exams/start', json={'exam_format': exam_format})
        self.assertEqual(response.status_code, 200, response.text)
        return response.json()

    def counts(self):
        with main.conn() as db:
            return tuple(db.execute('SELECT COUNT(*) FROM '+table).fetchone()[0]
                         for table in ('attempts','review_queue','exam_sessions','exam_runs'))

    def complete(self, run, answers):
        return self.client.post('/api/exams/complete', json={'session_id': run['session_id'], 'answers': answers})

    def test_start_selects_only_admitted_questions_and_hides_keys(self):
        run = self.start()
        self.assertEqual({q['id'] for q in run['questions']}, {1, 2, 3})
        self.assertEqual(run['total_questions'], 3)
        for question in run['questions']:
            self.assertNotIn('correct_answer', question)
            self.assertNotIn('explanation_es', question)
        self.assertEqual(self.counts(), (0, 0, 0, 1))

    def test_score_comes_from_keys_and_unanswered_questions_count(self):
        run = self.start()
        response = self.complete(run, [{'question_id': 1, 'answer': 'A'}, {'question_id': 2, 'answer': 'B'}])
        self.assertEqual(response.status_code, 200, response.text)
        result = response.json()
        self.assertEqual((result['correct_answers'],result['total_questions']), (1, 3))
        self.assertEqual(result['passing_score'], 2)
        self.assertFalse(result['passed'])
        self.assertGreaterEqual(result['duration_seconds'], 0)
        self.assertEqual(self.counts(), (2, 2, 1, 1))
        with main.conn() as db:
            self.assertEqual(tuple(db.execute('SELECT total_questions,correct_answers FROM exam_sessions').fetchone()), (3, 1))

    def test_retry_and_concurrent_completion_save_history_once(self):
        run = self.start()
        answers = [{'question_id': 1, 'answer': 'A'}, {'question_id': 2, 'answer': 'B'}]
        with ThreadPoolExecutor(max_workers=2) as pool:
            responses = list(pool.map(lambda _: self.complete(run, answers), range(2)))
        self.assertEqual([r.status_code for r in responses], [200, 200])
        self.assertEqual(responses[0].json(), responses[1].json())
        retry = self.complete(run, list(reversed(answers)))
        self.assertEqual(retry.json(), responses[0].json())
        self.assertEqual(self.counts(), (2, 2, 1, 1))
        conflict = self.complete(run, [{'question_id': 1, 'answer': 'B'}])
        self.assertEqual(conflict.status_code, 409)
        self.assertEqual(self.counts(), (2, 2, 1, 1))

    def test_forged_totals_foreign_ids_and_duplicate_ids_are_rejected(self):
        run = self.start()
        before = self.counts()
        forged = self.client.post('/api/exams/complete', json={
            'session_id': run['session_id'], 'answers': [], 'correct_answers': 999, 'total_questions': 999})
        self.assertEqual(forged.status_code, 422)
        for answers in ([{'question_id': 4, 'answer': 'A'}],
                        [{'question_id': 1, 'answer': 'A'}, {'question_id': 1, 'answer': 'A'}]):
            self.assertEqual(self.complete(run, answers).status_code, 422)
        self.assertEqual(self.complete({'session_id': 'missing'}, []).status_code, 404)
        self.assertEqual(self.counts(), before)

    def test_revoked_question_rolls_back_the_entire_completion(self):
        run = self.start()
        with main.conn() as db:
            db.execute("UPDATE questions SET status='draft' WHERE id=3")
        before = self.counts()
        response = self.complete(run, [{'question_id': 1, 'answer': 'A'}])
        self.assertEqual(response.status_code, 409)
        self.assertEqual(self.counts(), before)

    def test_snapshot_key_survives_bank_changes_and_result_survives_restart(self):
        run = self.start()
        with main.conn() as db:
            db.execute("UPDATE questions SET correct_answer='B' WHERE id=1")
        result = self.complete(run, [{'question_id': 1, 'answer': 'A'}])
        self.assertEqual(result.status_code, 200)
        self.assertEqual(result.json()['correct_answers'], 1)
        self.client.__exit__(None, None, None)
        self.client = TestClient(main.app)
        self.client.__enter__()
        self.assertEqual(self.complete(run, [{'question_id': 1, 'answer': 'A'}]).json(), result.json())
        self.assertEqual(self.counts(), (1, 1, 1, 1))

    def test_validation_rejects_bad_answers_times_and_formats(self):
        run = self.start()
        before = self.counts()
        for value in ('', 'E', 'AB', None, 1):
            self.assertEqual(self.complete(run, [{'question_id': 1, 'answer': value}]).status_code, 422)
            self.assertEqual(self.client.post('/api/questions/1/answer', json={'answer': value}).status_code, 422)
        for seconds in (-1, 'NaN', 'Infinity'):
            payload = {'question_id': 1, 'answer': 'A', 'response_time_seconds': seconds}
            self.assertEqual(self.complete(run, [payload]).status_code, 422)
            self.assertEqual(self.client.post('/api/questions/1/answer', json={
                'answer': 'A', 'response_time_seconds': seconds}).status_code, 422)
        self.assertEqual(self.client.post('/api/exams/start', json={'exam_format': 'unknown'}).status_code, 422)
        self.assertEqual(self.counts(), before)

    def test_no_admitted_questions_does_not_create_a_session(self):
        with main.conn() as db:
            db.execute("UPDATE questions SET status='draft'")
        self.assertEqual(self.client.post('/api/exams/start', json={'exam_format': 'D'}).status_code, 409)
        self.assertEqual(self.counts(), (0, 0, 0, 0))

    def test_full_format_limits_and_empty_completion(self):
        with main.conn() as db:
            db.execute("UPDATE questions SET status='reviewed'")
            for question_id in range(21, 91):
                db.execute('''INSERT INTO questions(id,question_es,answer_a,answer_b,answer_c,answer_d,
                    correct_answer,topic,explanation_es,status)
                    VALUES(?,'Fixture','A','B','C','D','A','Geografía','Fixture','reviewed')''', (question_id,))
        for exam_format, count in (('D', 65), ('B', 75)):
            run = self.start(exam_format)
            self.assertEqual(len(run['questions']), count)
            self.assertEqual(len({q['id'] for q in run['questions']}), count)
            response = self.complete(run, [])
            self.assertEqual(response.status_code, 200)
            self.assertEqual((response.json()['total_questions'], response.json()['correct_answers']), (count, 0))
        self.assertEqual(self.counts(), (0, 0, 2, 2))


if __name__ == '__main__':
    unittest.main(verbosity=2)
