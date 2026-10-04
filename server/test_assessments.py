import unittest,tempfile,json,io,base64,hmac,hashlib,sqlite3,random
from pathlib import Path
from unittest.mock import patch
from datetime import datetime,timezone
from cryptography.fernet import Fernet
from pypdf import PdfReader
from app import create_app
from engine import FREE,PAID,free_score,purpose_domains,purpose_score
from astro import calculate,local_to_utc,BirthError
from report import make_report
BASE=Path(__file__).parent
FA={q['id']:3 for q in FREE['questions']}
DA={q['id']:3 for d in PAID['domains'] for q in d['questions']}
CTX={'experience':'developing','workMode':'independent','visibility':'public','time':'three','incomeNeed':'supplement','obstacle':'confidence','hardship':'transition','skills':'Writing, teaching and hosting small circles.','audience':'Adults in a life transition.','intention':'Give my gifts a useful expression and begin a grounded service.'}
B={'dob':'1990-06-21','timeKnown':True,'time':'12:00','fold':None,'lat':40.7128,'lon':-74.006,'timezone':'America/New_York','place':'New York, USA'}
def role_answers(a,h,target=None):
 d=purpose_domains(a,h);selected={x['id'] for x in d[:3]}
 return {r['id']:(5 if r['id']==target else 2) for r in PAID['roles'] if r['domain'] in selected}
class Scoring(unittest.TestCase):
 def test_counts(self):self.assertEqual((len(FREE['questions']),len(FREE['lineages']),len(PAID['roles'])),(30,19,60))
 def test_uniform_is_broad(self):self.assertEqual(free_score(FA)['clarity'],'broad')
 def test_invalid_and_partial(self):
  for v in [None,False,0,6,3.1,'5']:
   a=FA.copy();a[next(iter(a))]=v
   with self.subTest(v=v),self.assertRaises(ValueError):free_score(a)
  with self.assertRaises(ValueError):free_score({})
 def test_bounds_reproducibility(self):
  for _ in range(30):
   a={q['id']:random.randint(1,5) for q in FREE['questions']};r=free_score(a)
   self.assertEqual(r,free_score(a));self.assertTrue(all(0<=m['score']<=100 for m in r['matches']))
 def test_astrology_influence_bounded(self):
  base={x['id']:x['score'] for x in free_score(FA)['matches']}
  for element in ['Fire','Earth','Air','Water']:
   r=free_score(FA,{'sun':{'element':element}})
   self.assertTrue(all(abs(x['score']-base[x['id']])<=2 for x in r['matches']))
 def test_all_60_roles_can_win(self):
  h=free_score(FA)
  for r in PAID['roles']:
   a={q['id']:5 if d['id']==r['domain'] else 1 for d in PAID['domains'] for q in d['questions']}
   result=purpose_score(a,role_answers(a,h,r['id']),CTX,h);self.assertEqual(result['top'][0]['id'],r['id'])
 def test_context_changes_actions(self):
  h=free_score(FA);ra=role_answers(DA,h);a=purpose_score(DA,ra,CTX,h);b=purpose_score(DA,ra,{**CTX,'visibility':'private','workMode':'employment','time':'one'},h)
  self.assertIn('TikTok',a['plan'][3]['action']);self.assertIn('private',b['plan'][3]['action']);self.assertIn('vacancies',b['plan'][4]['action'])
 def test_assets(self):
  for p in FREE['lineages']:self.assertTrue((BASE.parent/'public'/p['image']).exists())
 def test_probabilities_not_claimed(self):self.assertIn('not ancestry probabilities',free_score(FA)['method'])
class Birth(unittest.TestCase):
 def test_known(self):
  r=calculate(B);self.assertEqual(r['sun']['sign'],'Cancer');self.assertEqual(r['utc'],'1990-06-21T16:00:00+00:00');self.assertIsNotNone(r['ascendant'])
 def test_unknown(self):
  r=calculate({**B,'timeKnown':False});self.assertIsNone(r['ascendant']);self.assertIsNone(r['sun']['degree']);self.assertIn('possibleSigns',r['sun'])
 def test_gap(self):
  with self.assertRaises(BirthError):local_to_utc(datetime(2021,3,14,2,30),'America/New_York')
 def test_fold(self):
  with self.assertRaises(BirthError):local_to_utc(datetime(2021,11,7,1,30),'America/New_York')
  a=local_to_utc(datetime(2021,11,7,1,30),'America/New_York',0);b=local_to_utc(datetime(2021,11,7,1,30),'America/New_York',1);self.assertEqual((b-a).total_seconds(),3600)
 def test_invalid(self):
  for edit in [{'dob':'1800-01-01'},{'timezone':'Bad/Zone'},{'lat':'nan'},{'time':'27:80'},{'fold':True}]:
   with self.subTest(edit=edit),self.assertRaises(ValueError):calculate({**B,**edit})
 def test_polar(self):self.assertIsNone(calculate({**B,'lat':80})['ascendant'])
 def test_independent_swiss_reference(self):
  try:import swisseph as swe
  except ImportError:self.skipTest('Optional reference package')
  for dt,lat,lon in [(datetime(1990,6,21,16,tzinfo=timezone.utc),40.7128,-74.006),(datetime(1982,2,12,0,tzinfo=timezone.utc),-33.8688,151.2093),(datetime(2001,9,15,8,tzinfo=timezone.utc),51.5074,-.1278)]:
   r=calculate({'dob':dt.date().isoformat(),'timeKnown':True,'time':dt.strftime('%H:%M'),'fold':None,'lat':lat,'lon':lon,'timezone':'UTC'});jd=swe.julday(dt.year,dt.month,dt.day,dt.hour)
   for body,k in [(swe.SUN,'sun'),(swe.MOON,'moon')]:
    p,f=swe.calc_ut(jd,body,swe.FLG_MOSEPH);self.assertLess(abs((r[k]['longitude']-p[0]+180)%360-180),.01)
   _,axes=swe.houses_ex(jd,lat,lon,b'P');self.assertLess(abs((r['ascendant']['longitude']-axes[0]+180)%360-180),.02)
class Access(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.key=Fernet.generate_key().decode();self.app=create_app({'MODE':'test','DB':str(Path(self.tmp.name)/'test.db'),'DATA_KEY':self.key,'PUBLIC_URL':'http://localhost','SQUARE_LOCATION':'LOC','SQUARE_TOKEN':'testing-only','SQUARE_SIGNATURE':'sig-test','SQUARE_WEBHOOK_URL':'https://quiz.example/api/webhooks/square'});self.cl=self.app.test_client();self.token=self.cl.post('/api/sessions',json={}).get_json()['token'];self.h={'Authorization':'Bearer '+self.token}
 def tearDown(self):self.tmp.cleanup()
 def free(self):return self.cl.post('/api/heritage/result',json={'answers':FA},headers=self.h)
 def square(self,method,url,**kw):
  class R:
   def raise_for_status(self):pass
   def json(self_):
    if '/orders/' in url:return {'order':{'state':'COMPLETED','location_id':'LOC','tenders':[{'payment_id':'PAY'}]}}
    if '/payments/' in url:return {'payment':{'order_id':'ORDER','status':'COMPLETED','amount_money':{'amount':2900,'currency':'USD'},'location_id':'LOC','refunded_money':{'amount':0,'currency':'USD'}}}
    if '/payment-links' in url:
     assert kw['json']['quick_pay']['price_money']=={'amount':2900,'currency':'USD'}
     return {'payment_link':{'order_id':'ORDER','url':'https://square.link/u/test'}}
  return R()
 def test_no_auth(self):self.assertEqual(self.cl.get('/api/session').status_code,401)
 def test_free_cannot_unlock(self):
  self.free();self.assertEqual(self.cl.get('/api/content/purpose?paid=true',headers=self.h).status_code,402);self.assertEqual(self.cl.get('/api/report',headers=self.h).status_code,402)
 def test_origin(self):self.assertEqual(self.cl.post('/api/sessions',json={},headers={'Origin':'https://evil.example'}).status_code,403)
 def test_checkout_prerequisite(self):self.assertEqual(self.cl.post('/api/checkout',json={},headers=self.h).status_code,400)
 def test_checkout_and_paid(self):
  self.free()
  with patch('app.requests.request',side_effect=self.square):
   self.assertEqual(self.cl.post('/api/checkout',json={'amount':1},headers=self.h).status_code,200);self.assertTrue(self.cl.get('/api/payment/status',headers=self.h).get_json()['paid']);self.assertEqual(self.cl.get('/api/content/purpose',headers=self.h).status_code,200)
 def test_quickpay_open_order_with_tender_id_unlocks(self):
  self.free()
  p=self.app.neu['read_session'](self.token);p['orderId']='ORDER';self.app.neu['write_session'](self.token,p)
  def provider(method,url,**kw):
   if '/orders/' in url:
    class R:
     def raise_for_status(self):pass
     def json(self):return {'order':{'state':'OPEN','location_id':'LOC','tenders':[{'id':'PAY'}]}}
    return R()
   return self.square(method,url,**kw)
  with patch('app.requests.request',side_effect=provider):self.assertTrue(self.cl.get('/api/payment/status',headers=self.h).get_json()['paid'])
 def test_draft_order_does_not_unlock(self):
  self.free()
  p=self.app.neu['read_session'](self.token);p['orderId']='ORDER';self.app.neu['write_session'](self.token,p)
  class R:
   def raise_for_status(self):pass
   def json(self):return {'order':{'state':'DRAFT','location_id':'LOC','tenders':[{'id':'PAY'}]}}
  with patch('app.requests.request',return_value=R()):self.assertFalse(self.cl.get('/api/payment/status',headers=self.h).get_json()['paid'])
 def test_payment_fields_enforced(self):
  p={'order_id':'ORDER','status':'COMPLETED','amount_money':{'amount':2900,'currency':'USD'},'location_id':'LOC'};verify=self.app.neu['verified_payment'];self.assertTrue(verify(p,'ORDER'))
  for e in [{'status':'APPROVED'},{'order_id':'OTHER'},{'location_id':'OTHER'},{'amount_money':{'amount':1,'currency':'USD'}},{'amount_money':{'amount':2900,'currency':'EUR'}},{'refunded_money':{'amount':1,'currency':'USD'}}]:self.assertFalse(verify({**p,**e},'ORDER'))
 def test_production_has_no_preview_unlock(self):
  app=create_app({'MODE':'production','DB':str(Path(self.tmp.name)/'prod.db'),'DATA_KEY':self.key,'PUBLIC_URL':'https://quiz.example'});cl=app.test_client();t=cl.post('/api/sessions',json={}).get_json()['token'];self.assertEqual(cl.post('/api/preview/unlock',json={},headers={'Authorization':'Bearer '+t}).status_code,404)
 def test_forged_webhook(self):self.assertEqual(self.cl.post('/api/webhooks/square',json={'event_id':'x'},headers={'x-square-hmacsha256-signature':'forged'}).status_code,403)
 def test_valid_webhook_idempotent(self):
  raw=json.dumps({'event_id':'event1','type':'unknown'}).encode();sig=base64.b64encode(hmac.new(b'sig-test',b'https://quiz.example/api/webhooks/square'+raw,hashlib.sha256).digest()).decode()
  for _ in range(2):self.assertEqual(self.cl.post('/api/webhooks/square',data=raw,content_type='application/json',headers={'x-square-hmacsha256-signature':sig}).status_code,200)
  with sqlite3.connect(self.app.config['DB']) as c:self.assertEqual(c.execute('SELECT count(*) FROM events').fetchone()[0],1)
 def test_encrypted_and_deleted(self):
  self.cl.post('/api/birth',json={'birth':B,'name':'PrivateName'},headers=self.h);raw=Path(self.app.config['DB']).read_bytes();self.assertNotIn(b'PrivateName',raw);self.assertNotIn(b'1990-06-21',raw);self.assertEqual(self.cl.delete('/api/session',headers=self.h).status_code,200);self.assertEqual(self.cl.get('/api/session',headers=self.h).status_code,401)
 def test_report_access_and_five_pages(self):
  self.free();self.cl.post('/api/preview/unlock',json={},headers=self.h);d=self.cl.post('/api/purpose/domains',json={'answers':DA},headers=self.h).get_json();ra={r['id']:4 for r in d['roles']};self.assertEqual(self.cl.post('/api/purpose/result',json={'roles':ra,'context':CTX},headers=self.h).status_code,200);r=self.cl.get('/api/report',headers=self.h);self.assertEqual(r.status_code,200);self.assertEqual(len(PdfReader(io.BytesIO(r.data)).pages),5)
 def test_no_cross_session_unlock(self):
  self.free();self.cl.post('/api/preview/unlock',json={},headers=self.h);t=self.cl.post('/api/sessions',json={}).get_json()['token'];h={'Authorization':'Bearer '+t};self.cl.post('/api/heritage/result',json={'answers':FA},headers=h);self.assertEqual(self.cl.get('/api/content/purpose',headers=h).status_code,402)
class Reports(unittest.TestCase):
 def test_long_inputs_all_domains(self):
  h=free_score(FA)
  for domain in PAID['domains']:
   a={q['id']:5 if d['id']==domain['id'] else 1 for d in PAID['domains'] for q in d['questions']};ra=role_answers(a,h);ctx={**CTX,'skills':('Writing & teaching <reflection> '*15)[:400],'audience':('Community participants and shared practice '*15)[:400],'intention':('A grounded path into purpose and contribution '*15)[:400]};p=purpose_score(a,ra,ctx,h);pdf=make_report({'name':'Avery Sample','heritage':h,'purpose':p,'astro':calculate(B),'birth':B},True);self.assertEqual(len(PdfReader(io.BytesIO(pdf)).pages),5)
if __name__=='__main__':unittest.main(verbosity=2)
