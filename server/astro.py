"""JPL/Skyfield positions; tropical, geocentric, apparent ecliptic of date."""
from datetime import datetime,date,time,timedelta,timezone
from zoneinfo import ZoneInfo,ZoneInfoNotFoundError
from pathlib import Path
from functools import lru_cache
import math
SIGNS=['Aries','Taurus','Gemini','Cancer','Leo','Virgo','Libra','Scorpio','Sagittarius','Capricorn','Aquarius','Pisces']
ELEMENTS=['Fire','Earth','Air','Water']*3
REFLECTIONS={'Fire':'Explore courage, initiative, and creative expression. A useful question is: what small action can make my gift visible without rushing?','Earth':'Explore steadiness, practical service, and care for tangible needs. A useful question is: what structure will help my contribution become dependable?','Air':'Explore curiosity, communication, and connection. A useful question is: how can I make an idea understandable and invite a useful exchange?','Water':'Explore sensitivity, imagination, and compassionate presence. A useful question is: how can I pair care with boundaries and restoration?'}
class BirthError(ValueError):pass
@lru_cache(maxsize=1)
def ephemeris():
 from skyfield.api import load,load_file
 p=Path(__file__).parent/'data/de440s.bsp'
 if not p.exists():raise BirthError('Birth calculations are temporarily unavailable. You can continue without them; no positions will be invented.')
 return load.timescale(builtin=True),load_file(str(p))
def local_to_utc(naive,zone,fold=None):
 tz=ZoneInfo(zone);valid=[]
 for f in (0,1):
  a=naive.replace(tzinfo=tz,fold=f);u=a.astimezone(timezone.utc)
  if u.astimezone(tz).replace(tzinfo=None)==naive and u not in [v[1] for v in valid]:valid.append((f,u))
 if not valid:raise BirthError('That local time did not occur because clocks changed. Please check the recorded time.')
 if len(valid)>1 and fold is None:raise BirthError('That local time occurred twice when clocks changed. Choose the first or second occurrence, or mark the time unknown.')
 return valid[0][1] if len(valid)==1 else next(v for f,v in valid if f==fold)
def identify(lon):
 i=int((lon%360)//30)
 return {'sign':SIGNS[i],'element':ELEMENTS[i],'degree':round(lon%30,2),'longitude':round(lon%360,6),'reflection':REFLECTIONS[ELEMENTS[i]]}
def ascendant(ts,dt,lat,lon):
 # Intersection of horizon/ecliptic, choose the intersection with a positive eastward component.
 import numpy as np
 from skyfield.framelib import ecliptic_frame
 t=ts.from_datetime(dt);eq_to_ecl=ecliptic_frame.rotation_at(t)
 # Relative ecliptic/equatorial-of-date rotation; avoids hard-coded J2000 obliquity.
 rot=eq_to_ecl@t.M.T
 eps=math.atan2(abs(float(rot[1,2])),float(rot[1,1]))
 theta=math.radians((t.gast*15+lon)%360);phi=math.radians(lat)
 a=math.cos(phi)*math.cos(theta)
 b=math.cos(phi)*math.sin(theta)*math.cos(eps)+math.sin(phi)*math.sin(eps)
 l=math.atan2(-a,b)
 for v in [l,l+math.pi]:
  east=-math.sin(theta)*math.cos(v)+math.cos(theta)*math.sin(v)*math.cos(eps)
  if east>0:return identify(math.degrees(v)%360)
 return None

def calculate(b):
 if not isinstance(b,dict):raise BirthError('Please check your birth details.')
 try:d=date.fromisoformat(b.get('dob',''))
 except (ValueError,TypeError):raise BirthError('Enter a valid date of birth.')
 if d<date(1900,1,1) or d>date.today():raise BirthError('Use a birth date from 1900 through today.')
 zone=b.get('timezone','')
 try:ZoneInfo(zone)
 except (ZoneInfoNotFoundError,ValueError,TypeError):raise BirthError('Confirm a valid IANA time zone, such as America/New_York.')
 try:lat=float(b['lat']);lon=float(b['lon'])
 except (ValueError,TypeError,KeyError):raise BirthError('Confirm the birthplace coordinates.')
 if not math.isfinite(lat) or not math.isfinite(lon) or not -90<=lat<=90 or not -180<=lon<=180:raise BirthError('Check the birthplace coordinates.')
 if not isinstance(b.get('timeKnown'),bool):raise BirthError('Confirm whether the birth time is known.')
 known=b['timeKnown'];ts,eph=ephemeris()
 from skyfield.framelib import ecliptic_frame
 def positions(dt):
  t=ts.from_datetime(dt);earth=eph['earth']
  return {k:identify(earth.at(t).observe(eph[k]).apparent().frame_latlon(ecliptic_frame)[1].degrees) for k in ['sun','moon']}
 out={'method':'NASA/JPL DE440s with Skyfield; apparent geocentric tropical ecliptic of date.','timeKnown':known,'timezone':zone,'styleNote':'Astrological meanings are traditional / NEU spiritual interpretations; astronomical position accuracy does not validate ancestry or personality predictions.'}
 if known:
  try:tt=time.fromisoformat(b.get('time',''))
  except (ValueError,TypeError):raise BirthError('Enter a valid birth time or choose time unknown.')
  f=b.get('fold')
  if f not in [None,0,1] or isinstance(f,bool):raise BirthError('Choose a valid clock-change occurrence.')
  dt=local_to_utc(datetime.combine(d,tt),zone,f);out.update(positions(dt));out['utc']=dt.isoformat()
  out['ascendant']=ascendant(ts,dt,lat,lon) if abs(lat)<66 else None
  out['uncertainty']='Birth time recorded to the minute; historical time-zone boundaries and record accuracy should be confirmed. Ascendant is withheld at polar latitudes.'
 else:
  start=local_to_utc(datetime.combine(d,time(0)),zone,0)
  end=local_to_utc(datetime.combine(d+timedelta(days=1),time(0)),zone,0)
  samples=[positions(start+(end-start)*i/48) for i in range(49)]
  for k in ['sun','moon']:
   signs=list(dict.fromkeys(v[k]['sign'] for v in samples))
   if len(signs)==1:
    out[k]={'sign':signs[0],'element':samples[24][k]['element'],'reflection':samples[24][k]['reflection'],'degree':None,'rangeDegrees':[samples[0][k]['longitude'],samples[-1][k]['longitude']]}
   else:out[k]={'sign':' / '.join(signs),'possibleSigns':signs,'element':None,'reflection':'The sign changes during this local birth date. No single sign or element is assigned without a birth time.','degree':None}
  out['ascendant']=None
  out['uncertainty']='Time unknown: positions were sampled across the full local birth date. Degrees and ascendant are withheld; sign changes remain visible.'
 return out
