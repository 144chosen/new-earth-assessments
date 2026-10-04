"""Run daily on the host to purge expired encrypted sessions and limiter records."""
import os,sqlite3,time
from pathlib import Path
p=os.getenv('NEU_DB',str(Path(__file__).parent/'instance/assessments.sqlite3'))
if __name__=='__main__':
 with sqlite3.connect(p) as c:
  c.execute('DELETE FROM sessions WHERE expires<?',(time.time(),))
  c.execute('DELETE FROM limits WHERE reset<?',(time.time(),))
  c.execute('DELETE FROM events WHERE created<?',(time.time()-90*86400,))
  c.execute('DELETE FROM geocache WHERE created<?',(time.time()-30*86400,))
  c.execute('PRAGMA secure_delete=ON')
 print('Expired records removed.')
