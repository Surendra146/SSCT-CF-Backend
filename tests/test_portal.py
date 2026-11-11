import unittest, tempfile, asyncio, time, hashlib, os
from pathlib import Path
from fastapi.testclient import TestClient
from app.main import app
from app.core import db
from app.core.auth import hash_password

class PortalTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.old=db.LOCAL_DB; db.LOCAL_DB=str(Path(self.tmp.name)/'portal.sqlite3')
        self.client=TestClient(app);self.client.__enter__()
        asyncio.run(db.execute('INSERT OR REPLACE INTO admin_users(id,username,password_hash,name) VALUES(100,?,?,?)',('test-admin',hash_password('test-pass-12345'),'Test Admin')))
        self.headers={'Origin':'http://localhost:5173'}
    def tearDown(self):
        self.client.__exit__(None,None,None);db.LOCAL_DB=self.old;self.tmp.cleanup()
    def login(self):
        r=self.client.post('/api/admin/auth/login',json={'username':'test-admin','password':'test-pass-12345'},headers=self.headers)
        self.assertEqual(r.status_code,200,r.text)
        self.headers['X-CSRF-Token']=r.json()['csrf'];return r
    def post(self,path,data):return self.client.post('/api/admin/'+path,json=data,headers=self.headers)
    def patch(self,path,data):return self.client.patch('/api/admin/'+path,json=data,headers=self.headers)
    def program(self,id='test-program',status='published'):
        return dict(id=id,name='Test Program',status=status,course_id='python-full-stack',description='Test schedule only',duration='6 weeks',start_date='2099-01-01',end_date='2099-02-01',branch='Tarnaka',training_mode='Offline',start_time='10:00',end_time='12:00',schedule_days=['Monday'],skills_learned=['Python','SQL'])
    def registration(self,**updates):
        return dict(full_name='Test Student',mobile='9876543210',email='',preferred_branch='Tarnaka',qualification='B',course_id='python-full-stack',preferred_batch='Weekday morning',training_mode='Classroom',message='Test registration',consent=True,**updates)
    def test_security(self):
        for path in ('registrations','enquiries','courses','batches','internships','settings','dashboard/summary','internship-applications'):
            self.assertEqual(self.client.get('/api/admin/'+path).status_code,401)
            if path in ('registrations','enquiries','courses','batches','internships'):
                self.assertEqual(self.client.post('/api/admin/'+path,json={}).status_code,401)
        self.assertEqual(self.client.post('/api/admin/auth/login',json={'username':'test-admin','password':'wrong'},headers={'Origin':'https://evil.test'}).status_code,403)
        r=self.login();self.assertIn('HttpOnly',r.headers['set-cookie']);self.assertNotIn('token',r.json())
        self.assertEqual(self.client.get('/api/admin/auth/me').json()['role'],'admin')
        self.assertEqual(self.client.post('/api/admin/courses',json={'id':'bad','name':'bad'}).status_code,403)
        self.assertEqual(self.client.get('/api/admin/registrations').headers['cache-control'],'no-store')
        self.client.post('/api/admin/auth/logout',headers=self.headers)
        self.assertEqual(self.client.get('/api/admin/auth/me').status_code,401)
    def test_password_settings_and_session_revocation(self):
        self.login()
        original=self.client.cookies.get('ssct_admin_session')
        self.assertEqual(self.patch('settings',{'name':'Changed Name','current_password':'wrong','new_password':'new-password-12345'}).status_code,400)
        self.assertEqual(self.client.get('/api/admin/auth/me').json()['name'],'Test Admin')
        self.assertEqual(self.patch('settings',{'name':'Changed Name','current_password':'test-pass-12345','new_password':'new-password-12345'}).status_code,200)
        stored=asyncio.run(db.rows('SELECT password_hash FROM admin_users WHERE username=?',('test-admin',)))[0]['password_hash']
        self.assertTrue(stored.startswith('pbkdf2_sha256$600000$'));self.assertNotIn('new-password',stored)
        self.client.post('/api/admin/auth/logout',headers=self.headers)
        self.client.cookies.set('ssct_admin_session',original,domain='testserver.local',path='/api/admin')
        self.assertEqual(self.client.get('/api/admin/auth/me').status_code,401)

    def test_rate_limit(self):
        for i in range(5):
            self.assertEqual(self.client.post('/api/admin/auth/login',json={'username':'test-admin','password':'wrong'}).status_code,401)
        self.assertEqual(self.client.post('/api/admin/auth/login',json={'username':'test-admin','password':'test-pass-12345'}).status_code,429)
    def test_expiry(self):
        self.login();asyncio.run(db.execute('UPDATE admin_sessions SET last_seen=?',(int(time.time())-1000,)))
        self.assertEqual(self.client.get('/api/admin/auth/me').status_code,401)
        self.assertEqual(len(asyncio.run(db.rows('SELECT * FROM admin_sessions'))),0)
    def test_catalog_and_public_visibility(self):
        self.assertEqual(len(self.client.get('/api/courses').json()['items']),78)
        self.login()
        course={'id':'new-real-course','name':'New Course','status':'draft','description':'A new course','categories':['it'],'tags':['Python']}
        self.assertEqual(self.post('courses',course).status_code,201)
        self.assertEqual(self.client.get('/api/courses/new-real-course').status_code,404)
        self.assertEqual(self.patch('courses/new-real-course',{'status':'published'}).status_code,200)
        self.assertEqual(self.client.get('/api/courses/new-real-course').status_code,200)
        self.assertEqual(self.patch('courses/new-real-course',{'name':'Updated Course'}).status_code,200)
        self.assertEqual(self.client.get('/api/courses/new-real-course').json()['name'],'Updated Course')
        self.client.delete('/api/admin/courses/new-real-course',headers=self.headers)
        self.assertEqual(self.client.get('/api/courses/new-real-course').status_code,404)
        self.assertEqual(self.client.get('/api/enquiries').status_code,404)
    def test_programs_and_applications(self):
        self.login()
        for kind in ('batches','internships'):
            self.assertEqual(self.post(kind,self.program()).status_code,201)
            listed=self.client.get('/api/'+kind).json()['items'];self.assertEqual(len(listed),1);self.assertEqual(listed[0]['lifecycle'],'upcoming')
            field='batch_id' if kind=='batches' else 'internship_id'
            path='/api/registrations' if kind=='batches' else '/api/internship-applications'
            r=self.client.post(path,json=self.registration(**{field:'test-program'}));self.assertEqual(r.status_code,201,r.text)
            self.assertEqual(self.patch(kind+'/test-program',{'applications_open':False,'skills_learned':['FastAPI'],'duration':'8 weeks'}).status_code,200)
            self.assertEqual(self.client.get('/api/'+kind+'/test-program').json()['duration'],'8 weeks')
            self.assertEqual(self.client.post(path,json=self.registration(**{field:'test-program'})).status_code,409)
            self.assertEqual(self.patch(kind+'/test-program',{'status':'draft'}).status_code,200)
            self.assertEqual(len(self.client.get('/api/'+kind).json()['items']),0)
        apps=self.client.get('/api/admin/internship-applications').json()['items'];self.assertEqual(len(apps),1)
        self.assertEqual(self.patch('internship-applications/'+str(apps[0]['id']),{'status':'Contacted'}).status_code,200)
    def test_current_program_and_cancelled_applications(self):
        from datetime import timedelta
        from app.core.content import today
        self.login()
        program={**self.program('current-program'),'start_date':str(today()-timedelta(days=2)),'end_date':str(today()+timedelta(days=7))}
        self.assertEqual(self.post('internships',program).status_code,201)
        self.assertEqual(self.client.get('/api/internships/current-program').json()['lifecycle'],'current')
        self.assertEqual(self.patch('internships/current-program',{'status':'cancelled'}).status_code,200)
        self.assertEqual(self.client.post('/api/internship-applications',json=self.registration(internship_id='current-program')).status_code,404)

    def test_legacy_database_preserved(self):
        import sqlite3
        from contextlib import closing
        previous=db.LOCAL_DB
        try:
            db.LOCAL_DB=str(Path(self.tmp.name)/'legacy.sqlite3')
            with closing(sqlite3.connect(db.LOCAL_DB)) as conn:
                conn.executescript(Path('migrations/0001_init.sql').read_text())
                conn.execute("INSERT INTO registrations(id,full_name,mobile,email,city,qualification,course_id,preferred_batch,training_mode) VALUES(41,'Historical Student','9876543210','','Tarnaka','Graduate','dotnet-full-stack','Weekend','Offline')")
                conn.commit()
            db.init_local()
            record=asyncio.run(db.rows('SELECT * FROM registrations WHERE id=41'))[0]
            self.assertEqual(record['full_name'],'Historical Student')
            self.assertEqual(record['course_id'],'dotnet-full-stack')
            self.assertEqual(record['message'],'')
            self.assertEqual(len(asyncio.run(db.rows('SELECT * FROM courses'))),78)
        finally:db.LOCAL_DB=previous

    def test_validation(self):
        self.login()
        for changes in ({'end_date':'2098-01-01'},{'end_time':'09:00'},{'available_seats':-1},{'course_id':'missing'},{'branch':''}):
            r=self.post('batches',{**self.program(),**changes});self.assertIn(r.status_code,(422,404),r.text)
        self.assertEqual(self.post('courses',{'id':'same','name':'Same'}).status_code,201)
        self.assertEqual(self.post('courses',{'id':'same','name':'Same'}).status_code,409)
        self.assertEqual(self.post('unknown',{'id':'safe','name':'Safe'}).status_code,404)
    def test_records_export_stats_migrations(self):
        self.login()
        r=self.client.post('/api/registrations',json=self.registration());self.assertEqual(r.status_code,201,r.text);id=r.json()['id']
        self.assertEqual(self.patch('registrations/'+str(id),{'status':'Contacted','admin_notes':'Call tomorrow','full_name':'Updated Student'}).status_code,200)
        self.assertEqual(self.client.get('/api/admin/registrations?q=Updated').json()['total'],1)
        self.assertEqual(self.client.get('/api/admin/registrations?q=absent').json()['total'],0)
        r=self.post('enquiries',{'name':'Enquiry Test','mobile':'9876543210','email':'','message':'Please call me','source':'batch'});self.assertEqual(r.status_code,201,r.text)
        eid=r.json()['id'];self.assertEqual(self.patch('enquiries/'+str(eid),{'follow_up_date':'2099-01-01','admin_notes':'Follow up'}).status_code,200)
        csv=self.client.get('/api/admin/registrations/export').text;self.assertIn('Updated Student',csv)
        summary=self.client.get('/api/admin/dashboard/summary');self.assertEqual(summary.status_code,200,summary.text);self.assertEqual(summary.json()['courses'],78)
        self.assertEqual(summary.json()['recent'][0]['course_name'],'Python Full Stack Development')
        self.client.delete('/api/admin/registrations/'+str(id),headers=self.headers)
        self.assertEqual(self.client.get('/api/admin/registrations').json()['total'],0)
        self.assertEqual(self.client.get('/api/admin/registrations?archived=true').json()['total'],1)
        db.init_local();db.init_local()
        self.assertEqual(len(asyncio.run(db.rows('SELECT * FROM registrations'))),1)
        self.assertEqual(len(asyncio.run(db.rows('SELECT * FROM courses'))),78)

if __name__=='__main__':unittest.main(verbosity=2)
