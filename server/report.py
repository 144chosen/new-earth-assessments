"""Five bounded, verified pages of personalized NEU reflection; no generative certainty."""
from pathlib import Path
import io,html,re,math
from reportlab.pdfgen import canvas
from reportlab.lib import colors
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import Paragraph,Spacer,Image,Table,TableStyle,KeepTogether
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.utils import ImageReader
from engine import FREE,PAID,hardship_text
BASE=Path(__file__).parent
ASSETS=BASE.parent/'public/assets'
FONTS=BASE/'fonts'
def setup_fonts():
 candidates=[FONTS,Path('/usr/share/fonts/truetype/dejavu')]
 font_names=[('NeuSans','DejaVuSans.ttf'),('NeuSansBold','DejaVuSans-Bold.ttf'),('NeuSerif','DejaVuSerif.ttf')]
 for name,fn in font_names:
  p=next((d/fn for d in candidates if (d/fn).exists()),None)
  if p and name not in pdfmetrics.getRegisteredFontNames():pdfmetrics.registerFont(TTFont(name,str(p)))
 return all(n in pdfmetrics.getRegisteredFontNames() for n,fn in font_names)
setup_fonts()
SAN='NeuSans' if 'NeuSans' in pdfmetrics.getRegisteredFontNames() else 'Helvetica'
BOLD='NeuSansBold' if 'NeuSansBold' in pdfmetrics.getRegisteredFontNames() else 'Helvetica-Bold'
SERIF='NeuSerif' if 'NeuSerif' in pdfmetrics.getRegisteredFontNames() else 'Times-Roman'
NAVY=colors.HexColor('#101a2d');GOLD=colors.HexColor('#d0a85e');INK=colors.HexColor('#23324a');MUTED=colors.HexColor('#52617a');IVORY=colors.HexColor('#fbf8f1')
def safe(s):return html.escape(str(s or '')).replace('\n','<br/>')
def make_report(session,preview=False):
 heritage=session['heritage'];purpose=session['purpose'];context=purpose['context'];birth=session.get('birth');astro=session.get('astro');name=session.get('name') or 'Your personal reflection'
 pmap={p['id']:p for p in FREE['lineages']};rmap={r['id']:r for r in PAID['roles']}
 lineages=[pmap[m['id']] for m in heritage['top']];roles=[rmap[m['id']] for m in purpose['top']];top=roles[0]
 buffer=io.BytesIO();c=canvas.Canvas(buffer,pagesize=(612,792));c.setTitle('New Earth University | Soul Blueprint & Purpose');c.setAuthor('New Earth University')
 sections=['Your Celestial Heritage','Your Soul Blueprint & Role Blend','Purpose, Experience & Your Next Chapter','Work, Service & Income Possibilities','Your First Month of Embodied Purpose']
 def style(size=10.1,font=SAN,color=INK,space=8):return ParagraphStyle('p',fontName=font,fontSize=size,leading=size*1.42,textColor=color,spaceAfter=space)
 def para(txt,size=10.1,font=SAN,color=INK):return Paragraph(txt,style(size,font,color))
 def head(txt):return para(safe(txt),15,SERIF)
 def small(txt):return para(safe(txt),8.3,SAN,MUTED)
 def block(title,text):return [head(title),para(safe(text))]
 def paint(page,title,items):
  c.setFillColor(IVORY);c.rect(0,0,612,792,fill=1,stroke=0)
  c.setFillColor(NAVY);c.rect(0,689,612,103,fill=1,stroke=0)
  c.setFillColor(GOLD);c.setFont(SAN,8);c.drawString(46,763,'N E W  E A R T H  U N I V E R S I T Y')
  c.setFillColor(colors.white);c.setFont(SERIF,19);c.drawString(46,726,title)
  c.setFillColor(GOLD);c.rect(46,704,520,1,fill=1,stroke=0)
  c.setStrokeColor(GOLD);c.line(46,43,566,43);c.setFont(SAN,7.5);c.setFillColor(MUTED)
  c.drawString(46,28,'REMEMBER · PRACTICE · EMBODY' + ('  |  OWNER SAMPLE' if preview else ''))
  c.drawRightString(566,28,f'{page} / 5')
  # Scale typography only if a long combination requires it; never create or clip a sixth page.
  width=520;available=620
  def size_items():
   return sum(item.wrap(width,available)[1]+getattr(item,'spaceAfter',0) for item in items)
  total=size_items();factor=1
  if total>available:
   factor=max(.82,available/total-.015)
   for item in items:
    if isinstance(item,Paragraph):item.style=item.style.clone(item.style.name+'_fit',fontSize=item.style.fontSize*factor,leading=item.style.leading*factor,spaceAfter=item.style.spaceAfter*factor)
   total=size_items()
  if total>available:raise ValueError('Report page content exceeded its verified layout boundary.')
  y=664
  for item in items:
   w,h=item.wrap(width,available);y-=h;item.drawOn(c,46,y);y-=getattr(item,'spaceAfter',0)
  if y<46:raise ValueError('Report text exceeded the printable page.')
  c.showPage()
 # 1: three portraits, exact source distinctions, no personal origin asserted.
 rows=[]
 for p,m in zip(lineages,heritage['top']):
  img=Image(str(ASSETS/Path(p['image']).name),width=158,height=162,kind='proportional')
  rows.append([img,para(safe(p['name']),11,SERIF),small(f'{m["score"]:.1f} / 100 resonance'),small(p['family'])])
 table=Table([[r[j] for r in rows] for j in range(4)],colWidths=[173.33]*3)
 table.setStyle(TableStyle([('VALIGN',(0,0),(-1,-1),'TOP'),('LEFTPADDING',(0,0),(-1,-1),0),('RIGHTPADDING',(0,0),(-1,-1),12),('TOPPADDING',(0,0),(-1,-1),3),('BOTTOMPADDING',(0,0),(-1,-1),3)]))
 items=[para(safe(name),22,SERIF),para('Your Soul Blueprint & Purpose',12,SAN,MUTED),para('Your celestial story is offered as a spiritual mirror. These founder families and related expressions resonate with patterns in your answers; they do not establish a verified extraterrestrial identity or the exact birthplace of your soul.'),Spacer(1,8),table,Spacer(1,14)]
 for p in lineages:
  items.append(para(f'<font name="{BOLD}">{safe(p["name"])}</font>: {safe(p["background"])} {safe(p["location"])}. {safe(p["locationNote"])}',9.1))
 items.append(small('Portraits are artistic interpretations supplied by New Earth University. A consciousness collective, founder order, and specialized race expression are different categories; overlapping matches are expected.'))
 paint(1,sections[0],items)
 # 2: roles and evidence, specific practices, soul-blueprint invitation.
 blend=', '.join(r['name'] for r in roles)
 items=[head('Your strongest role blend'),para(f'Your answers point toward <font name="{BOLD}">{safe(blend)}</font>. Your soul blueprint is explored here as the meeting place of your values, recurring interests, developing abilities, and the people or places you want to serve. Let it be something you practice and refine, rather than a title you must prove.'),Spacer(1,4)]
 for r,m in zip(roles,purpose['top']):
  items+=block(f'{r["name"]} · {m["score"]:.1f} / 100',r['description'])
  items.append(para(safe('To begin: '+r['firstStep']),9.5))
 items+=block('The thread connecting heritage and purpose','Your heritage results bring a symbolic language for connection; your role answers show how that connection might become useful here. These are separate lenses. No founder family determines one inevitable profession, and your present skills and choices can change the expression of your calling.')
 items+=block('Your destiny as an invitation','Ask: “What contribution would make me more honest, more alive, and more useful to the people I care about?” A meaningful path can include employment, creative work, study, care, leadership, or a quiet commitment. You do not need a public spiritual identity to fulfill a worthwhile purpose.')
 items.append(small('Close scores suggest a blend, not a single dominant role. These are transparent NEU reflection scores, not a standardized psychological test.'))
 paint(2,sections[1],items)
 # 3: disclosed hardship and genuine personal context; astrology subtle and uncertainties explicit.
 items=block('Acknowledge the life you have actually lived',hardship_text(context))
 items+=block('Alchemize experience through choice','You can choose what you learn from an experience without calling the pain necessary, deserved, or spiritually required. Turn one insight into an observable practice: a clearer boundary, a more inclusive invitation, a steadier routine, or a small act of service. Keep support available, and share only what you want to share.')
 if context.get('skills'):items+=block('Skills and experience you named',context['skills']+' These are your self-reported strengths. Choose one you can demonstrate in a small portfolio piece or supervised practice; the assessment does not verify qualifications.')
 if context.get('audience'):items+=block('The people you want to serve',context['audience']+' Speak with people in this group about their actual needs before deciding what they should want. Let their feedback shape the contribution.')
 if context.get('intention'):items+=block('Your intention for the next chapter',context['intention']+' Use this as a direction for experiments, rather than a standard you must achieve immediately.')
 if birth:
  record=f'Birth context: {birth["dob"]}; '+(birth.get('time','')+' local time' if birth.get('timeKnown') else 'time unknown')+'; '+birth.get('place','confirmed birthplace')+'; '+birth.get('timezone','')+'.'
  items.append(small(record))
 if astro:
  t=f'Sun: {astro["sun"]["sign"]}. Moon: {astro["moon"]["sign"]}.'
  if astro.get('ascendant'):t+=f' Ascendant: {astro["ascendant"]["sign"]}.'
  items+=block('A subtle birth-pattern reflection',t+' '+astro['sun']['reflection'])
  items.append(para(safe(astro['uncertainty']),9.2))
  items.append(small('Method: '+astro['method']+' Astrological meanings are traditional / NEU interpretations, not evidence of celestial ancestry.'))
 else:items+=block('Birth-pattern reflection','Birth details were not included. No sign, degree, or ascendant has been invented. Your reflection is based on your answers and the practical context you chose.')
 items+=block('One reflection to carry forward','What did your life teach you to notice, and how could you meet that need with appropriate skill and healthy limits? You are free to choose a different meaning, seek support, or begin with something unrelated to a hardship.')
 paint(3,sections[2],items)
 # 4: all top-three career options, entry path and scope; income realism without earnings predictions.
 items=[para('These paths connect your strongest roles with work that people actually do. Some are conventional job titles; others are independent spiritual or creative practices. Investigate demand, training, local requirements, and your capacity before investing heavily.'),Spacer(1,2)]
 for r in roles:
  items.append(head(r['name']))
  items.append(para(' · '.join(safe(x) for x in r['careers']),10.2,BOLD))
  items.append(para(safe(r['firstStep']),9.5))
  items.append(para(safe('Possible service pilot: '+r['offer']),9.5))
 work={'employment':'Start with real vacancies and volunteer or supervised entry routes. Match your resume to observable skills, and build one portfolio example. An adjacent administrative, creative, or community role can support your spiritual interests while providing employment.','independent':'Choose one specific audience and need. Offer a small service with a clear format, scope, price, and feedback process. Avoid launching a full course before testing whether people value a smaller workshop, creative product, or practice session.','mixed':'Combine a realistic employment path with a small independent practice. Keep separate schedules and finances so testing a spiritual offer remains manageable and does not undermine your current responsibilities.'}[context['workMode']]
 items+=block('Your preferred livelihood route',work)
 income={'exploring':'Because you are exploring without an immediate earnings requirement, compare two paths through conversations and small experiments before purchasing an extensive training.','supplement':'Because you want supplementary income, start with a low-overhead offer or a part-time role. Track time, costs, actual demand, and what people return for.','soon':'Because reliable income matters soon, prioritize paid roles that fit your current demonstrated skills. Keep a spiritual practice pilot small while you investigate qualifications and demand; a new spiritual business may not provide immediate reliable income.'}[context['incomeNeed']]
 items.append(para(safe(income),9.5))
 items+=block('Training, scope, and ethical service','Coaching, ceremony, contemplative sound, spiritual teaching, and art are distinct from regulated clinical practice. Counseling, bodywork, work with children, professional architecture, and some guiding roles can require credentials, licensing, safeguarding, insurance, or supervision. Verify local requirements. Offer only what you can competently deliver, and describe the experience without promising medical treatment, guaranteed transformation, or guaranteed earnings.')
 paint(4,sections[3],items)
 # 5: actionable personal capacity, visibility, money experiment, mentor and review prompts, method notes.
 items=[para('Choose one contribution to test. Your next chapter can begin with useful evidence of practice: a conversation, a small portfolio piece, a supervised session, or an invitation that meets a real need.'),Spacer(1,2)]
 for step in purpose['plan']:
  items.append(head(step['period']+' · '+step['title']))
  items.append(para(safe(step['action']),9.6))
 items+=block('Questions for a mentor','What preparation and boundaries matter in this work? What can a beginner safely practice? What qualifications do employers or clients expect? Where can I find supervised experience? What do people actually pay for, and what is a realistic first offer?')
 items+=block('Review after 30 days','Which activity gave you energy? Which contribution was useful to someone else? What feedback challenged your assumptions? What needs further training? Continue, adjust, or change direction using what you learned. A purpose that develops through real relationship can remain spiritual and practical at the same time.')
 items.append(small('Research and matching notes: '+heritage['method']+' '+purpose['method']))
 sources=list(dict.fromkeys(p['source'] for p in lineages))
 items.append(small('Celestial context: '+ '; '.join(sources)+'. Role taxonomy: owner-supplied New Earth Archetypes. Career and action interpretations: New Earth University editorial design. No exact personal soul-origin claim is made.'))
 items.append(small('To continue your practice: www.newearthuniversity.org/design-the-life-of-your-dreams'))
 paint(5,sections[4],items)
 c.save();return buffer.getvalue()
