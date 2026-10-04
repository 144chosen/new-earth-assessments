"""Transparent NEU reflection scoring. Not an ancestry or clinical probability model."""
from pathlib import Path
import json, math
BASE=Path(__file__).parent
FREE=json.loads((BASE/'free.json').read_text())
PAID=json.loads((BASE/'purpose.json').read_text())
THEMES=[t['id'] for t in FREE['themes']]
ASTRO_THEMES={'Fire':['leadership','expression','imagination'],'Earth':['service','nature','clarity'],'Air':['inquiry','expression','cohesion'],'Water':['care','stillness','imagination']}
DOMAIN_THEMES={'vision':['imagination','inquiry','leadership'],'steadiness':['clarity','stillness','service'],'healing':['care','stillness','service'],'community':['cohesion','care','leadership'],'teaching':['inquiry','expression','clarity'],'art':['expression','imagination','stillness'],'earth':['nature','service','care'],'caregiving':['care','cohesion','service'],'building':['service','inquiry','leadership'],'calling':['clarity','leadership','cohesion']}
def validate_answers(answers,questions):
 if not isinstance(answers,dict):raise ValueError('Please answer each question.')
 result={}
 for q in questions:
  v=answers.get(q['id'])
  if isinstance(v,bool) or not isinstance(v,int) or not 1<=v<=5:raise ValueError('Each question needs a rating from 1 to 5.')
  result[q['id']]=v
 if set(answers)-{q['id'] for q in questions}:raise ValueError('Unrecognized question in this assessment version.')
 return result
def free_score(answers,astro=None):
 answers=validate_answers(answers,FREE['questions'])
 totals={k:[] for k in THEMES}
 for q in FREE['questions']:
  for k in q.get('themes',[q.get('theme')]):totals[k].append((answers[q['id']]-1)*25)
 themes={k:sum(v)/len(v) for k,v in totals.items()}
 element=astro.get('sun',{}).get('element') if astro else None
 # Astrology can change a profile by at most two points. Never infer lineage from a sign.
 adjusted={k:.98*v+.02*(65 if k in ASTRO_THEMES.get(element,[]) else 50) for k,v in themes.items()} if element else themes
 matches=[]
 for p in FREE['lineages']:
  s=sum(adjusted[k]*w for k,w in p['weights'].items())/sum(p['weights'].values())
  evidence=sorted(p['weights'],key=lambda k:-(themes[k]*p['weights'][k]))[:3]
  matches.append({'id':p['id'],'score':round(s,1),'evidence':evidence})
 matches.sort(key=lambda p:(-p['score'],p['id']))
 gap=matches[0]['score']-matches[1]['score']
 varied=max(answers.values())-min(answers.values())
 clarity='broad' if varied==0 or gap<1.5 else ('emerging' if gap<5 else 'focused')
 return {'matches':matches,'top':matches[:3],'themes':themes,'clarity':clarity,'astrologyWeight':2 if element else 0,'method':'Weighted answer resonance, with an optional 2% NEU Sun-element reflection. Scores are independent 0-100 indices, not ancestry probabilities, and do not need to sum to 100.','version':FREE['version']}
def purpose_domains(answers,heritage):
 qs=[q for d in PAID['domains'] for q in d['questions']]
 answers=validate_answers(answers,qs)
 out=[]
 for d in PAID['domains']:
  direct=sum((answers[q['id']]-1)*25 for q in d['questions'])/2
  prior=sum(heritage['themes'][k] for k in DOMAIN_THEMES[d['id']])/3
  out.append({'id':d['id'],'score':round(.97*direct+.03*prior,2),'answerScore':direct})
 return sorted(out,key=lambda x:(-x['score'],x['id']))
def purpose_score(answers,role_answers,context,heritage):
 domains=purpose_domains(answers,heritage)
 selected={d['id'] for d in domains[:3]}
 selected_roles=[r for r in PAID['roles'] if r['domain'] in selected]
 role_answers=validate_answers(role_answers,[{'id':r['id']} for r in selected_roles])
 dom={d['id']:d['score'] for d in domains}
 results=[]
 for r in selected_roles:
  # Specific preference materially differentiates the six roles in each selected domain.
  score=.60*dom[r['domain']]+.40*((role_answers[r['id']]-1)*25)
  results.append({'id':r['id'],'score':round(score,1)})
 results.sort(key=lambda x:(-x['score'],x['id']))
 ctx=validate_context(context)
 candidates=[]
 byid={r['id']:r for r in PAID['roles']}
 for result in results[:3]:
  r=byid[result['id']]
  for job in r['careers']:
   candidates.append({'title':job,'role':r['name'],'reason':r['description'],'entry':r['firstStep'],'training':r['training'],'readiness':'Training pathway' if any(w in job.lower() for w in ['licensed','therapist','mediator','childhood','interpreter','carpenter']) else ('Build evidence of skill' if ctx['experience']=='new' else 'Test a scoped offer or application')})
 # Remove duplicate job titles while preserving the role match.
 careers=list({c['title']:c for c in reversed(candidates)}.values());careers.reverse()
 plan=action_plan(ctx,byid[results[0]['id']])
 return {'top':results[:3],'ranked':results,'domains':domains,'context':ctx,'careers':careers,'plan':plan,'clarity':'broad' if results[0]['score']-results[1]['score']<2 else 'emerging','method':'97% current domain answers + 3% earlier heritage answer themes; then 60% domain fit + 40% specific role preference. Careers are NEU editorial suggestions filtered by the practical context, not credential or earnings predictions.','version':PAID['version']}
def validate_context(c):
 if not isinstance(c,dict):raise ValueError('Please complete your practical reflection.')
 choices={'experience':['new','developing','experienced'],'workMode':['employment','independent','mixed'],'visibility':['private','gentle','public'],'time':['one','three','five'],'incomeNeed':['exploring','supplement','soon'],'obstacle':['uncertainty','confidence','resources','burnout','none'],'hardship':['none','transition','loss','exclusion','setback','careload']}
 out={}
 for k,opts in choices.items():
  v=c.get(k)
  if v not in opts:raise ValueError('Please choose an answer for each practical question.')
  out[k]=v
 for k in ['skills','audience','intention']:
  v=c.get(k,'')
  if not isinstance(v,str) or len(v)>400:raise ValueError('Keep written reflections within 400 characters.')
  out[k]=v.strip()
 return out
def action_plan(c,r):
 capacity={'one':'one hour','three':'three hours','five':'five or more hours'}[c['time']]
 visibility={'private':'Ask one trusted person for a private practice session; you do not need to publish your personal story.','gentle':'Publish one short written post or audio note about a useful idea. Invite a conversation without promising transformation.','public':'Create a 60-second teaching video, or host a short TikTok / Instagram live with a practical exercise and one clear invitation.'}[c['visibility']]
 work={'employment':'Find three real vacancies related to your matched jobs. Compare requirements, revise one portfolio example, and apply to one realistic entry route.','independent':'Interview three people in a specific audience about what support they want. Define a small paid pilot with a clear outcome, duration, price, boundaries, and feedback process.','mixed':'Choose one stable employment route and one small service pilot. Set a weekly limit so testing your calling does not consume your whole schedule.'}[c['workMode']]
 obstacle={'uncertainty':'Run one experiment before making a large commitment. Track what felt useful, what others actually valued, and what you want to learn next.','confidence':'Rehearse with a trusted peer and ask for specific feedback on clarity, usefulness, and boundaries. Confidence can grow through evidence of practice.','resources':'Start with tools and spaces you already have. Use a library, free community room, or online meeting before buying equipment or a costly training.','burnout':'Protect recovery first. Choose one small, time-limited contribution and arrange shared responsibility. Rest can be part of service.','none':'Choose one clear project and set a completion date so your energy produces a usable result.'}[c['obstacle']]
 return [dict(period='Within 48 hours',title='Name your useful contribution',action=f'Write: “I help [audience] with [specific need] through [skill or practice].” Begin with {r["name"].lower()} as a lens, then use your own words.'),dict(period='Week 1',title='Find a mentor and verify your route',action=r['firstStep']+' Ask for one reputable training or supervised practice route.'),dict(period='Week 2',title='Practice at a sustainable scale',action=f'Reserve {capacity} this week. '+obstacle),dict(period='Week 3',title='Make the gift visible',action=visibility),dict(period='Week 4',title='Test livelihood and learn',action=work+' Ask what the person or employer actually needs and revise your offer using their response.')]
def hardship_text(context):
 return {'none':'You did not choose a hardship to include. Your gifts do not need a painful origin story to be meaningful.','transition':'You named a major life transition. Change can interrupt familiar roles and confidence. Choose a small experiment that lets your next chapter develop without requiring every answer at once.','loss':'You named loss or grief. Your grief deserves its own space and pace. If you choose to serve from this experience, pair compassion with support and boundaries; you do not have to teach before you are ready.','exclusion':'You named feeling unseen or excluded. That experience may help you notice who is missing from a room. Practice one invitation or accessible improvement while also allowing yourself to receive belonging.','setback':'You named a setback or disappointment. Separate what happened from your whole identity. Review one lesson, ask for constructive feedback, and choose a smaller experiment that you can evaluate.','careload':'You named heavy care responsibilities. Your contribution must fit your actual capacity. Seek shared support, protect restoration, and choose an action that does not require more self-abandonment.'}[context['hardship']]
