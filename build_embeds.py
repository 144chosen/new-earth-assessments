from pathlib import Path
import argparse
from urllib.parse import urlsplit
p=argparse.ArgumentParser();p.add_argument('--url',default='https://quiz.newearthuniversity.org');args=p.parse_args()
u=args.url.rstrip('/');parts=urlsplit(u)
if parts.scheme not in ['http','https'] or not parts.netloc or parts.path or parts.query or parts.fragment:raise SystemExit('Use the assessment service origin, without a path.')
base=Path(__file__).parent;dest=base/'kajabi';dest.mkdir(exist_ok=True)
for kind,title in [('heritage','Discover Your Celestial Heritage'),('purpose','The 144,000: Discover Your Role')]:
 ident='neu-'+kind
 text=f'''<!-- Host the included assessment service first; this is the Kajabi Custom Code embed. -->
<iframe id="{ident}" src="{u}/{kind}" title="{title}" style="display:block;width:100%;height:1250px;border:0;border-radius:12px;background:#070e20" loading="eager" allow="clipboard-write" referrerpolicy="strict-origin" ></iframe>
<p style="text-align:center;font-size:13px"><a href="{u}/{kind}" target="_blank" rel="noopener">Open assessment in a full window</a></p>
<script>
(function(){{
  var frame=document.getElementById('{ident}');
  var origin='{u}';
  window.addEventListener('message',function(event){{
    if(event.origin!==origin || event.source!==frame.contentWindow) return;
    var data=event.data;
    if(data && data.type==='neu-assessment-height' && Number.isFinite(data.height)){{
      frame.style.height=Math.min(60000,Math.max(850,Math.ceil(data.height)+20))+'px';
    }}
  }});
}})();
</script>
'''
 (dest/(kind+'-embed.html')).write_text(text)
print('Both Kajabi embed fragments generated for',u)
