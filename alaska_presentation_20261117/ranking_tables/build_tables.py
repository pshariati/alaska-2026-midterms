from pathlib import Path
import csv, json, html
from PIL import Image, ImageDraw, ImageFont

BASE=Path(__file__).resolve().parent
ROOT=BASE.parent.parent
SOURCE=ROOT/'alaska_2026_sam_followup_20261116/confusion/daniel_first_usable_permutations.csv'
rows=list(csv.DictReader(SOURCE.open()))
counts={tuple(json.loads(r['candidate_ids_json'])):int(r['literal_rank1_daniel_ballots']) for r in rows}
assert sum(counts.values())==3940
NAMES={526:'Dan J.',527:'Daniel S.',525:'Peltola',524:'Heikes'}
groups=[
 ('Daniel_S_next_to_Dan_J','Daniel S. immediately after Dan J.',
  'Peltola appears later in the valid named sequence',
  [(526,527,525),(526,527,525,524),(526,527,524,525)],263),
 ('Peltola_before_Daniel_S','Peltola before Daniel S.',
  'Heikes may appear between the named candidates',
  [(526,525,527),(526,525,527,524),(526,525,524,527),(526,524,525,527)],568)
]
FONT='/System/Library/Fonts/Supplemental/Arial.ttf'
BOLD='/System/Library/Fonts/Supplemental/Arial Bold.ttf'
def font(size,bold=False):return ImageFont.truetype(BOLD if bold else FONT,size)
navy='#24384F';muted='#526A80';pale='#F0F4F8';line='#CBD6DF'
manifest=[]
for stem,title,subtitle,patterns,total in groups:
 assert sum(counts[v] for v in patterns)==total
 im=Image.new('RGB',(1800,760),'white');d=ImageDraw.Draw(im)
 d.text((64,40),title,font=font(54,True),fill=navy)
 d.text((64,112),subtitle,font=font(32),fill=muted)
 x0,x1,y0,hh,rh=64,1736,188,66,78
 d.rectangle((x0,y0,x1,y0+hh),fill=navy)
 d.text((88,y0+14),'Ranking',font=font(32,True),fill='white')
 d.text((1705,y0+14),'Ballots',font=font(32,True),fill='white',anchor='ra')
 labels=[]
 for i,pat in enumerate(patterns):
  y=y0+hh+i*rh;label=' → '.join(NAMES[v] for v in pat);n=counts[pat]
  d.rectangle((x0,y,x1,y+rh),fill='white' if i%2==0 else pale)
  d.text((88,y+21),label,font=font(35),fill=navy)
  d.text((1705,y+21),f'{n:,}',font=font(35),fill=navy,anchor='ra')
  labels.append((label,n))
 y=y0+hh+len(patterns)*rh
 d.rectangle((x0,y,x1,y+rh),fill='#E3EBF2')
 d.text((88,y+21),'Total',font=font(35,True),fill=navy)
 d.text((1705,y+21),f'{total:,}  ({100*total/3940:.2f}%)',font=font(35,True),fill=navy,anchor='ra')
 d.line((64,676,1736,676),fill=line,width=2)
 d.text((64,696),'Base: 3,940 Dan J.-first ballots · Rachel/FairVote November 11 snapshot',font=font(27),fill=muted)
 im.save(BASE/(stem+'.png'))
 with (BASE/(stem+'.tsv')).open('w') as f:
  writer=csv.writer(f,delimiter='\t');writer.writerow(['Ranking','Ballots']);writer.writerows(labels);writer.writerow(['Total',total])
 # Vector version preserves sharp type at any size.
 el=[f'<svg xmlns="http://www.w3.org/2000/svg" width="1800" height="760" viewBox="0 0 1800 760"><rect width="1800" height="760" fill="white"/>']
 def txt(t,x,y,size=35,bold=False,fill=navy,anchor='start'):
  el.append(f'<text x="{x}" y="{y}" font-family="Arial,sans-serif" font-size="{size}" font-weight="{700 if bold else 400}" fill="{fill}" text-anchor="{anchor}">{html.escape(t)}</text>')
 txt(title,64,93,54,True);txt(subtitle,64,143,32,False,muted)
 el.append(f'<rect x="64" y="188" width="1672" height="66" fill="{navy}"/>')
 txt('Ranking',88,234,32,True,'white');txt('Ballots',1705,234,32,True,'white','end')
 for i,(label,n) in enumerate(labels):
  y=254+i*78;el.append(f'<rect x="64" y="{y}" width="1672" height="78" fill="{pale if i%2 else "white"}"/>');txt(label,88,y+53);txt(f'{n:,}',1705,y+53,anchor='end')
 y=254+len(labels)*78;el.append(f'<rect x="64" y="{y}" width="1672" height="78" fill="#E3EBF2"/>');txt('Total',88,y+53,bold=True);txt(f'{total:,}  ({100*total/3940:.2f}%)',1705,y+53,bold=True,anchor='end')
 el.append(f'<line x1="64" y1="676" x2="1736" y2="676" stroke="{line}" stroke-width="2"/>');txt('Base: 3,940 Dan J.-first ballots · Rachel/FairVote November 11 snapshot',64,723,27,False,muted);el.append('</svg>')
 (BASE/(stem+'.svg')).write_text('\n'.join(el))
 manifest.append({'file':stem,'rows':labels,'total':total,'denominator':3940,'percent':100*total/3940})
(BASE/'TABLE_VALUES.json').write_text(json.dumps(manifest,indent=2))
print('Both ranking tables rendered; source counts verified.')
