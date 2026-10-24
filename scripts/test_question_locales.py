"""Locale HTTP regression checks, with approval fixtures confined to temp DBs."""
import json, unittest
from test_question_admission import QuestionAdmissionTests, main

class QuestionLocaleTests(unittest.TestCase):
    setUp=QuestionAdmissionTests.setUp
    tearDown=QuestionAdmissionTests.tearDown

    def fixture(self):
        with main.conn() as db:
            db.executescript('''CREATE TABLE authored_imports(external_id TEXT PRIMARY KEY,question_id INTEGER,payload_json TEXT);
                CREATE TABLE authored_localizations(external_id TEXT,locale TEXT,prompt TEXT,options_json TEXT,
                explanation TEXT,review_status TEXT,PRIMARY KEY(external_id,locale));''')
            db.execute('INSERT INTO authored_imports VALUES(?,?,?)',('fixture',1,json.dumps({'options':[{'id':k} for k in 'ABCD']})))
            db.execute("UPDATE questions SET question_ru='PRIVATE RU' WHERE id=1")
            for locale in main.LOCALES:
                choices=[{'id':k,'text':'PRIVATE '+locale+' '+k} for k in 'ABCD']
                db.execute('INSERT INTO authored_localizations VALUES(?,?,?,?,?,?)',
                    ('fixture',locale,'PRIVATE prompt',json.dumps(choices),'PRIVATE explanation','pending'))

    def approve(self,locale):
        choices=[{'id':k,'text':locale+' '+k} for k in reversed('ABCD')]
        with main.conn() as db:
            db.execute("UPDATE authored_localizations SET prompt=?,options_json=?,explanation=?,review_status='approved' WHERE locale=?",
                       (locale+' prompt',json.dumps(choices),locale+' explanation',locale))

    def get_question(self,locale,path='/api/questions'):
        response=self.client.get(path,params={'locale':locale})
        self.assertEqual(response.status_code,200,response.text)
        self.assertNotIn('PRIVATE',response.text)
        rows=response.json()['questions'] if path.endswith('study-plan/questions') else response.json()
        return next(q for q in rows if q.get('question_id',q.get('id'))==1)

    def test_order_and_pending_fallback(self):
        self.fixture()
        self.assertEqual([r['id'] for r in self.client.get('/api/locales').json()],['es','ru','en','de','fr','zh-Hans'])
        for locale in main.LOCALES:
            q=self.get_question(locale)
            self.assertEqual((q['requested_locale'],q['content_locale']),(locale,'es'))
            self.assertIsNone(q['question_ru'])
            self.assertEqual(q['translation_available'],locale=='es')
            self.assertNotIn('display_explanation',q)
            self.assertNotIn('correct_answer',q)

    def test_approved_option_ids_and_explanations(self):
        self.fixture()
        for locale in main.LOCALES[1:]:
            self.approve(locale)
            q=self.get_question(locale)
            self.assertEqual(q['display_question'],locale+' prompt')
            self.assertEqual(q['display_options'],{k:locale+' '+k for k in 'ABCD'})
            response=self.client.post('/api/questions/1/answer',params={'locale':locale},json={'answer':'A'})
            self.assertTrue(response.json()['correct'])
            self.assertEqual(response.json()['display_explanation'],locale+' explanation')

    def test_each_question_route_projects_locale(self):
        self.fixture();self.approve('fr')
        for path in ('/api/questions','/api/errors','/api/attempts','/api/explanations','/api/bookmarks','/api/review/due','/api/study-plan/questions'):
            self.assertEqual(self.get_question('fr',path)['display_question'],'fr prompt')

    def test_exam_locale_and_key_privacy(self):
        self.fixture();self.approve('zh-Hans')
        response=self.client.post('/api/exams/start',params={'locale':'zh-Hans'},json={'exam_format':'D'})
        self.assertEqual(response.status_code,200,response.text)
        q=next(q for q in response.json()['questions'] if q['id']==1)
        self.assertEqual(q['display_question'],'zh-Hans prompt')
        self.assertNotIn('correct_answer',q)
        self.assertNotIn('display_explanation',q)

    def test_malformed_and_revoked_locale_fall_back(self):
        self.fixture();self.approve('en')
        with main.conn() as db:db.execute("UPDATE authored_localizations SET options_json='[]' WHERE locale='en'")
        self.assertEqual(self.get_question('en')['content_locale'],'es')
        self.approve('en')
        with main.conn() as db:db.execute("UPDATE authored_localizations SET review_status='pending' WHERE locale='en'")
        self.assertEqual(self.get_question('en')['content_locale'],'es')

    def test_legacy_ru_and_unknown_locale(self):
        with main.conn() as db:
            db.execute("UPDATE questions SET question_ru='RU prompt',answer_a_ru='RU A',answer_b_ru='RU B',answer_c_ru='RU C',answer_d_ru='RU D' WHERE id=1")
        self.assertEqual(self.get_question('ru')['content_locale'],'ru')
        with main.conn() as db:db.execute('UPDATE questions SET answer_d_ru=NULL WHERE id=1')
        self.assertEqual(self.get_question('ru')['content_locale'],'es')
        self.assertEqual(self.client.get('/api/questions',params={'locale':'xx'}).status_code,422)

    def test_learning_translation_hash_and_key_privacy(self):
        import tempfile
        from pathlib import Path
        from unittest.mock import patch
        import question_locales
        with main.conn() as db:
            question = dict(db.execute("SELECT * FROM questions WHERE id=1").fetchone())
        translated = {'question': 'Translated study question', 'options': {k:'choice '+k for k in 'ABCD'},
                      'explanation': 'Translated explanation', 'correct_answer':question['correct_answer'],
                      'translation_method':'machine_translation_with_second_pass',
                      'source_hash':question_locales.translation_source_hash(question)}
        locales = ('en','zh-Hans','fr','de')
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder)/'translations.json'
            path.write_text(json.dumps({'locales':{locale:{'1':translated} for locale in locales}}),encoding='utf-8')
            with patch.object(question_locales,'TRANSLATION_FILE',path):
                for locale in locales:
                    with self.subTest(locale=locale):
                        item = self.get_question(locale)
                        self.assertEqual(item['display_question'],translated['question'])
                        self.assertEqual(item['content_locale'],locale)
                        self.assertNotIn('correct_answer',item)
                        self.assertNotIn('display_explanation',item)
                        response=self.client.post('/api/questions/1/answer',params={'locale':locale},
                                                  json={'answer':question['correct_answer']})
                        self.assertEqual(response.json()['display_explanation'],translated['explanation'])
                with main.conn() as db:
                    db.execute("UPDATE questions SET question_es=question_es||' changed' WHERE id=1")
                for locale in locales:
                    self.assertEqual(self.get_question(locale)['content_locale'],'es')

if __name__=='__main__':
    unittest.main(defaultTest='QuestionLocaleTests',verbosity=2)
