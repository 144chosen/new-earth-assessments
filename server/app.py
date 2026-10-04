"""Private assessment service; payment enforcement and reporting live here."""
from flask import Flask,request,jsonify,send_from_directory,send_file
from cryptography.fernet import Fernet
from pathlib import Path
from datetime import datetime,timezone
from functools import wraps
import os,sqlite3,json,secrets,hashlib,hmac,base64,time,threading,io,uuid,math
import requests
from engine import FREE,PAID,free_score,purpose_domains,purpose_score
from astro import calculate,BirthError
BASE=Path(__file__).parent
PUBLIC=BASE.parent/'public'
class ServiceError(Exception):pass

def create_app(overrides=None):
 app=Flask(__name__,static_folder=None)
 app.config.update(MAX_CONTENT_LENGTH=64000,MODE=os.getenv('NEU_MODE','production'),DATA_KEY=os.getenv('NEU_DATA_KEY',''),DB=os.getenv('NEU_DB',str(BASE/'instance/assessments.sqlite3')),PUBLIC_URL=os.getenv('NEU_PUBLIC_URL',''),SQUARE_TOKEN=os.getenv('SQUARE_ACCESS_TOKEN',''),SQUARE_LOCATION=os.getenv('SQUARE_LOCATION_ID',''),SQUARE_SIGNATURE=os.getenv('SQUARE_WEBHOOK_SIGNATURE_KEY',''),SQUARE_WEBHOOK_URL=os.getenv('SQUARE_WEBHOOK_URL',''),SQUARE_ENV=os.getenv('SQUARE_ENV','sandbox'),SQUARE_VERSION=os.getenv('SQUARE_API_VERSION','2026-09-16'),TRUST_PROXY=os.getenv('NEU_TRUST_PROXY','0')=='1',GEOCODE_AGENT=os.getenv('NEU_GEOCODE_AGENT',''),GEOCODE_URL=os.getenv('NEU_GEOCODE_URL','https://nominatim.openstreetmap.org/search'))
 if overrides:app.config.update(overrides)
 if app.config['MODE'] not in ['production','preview','test']:raise RuntimeError('Invalid NEU_MODE')
 if app.config['MODE']=='production' and (not app.config['DATA_KEY'] or not app.config['PUBLIC_URL'].startswith('https://')):raise RuntimeError('Set a persistent NEU_DATA_KEY and HTTPS NEU_PUBLIC_URL before production startup.')
 if not app.config['DATA_KEY']:
  p=BASE/'instance/preview.key';p.parent.mkdir(exist_ok=True)
  if not p.exists():p.write_bytes(Fernet.generate_key());p.chmod(0o600)
  app.config['DATA_KEY']=p.read_bytes().decode()
 crypt=Fernet(app.config['DATA_KEY'])
 dbpath=Path(app.config['DB']);dbpath.parent.mkdir(parents=True,exist_ok=True)
 def db():
  c=sqlite3.connect(str(dbpath),timeout=30);c.row_factory=sqlite3.Row
  return c
 with db() as c:
  c.executescript('CREATE TABLE IF NOT EXISTS sessions (token_hash TEXT PRIMARY KEY,payload BLOB NOT NULL,expires REAL NOT NULL,order_id TEXT UNIQUE); CREATE TABLE IF NOT EXISTS events (id TEXT PRIMARY KEY,created REAL NOT NULL); CREATE TABLE IF NOT EXISTS geocache (query TEXT PRIMARY KEY,payload TEXT,created REAL); CREATE TABLE IF NOT EXISTS limits (bucket TEXT PRIMARY KEY,count INTEGER,reset REAL); CREATE TABLE IF NOT EXISTS locks (name TEXT PRIMARY KEY,stamp REAL);')
 dbpath.chmod(0o600)
 def token_hash(t):return hashlib.sha256(t.encode()).hexdigest()
 def read_session(t):
  if not isinstance(t,str) or not 30<=len(t)<=100:return None
  with db() as c:row=c.execute('SELECT * FROM sessions WHERE token_hash=? AND expires>?',(token_hash(t),time.time())).fetchone()
  return json.loads(crypt.decrypt(row['payload'])) if row else None
 def write_session(t,p):
  # Caller performs a single sequential user mutation; order binding also indexed.
  with db() as c:c.execute('UPDATE sessions SET payload=?,order_id=? WHERE token_hash=?',(crypt.encrypt(json.dumps(p).encode()),p.get('orderId'),token_hash(t)))
 def authenticated(fn):
  @wraps(fn)
  def wrap(*a,**k):
   auth=request.headers.get('Authorization','')
   t=auth[7:] if auth.startswith('Bearer ') else ''
   p=read_session(t)
   if not p:return jsonify(error='Your private session has expired. Start again or restore your saved access key.'),401
   request.neu_token=t;request.neu=p
   return fn(*a,**k)
  return wrap
 def rate(bucket,maximum,seconds):
  key=hashlib.sha256(bucket.encode()).hexdigest();now=time.time()
  with db() as c:
   c.execute('BEGIN IMMEDIATE');r=c.execute('SELECT * FROM limits WHERE bucket=?',(key,)).fetchone()
   n=r['count']+1 if r and r['reset']>now else 1;end=r['reset'] if r and r['reset']>now else now+seconds
   if n>maximum:return False
   c.execute('INSERT OR REPLACE INTO limits VALUES (?,?,?)',(key,n,end))
  return True
 @app.before_request
 def boundary():
  if app.config['MODE']=='preview' and request.host.split(':')[0] not in ['127.0.0.1','localhost','[::1]']:return jsonify(error='Preview mode is local only.'),403
  if request.path.startswith('/api/'):
   ip=request.headers.get('X-Forwarded-For','').split(',')[0].strip() if app.config['TRUST_PROXY'] else request.remote_addr
   if not rate('api:'+str(ip),240,60):return jsonify(error='Please wait a minute before trying again.'),429
   if request.method in ['POST','PUT','DELETE'] and request.path!='/api/webhooks/square':
    origin=request.headers.get('Origin')
    trusted=app.config['PUBLIC_URL'].rstrip('/') or request.host_url.rstrip('/')
    if origin and origin!=trusted:return jsonify(error='This request must come from the assessment website.'),403
    if request.method!='DELETE' and not request.is_json:return jsonify(error='Send JSON assessment data.'),415
 @app.after_request
 def headers(response):
  response.headers['X-Content-Type-Options']='nosniff';response.headers['Referrer-Policy']='no-referrer'
  if request.path.startswith('/api/'):response.headers['Cache-Control']='no-store'
  response.headers['Content-Security-Policy']="default-src 'self'; img-src 'self' data:; script-src 'self'; style-src 'self' 'unsafe-inline'; connect-src 'self'; font-src 'self'; frame-ancestors https://www.newearthuniversity.org https://newearthuniversity.org https://*.mykajabi.com https://app.kajabi.com http://127.0.0.1:* http://localhost:*"
  return response
 @app.errorhandler(ValueError)
 def invalid(e):return jsonify(error=str(e)),400
 @app.errorhandler(ServiceError)
 def service(e):return jsonify(error=str(e)),503
 @app.errorhandler(413)
 def too_big(e):return jsonify(error='This submission is too large.'),413
 @app.get('/')
 def home():return send_from_directory(PUBLIC,'index.html')
 @app.get('/heritage')
 @app.get('/purpose')
 def page():return send_from_directory(PUBLIC,'assessment.html')
 @app.get('/assets/<path:name>')
 def assets(name):return send_from_directory(PUBLIC/'assets',name)
 @app.get('/app.js')
 @app.get('/styles.css')
 def code():return send_from_directory(PUBLIC,request.path.lstrip('/'))
 @app.get('/api/config')
 def config():return jsonify(mode=app.config['MODE'],checkout='Square',price=2900,currency='USD',checkoutConfigured=bool(app.config['SQUARE_TOKEN'] and app.config['SQUARE_LOCATION']),retentionDays=90)
 @app.get('/api/content/heritage')
 def free_content():return jsonify(FREE)
 @app.post('/api/sessions')
 def start():
  t=secrets.token_urlsafe(40);p={'created':time.time(),'paid':False,'freeAnswers':{},'birth':None,'astro':None}
  with db() as c:
   c.execute('DELETE FROM sessions WHERE expires<?',(time.time(),));c.execute('DELETE FROM limits WHERE reset<?',(time.time(),));c.execute('DELETE FROM events WHERE created<?',(time.time()-90*86400,))
   c.execute('INSERT INTO sessions VALUES (?,?,?,?)',(token_hash(t),crypt.encrypt(json.dumps(p).encode()),time.time()+90*86400,None))
  return jsonify(token=t,session=p),201
 @app.get('/api/session')
 @authenticated
 def session():return jsonify(request.neu)
 @app.delete('/api/session')
 @authenticated
 def forget():
  with db() as c:c.execute('DELETE FROM sessions WHERE token_hash=?',(token_hash(request.neu_token),))
  return jsonify(deleted=True)
 @app.put('/api/draft')
 @authenticated
 def draft():
  data=request.get_json();a=data.get('answers',{});qs={q['id'] for q in FREE['questions']}
  if not isinstance(a,dict) or any(k not in qs or isinstance(v,bool) or not isinstance(v,int) or not 1<=v<=5 for k,v in a.items()):raise ValueError('Invalid draft answers.')
  request.neu['freeAnswers']=a;write_session(request.neu_token,request.neu);return jsonify(saved=True)
 @app.post('/api/geocode')
 @authenticated
 def geocode():
  q=request.get_json().get('place','')
  if not isinstance(q,str) or not 3<=len(q)<=160:raise ValueError('Enter a city or town and country.')
  if not app.config['GEOCODE_AGENT']:raise ServiceError('Place search is not configured. Use the manual coordinates and time-zone fields.')
  with db() as c:r=c.execute('SELECT * FROM geocache WHERE query=? AND created>?',(q.casefold(),time.time()-30*86400)).fetchone()
  if r:return jsonify(json.loads(r['payload']))
  # Shared SQLite lock enforces public Nominatim's one-request-per-second ceiling across workers.
  with db() as c:
   c.execute('BEGIN IMMEDIATE');r=c.execute('SELECT stamp FROM locks WHERE name=?',('geocode',)).fetchone()
   if r and time.time()-r['stamp']<1.1:return jsonify(error='Please wait a moment before searching again.'),429
   c.execute('INSERT OR REPLACE INTO locks VALUES (?,?)',('geocode',time.time()))
  try:
   r=requests.get(app.config['GEOCODE_URL'],params={'q':q,'format':'jsonv2','limit':5},headers={'User-Agent':app.config['GEOCODE_AGENT']},timeout=12);r.raise_for_status();raw=r.json()
   from timezonefinder import TimezoneFinder
   tf=TimezoneFinder()
   candidates=[{'label':v['display_name'],'lat':float(v['lat']),'lon':float(v['lon']),'timezone':tf.timezone_at(lat=float(v['lat']),lng=float(v['lon']))} for v in raw]
  except (requests.RequestException,ValueError,KeyError):raise ServiceError('Place search is unavailable. You can enter coordinates and a time zone manually.')
  result={'candidates':candidates,'attribution':'© OpenStreetMap contributors; Nominatim. Current IANA zone boundaries from timezonefinder; confirm the historical zone for the birth record.'}
  with db() as c:c.execute('INSERT OR REPLACE INTO geocache VALUES (?,?,?)',(q.casefold(),json.dumps(result),time.time()))
  return jsonify(result)
 @app.post('/api/birth')
 @authenticated
 def birth():
  data=request.get_json()
  if data.get('skip'):
   request.neu.update(birth=None,astro=None)
  else:
   b=data.get('birth');a=calculate(b)
   name=data.get('name','')
   if not isinstance(name,str) or len(name)>80:raise ValueError('Use a name within 80 characters.')
   label=b.get('place','')
   if not isinstance(label,str) or len(label)>200:raise ValueError('Use a birthplace label within 200 characters.')
   safe={k:b.get(k) for k in ['dob','timeKnown','time','fold','lat','lon','timezone']};safe['place']=label
   request.neu.update(birth=safe,astro=a,name=name.strip())
  request.neu.update(freeAnswers={})
  for k in ['heritage','purpose','domainAnswers','roleAnswers']:request.neu.pop(k,None)
  write_session(request.neu_token,request.neu);return jsonify(astro=request.neu.get('astro'))
 @app.post('/api/heritage/result')
 @authenticated
 def heritage():
  a=request.get_json().get('answers');result=free_score(a,request.neu.get('astro'))
  request.neu.update(freeAnswers=a,heritage=result)
  for k in ['purpose','domainAnswers','roleAnswers']:request.neu.pop(k,None)
  write_session(request.neu_token,request.neu)
  return jsonify(result)
 def square(method,path,payload=None):
  if not app.config['SQUARE_TOKEN']:raise ServiceError('The owner has not connected checkout yet. No payment has been taken.')
  host='https://connect.squareup.com' if app.config['SQUARE_ENV']=='production' else 'https://connect.squareupsandbox.com'
  try:
   r=requests.request(method,host+'/v2/'+path,json=payload,headers={'Authorization':'Bearer '+app.config['SQUARE_TOKEN'],'Square-Version':app.config['SQUARE_VERSION'],'Content-Type':'application/json'},timeout=15);r.raise_for_status();return r.json()
  except (requests.RequestException,ValueError):raise ServiceError('Payment verification is temporarily unavailable. Please try again; do not purchase a second time.')
 def verified_payment(payment,order_id):
  return bool(payment.get('order_id')==order_id and payment.get('status')=='COMPLETED' and payment.get('amount_money')=={'amount':2900,'currency':'USD'} and payment.get('location_id')==app.config['SQUARE_LOCATION'] and (payment.get('refunded_money',{}).get('amount',0)==0))
 def check_paid(p):
  oid=p.get('orderId')
  if not oid:return False
  order=square('GET','orders/'+oid).get('order',{})
  if order.get('location_id')!=app.config['SQUARE_LOCATION'] or order.get('state') not in ['OPEN','COMPLETED']:return False
  for tender in order.get('tenders',[]):
   pid=tender.get('payment_id') or tender.get('id')
   if pid and verified_payment(square('GET','payments/'+pid).get('payment',{}),oid):
    p['paymentId']=pid;p['verifiedAt']=time.time();return True
  return False
 def enforce_paid():
  p=request.neu
  if not p.get('heritage'):raise ValueError('Complete the Celestial Heritage Assessment first.')
  if app.config['MODE'] in ['preview','test'] and p.get('previewPaid'):return
  # Recheck on every paid content/report call, so refunds and payment revocations are respected.
  ok=check_paid(p);p['paid']=ok;write_session(request.neu_token,p)
  if not ok:return jsonify(error='The $29 assessment unlocks after the server verifies a completed payment.'),402
 @app.post('/api/checkout')
 @authenticated
 def checkout():
  p=request.neu
  if not p.get('heritage'):raise ValueError('Complete your free assessment first.')
  if p.get('checkoutUrl'):return jsonify(url=p['checkoutUrl'])
  if not app.config['SQUARE_LOCATION']:raise ServiceError('The owner has not connected checkout yet. No payment has been taken.')
  key=p.get('checkoutKey') or str(uuid.uuid4());p['checkoutKey']=key;write_session(request.neu_token,p)
  url=app.config['PUBLIC_URL'].rstrip('/')+'/purpose'
  result=square('POST','online-checkout/payment-links',{'idempotency_key':key,'quick_pay':{'name':'The 144,000: Discover Your Role + Five-Page Report','price_money':{'amount':2900,'currency':'USD'},'location_id':app.config['SQUARE_LOCATION']},'checkout_options':{'redirect_url':url,'allow_tipping':False,'ask_for_shipping_address':False}})
  link=result.get('payment_link',{})
  if not link.get('order_id') or not link.get('url'):raise ServiceError('Checkout was not created. Please try again.')
  p.update(orderId=link['order_id'],checkoutUrl=link['url']);write_session(request.neu_token,p)
  return jsonify(url=link['url'])
 @app.get('/api/payment/status')
 @authenticated
 def status():
  p=request.neu
  if app.config['MODE'] in ['preview','test'] and p.get('previewPaid'):return jsonify(paid=True,preview=True)
  if p.get('orderId'):
   if not rate('payment:'+request.neu_token,15,60):return jsonify(error='Please wait before checking payment again.'),429
   p['paid']=check_paid(p);write_session(request.neu_token,p)
  return jsonify(paid=bool(p.get('paid')),preview=False)
 @app.post('/api/preview/unlock')
 @authenticated
 def preview_unlock():
  if app.config['MODE'] not in ['preview','test']:return jsonify(error='Not found'),404
  request.neu['previewPaid']=True;write_session(request.neu_token,request.neu);return jsonify(preview=True)
 @app.post('/api/webhooks/square')
 def webhook():
  raw=request.get_data();key=app.config['SQUARE_SIGNATURE'];url=app.config['SQUARE_WEBHOOK_URL']
  if not key or not url:return jsonify(error='Webhook is not configured.'),503
  expected=base64.b64encode(hmac.new(key.encode(),url.encode()+raw,hashlib.sha256).digest()).decode()
  if not hmac.compare_digest(expected,request.headers.get('x-square-hmacsha256-signature','')):return jsonify(error='Invalid signature.'),403
  event=request.get_json();eid=event.get('event_id')
  if not isinstance(eid,str) or not 1<=len(eid)<=100:raise ValueError('Invalid event.')
  with db() as c:
   if c.execute('SELECT 1 FROM events WHERE id=?',(eid,)).fetchone():return jsonify(received=True)
  if event.get('type') in ['payment.created','payment.updated','refund.created','refund.updated']:
   obj=event.get('data',{}).get('object',{});payment=obj.get('payment')
   if not payment:
    pid=obj.get('refund',{}).get('payment_id')
    if pid:payment=square('GET','payments/'+pid).get('payment',{})
   oid=payment.get('order_id') if payment else None
   if oid:
    with db() as c:row=c.execute('SELECT * FROM sessions WHERE order_id=? AND expires>?',(oid,time.time())).fetchone()
    if row:
     p=json.loads(crypt.decrypt(row['payload']));p['paid']=check_paid(p)
     with db() as c:c.execute('UPDATE sessions SET payload=? WHERE token_hash=?',(crypt.encrypt(json.dumps(p).encode()),row['token_hash']))
  with db() as c:c.execute('INSERT OR IGNORE INTO events VALUES (?,?)',(eid,time.time()))
  return jsonify(received=True)
 @app.get('/api/content/purpose')
 @authenticated
 def paid_content():
  block=enforce_paid()
  if block:return block
  return jsonify(PAID)
 @app.post('/api/purpose/domains')
 @authenticated
 def domains():
  block=enforce_paid()
  if block:return block
  a=request.get_json().get('answers');d=purpose_domains(a,request.neu['heritage']);request.neu['domainAnswers']=a;write_session(request.neu_token,request.neu)
  return jsonify(domains=d,roles=[r for r in PAID['roles'] if r['domain'] in {d['id'] for d in d[:3]}])
 @app.post('/api/purpose/result')
 @authenticated
 def purpose():
  block=enforce_paid()
  if block:return block
  data=request.get_json();r=purpose_score(request.neu.get('domainAnswers'),data.get('roles'),data.get('context'),request.neu['heritage'])
  request.neu.update(roleAnswers=data['roles'],purpose=r);write_session(request.neu_token,request.neu);return jsonify(r)
 @app.get('/api/report')
 @authenticated
 def report():
  block=enforce_paid()
  if block:return block
  if not request.neu.get('purpose'):raise ValueError('Complete the purpose assessment to create your report.')
  from report import make_report
  pdf=make_report(request.neu,preview=app.config['MODE'] in ['preview','test'])
  return send_file(io.BytesIO(pdf),mimetype='application/pdf',as_attachment=True,download_name='New-Earth-University-Soul-Blueprint.pdf')
 # Hooks intentionally exposed only for tests that verify actual access boundaries.
 app.neu={'read_session':read_session,'write_session':write_session,'verified_payment':verified_payment}
 return app
if __name__=='__main__':
 app=create_app();app.run(host='127.0.0.1',port=int(os.getenv('PORT','8765')),debug=False)
