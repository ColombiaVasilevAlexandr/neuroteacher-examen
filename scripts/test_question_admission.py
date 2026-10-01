"""HTTP regression checks; all writes use a temporary SQLite database.

Run with the backend dependencies and httpx installed:
    python scripts/test_question_admission.py
"""
import gc
import sys
import tempfile
import unittest
from datetime import date, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / 'backend'))
import main
from fastapi.testclient import TestClient


class QuestionAdmissionTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.original_path = main.DB_PATH
        main.DB_PATH = Path(self.temp.name) / 'test.db'
        self.client = TestClient(main.app)
        self.client.__enter__()
        self.admitted = {1, 2, 3}
        self.blocked = {4, 5, 6, 7, 8}
        with main.conn() as db:
            db.execute('DELETE FROM questions')
            for question_id, status in enumerate(('reviewed', 'verified', 'ai_reviewed',
                    'draft', 'pending', 'rejected', 'archived', 'unknown'), 1):
                marker = 'admitted' if question_id in self.admitted else 'withheld'
                topic = 'Geografía' if question_id in self.admitted else 'hidden-topic'
                db.execute('''INSERT INTO questions(id, question_es, answer_a, answer_b,
                    answer_c, answer_d, correct_answer, topic, explanation_es,
                    explanation_ru, status) VALUES(?,?, 'A', 'B', 'C', 'D', 'A', ?,?,?,?)''',
                    (question_id, f'{marker}-{question_id}', topic,
                     f'{marker}-explanation', f'{marker}-explanation', status))
                for correct in (0, 1):
                    db.execute('INSERT INTO attempts(question_id,answer,correct) VALUES(?,?,?)',
                               (question_id, 'A' if correct else 'B', correct))
                db.execute('INSERT INTO bookmarks(question_id) VALUES(?)', (question_id,))
                db.execute("INSERT INTO review_queue(question_id,due_at,step) VALUES(?,date('now','localtime'),0)", (question_id,))

    def tearDown(self):
        self.client.__exit__(None, None, None)
        main.DB_PATH = self.original_path
        gc.collect()  # Release SQLite connections before Windows removes the temp file.
        self.temp.cleanup()

    def get(self, path, **params):
        response = self.client.get(path, params=params)
        self.assertEqual(response.status_code, 200, response.text)
        self.assertNotIn('withheld', response.text)
        self.assertNotIn('hidden-topic', response.text)
        return response.json()

    def state(self):
        with main.conn() as db:
            return tuple(tuple(tuple(row) for row in db.execute(f'SELECT * FROM {table} ORDER BY 1'))
                         for table in ('attempts', 'bookmarks', 'review_queue'))

    def test_all_question_lists_hide_blocked_statuses(self):
        for path in ('/api/questions', '/api/explanations', '/api/bookmarks',
                     '/api/review/due', '/api/errors'):
            with self.subTest(path=path):
                rows = self.get(path, limit=50)
                self.assertEqual({row['id'] for row in rows}, self.admitted)
        self.assertEqual({row['id'] for row in self.get('/api/questions', topic='География')}, self.admitted)
        self.assertEqual(self.get('/api/questions', topic='hidden-topic'), [])
        self.assertEqual({row['id'] for row in self.get('/api/questions', exclude='1,2')}, {3})
        for correct_only in (False, True):
            rows = self.get('/api/attempts', correct_only=correct_only)
            self.assertEqual({row['question_id'] for row in rows}, self.admitted)
            self.assertEqual(len(rows), 3 if correct_only else 6)
        plan = self.get('/api/study-plan/questions', limit=50)
        self.assertEqual({row['id'] for row in plan['questions']}, self.admitted)
        self.assertEqual(plan['due_reviews'], 3)

    def test_counts_and_plans_use_the_same_admission_policy(self):
        deadline = (date.today() + timedelta(days=30)).isoformat()
        for path in ('/api/study-plan', '/api/study-plan/today'):
            plan = self.get(path, exam_date=deadline)
            self.assertEqual(plan['total_available'], 3)
            self.assertEqual(plan['daily_reviews'], 3)
        formats = self.get('/api/exams/formats')
        self.assertEqual(formats['available_questions'], 3)
        self.assertEqual(formats['verified_questions'], 1)
        dashboard = self.get('/api/dashboard')
        self.assertEqual(dashboard['due_reviews'], 3)
        self.assertEqual(sum(row['count'] for row in dashboard['topic_counts']), 3)
        self.assertEqual(dashboard['attempts'], 16)  # Historical totals are retained.
        self.assertEqual(self.get('/api/topics/weak')[0]['attempts'], 6)

    def test_blocked_direct_ids_return_404_without_history_writes(self):
        before = self.state()
        for question_id in self.blocked | {999}:
            for path, payload in ((f'/api/questions/{question_id}/answer', {'answer': 'A'}),
                                  (f'/api/bookmarks/{question_id}', None)):
                with self.subTest(path=path):
                    response = self.client.post(path, json=payload)
                    self.assertEqual(response.status_code, 404, response.text)
                    self.assertNotIn('withheld', response.text)
        self.assertEqual(before, self.state())

    def test_admitted_answers_and_bookmarks_still_work(self):
        for question_id in self.admitted:
            with self.subTest(question_id=question_id):
                response = self.client.post(f'/api/questions/{question_id}/answer',
                                            json={'answer': 'a', 'response_time_seconds': 2.5})
                self.assertEqual(response.status_code, 200, response.text)
                self.assertTrue(response.json()['correct'])
                self.assertEqual(response.json()['correct_answer'], 'A')
                self.assertEqual(self.client.delete(f'/api/bookmarks/{question_id}').status_code, 200)
                self.assertEqual(self.client.post(f'/api/bookmarks/{question_id}').status_code, 200)
        with main.conn() as db:
            self.assertEqual(db.execute('SELECT COUNT(*) FROM attempts').fetchone()[0], 19)

    def test_revocation_hides_existing_history_without_deleting_it(self):
        with main.conn() as db:
            db.execute("UPDATE questions SET status='draft' WHERE id=1")
        before = self.state()
        self.admitted.remove(1)
        self.assert_question_lists_follow_current_status()
        self.assertEqual(self.client.post('/api/questions/1/answer', json={'answer': 'A'}).status_code, 404)
        self.assertEqual(self.client.post('/api/bookmarks/1').status_code, 404)
        self.assertEqual(before, self.state())
        # Removing an old bookmark remains possible after content is withheld.
        self.assertEqual(self.client.delete('/api/bookmarks/1').status_code, 200)

    def assert_question_lists_follow_current_status(self):
        # Also run on the initial fixture; exercise the same lists after revocation.
        for path in ('/api/questions', '/api/explanations', '/api/bookmarks', '/api/review/due', '/api/errors'):
            self.assertEqual({row['id'] for row in self.get(path)}, self.admitted)
        self.assertEqual({row['question_id'] for row in self.get('/api/attempts')}, self.admitted)


if __name__ == '__main__':
    unittest.main(verbosity=2)
