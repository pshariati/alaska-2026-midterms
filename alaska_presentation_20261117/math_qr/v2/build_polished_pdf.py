from pathlib import Path
from io import BytesIO
import json
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak, Table, TableStyle, Flowable, KeepTogether
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib import colors
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from pypdf import PdfReader, PdfWriter, Transformation

BASE=Path(__file__).parent
pdfmetrics.registerFont(TTFont('Body','/System/Library/Fonts/Supplemental/Arial.ttf'))
pdfmetrics.registerFont(TTFont('BodyBold','/System/Library/Fonts/Supplemental/Arial Bold.ttf'))
pdfmetrics.registerFontFamily('Body',normal='Body',bold='BodyBold',italic='Body',boldItalic='BodyBold')
NAVY=colors.HexColor('#24384F');MUTED=colors.HexColor('#526A80');TEAL=colors.HexColor('#147E83');LINE=colors.HexColor('#D4DFE8');PALE=colors.HexColor('#F1F5F8')
styles={
'title':ParagraphStyle('title',fontName='BodyBold',fontSize=25,leading=29,textColor=NAVY,spaceAfter=10),
'deck':ParagraphStyle('deck',fontName='Body',fontSize=11,leading=16,textColor=MUTED,spaceAfter=14),
'step':ParagraphStyle('step',fontName='BodyBold',fontSize=14,leading=18,textColor=NAVY,spaceBefore=12,spaceAfter=7),
'body':ParagraphStyle('body',fontName='Body',fontSize=10.5,leading=14.4,textColor=NAVY,spaceAfter=7),
'note':ParagraphStyle('note',fontName='Body',fontSize=8.8,leading=12.4,textColor=MUTED,spaceAfter=8),
'label':ParagraphStyle('label',fontName='BodyBold',fontSize=9.1,leading=12,textColor=TEAL,spaceAfter=4),
'cell':ParagraphStyle('cell',fontName='Body',fontSize=9.6,leading=13,textColor=NAVY),
'headcell':ParagraphStyle('headcell',fontName='BodyBold',fontSize=9.3,leading=12,textColor=colors.white),
}
placements=[]
story=[]
def P(t,style='body'):story.append(Paragraph(t,styles[style]))
def Eq(name):story.append(VectorEquation(name))
class VectorEquation(Flowable):
 def __init__(self,name):
  Flowable.__init__(self);self.name=name;pg=PdfReader(BASE/'equations'/f'{name}.pdf').pages[0];self.ow=float(pg.mediabox.width);self.oh=float(pg.mediabox.height)
 def wrap(self,availW,availH):
  self.scale=min(1,availW/self.ow);self.width=availW;self.height=self.oh*self.scale+6;return self.width,self.height
 def draw(self):
  x,y=self.canv.absolutePosition((self.width-self.ow*self.scale)/2,3)
  placements.append({'page':self.canv.getPageNumber()-1,'name':self.name,'x':x,'y':y,'scale':self.scale})
class SenateAxis(Flowable):
 def wrap(self,aw,ah):self.width=aw;self.height=75;return aw,75
 def draw(self):
  c=self.canv;x0=34;span=self.width-68;y=37
  c.setLineWidth(1.5);c.setStrokeColor(LINE);c.line(x0,y,x0+span,y)
  data=[('Peltola',0,'#347CB1'),('Dan J.',.4363060892776858,'#D9A12C'),('Heikes',.7511664584004958,'#BA5054'),('Daniel S.',1,'#BA5054')]
  for i,(label,pos,color) in enumerate(data):
   x=x0+span*pos;c.setFillColor(colors.HexColor(color));c.circle(x,y,4,fill=1,stroke=0);c.setFillColor(NAVY);c.setFont('BodyBold',9.5);yy=58 if i%2==0 else 15;c.drawCentredString(x,yy,label);c.setFont('Body',9);c.drawCentredString(x,yy-13,f'{pos:.3f}')
def Tbl(data,widths,head=True):
 vals=[[Paragraph(str(v),styles['headcell'] if head and i==0 else styles['cell']) for v in row] for i,row in enumerate(data)]
 t=Table(vals,colWidths=widths,hAlign='LEFT');cmd=[('VALIGN',(0,0),(-1,-1),'MIDDLE'),('LEFTPADDING',(0,0),(-1,-1),10),('RIGHTPADDING',(0,0),(-1,-1),10),('TOPPADDING',(0,0),(-1,-1),7),('BOTTOMPADDING',(0,0),(-1,-1),7)]
 if head:cmd.extend([('BACKGROUND',(0,0),(-1,0),NAVY),('ROWBACKGROUNDS',(0,1),(-1,-1),[colors.white,PALE])])
 else:cmd.append(('LINEBELOW',(0,0),(-1,-1),.5,LINE))
 t.setStyle(TableStyle(cmd));story.append(t);story.append(Spacer(1,7))
def footer(c,d):
 c.saveState();c.setFillColor(TEAL);c.rect(48,750,22,3,fill=1,stroke=0);c.setFont('BodyBold',8);c.drawString(79,748,'ALASKA 2026  /  MATHEMATICAL METHODS')
 c.setStrokeColor(LINE);c.setLineWidth(.5);c.line(48,42,564,42);c.setFillColor(MUTED);c.setFont('Body',8);c.drawString(48,27,'Rachel/FairVote November 11 snapshot | Revised November 17, 2026');c.drawRightString(564,27,f'{d.page} / 4');c.restoreState()

P('From ranked ballots<br/>to a candidate axis','title')
P('The six-step method behind the one-dimensional MDS analysis','deck')
P('Multidimensional scaling (MDS) summarizes candidate relationships on a line. Here the relationships come from ballot rankings; the resulting coordinate is a model of preference structure, not a calibrated ideology measurement.')
P('01  Represent the valid named rankings','step');Eq('ranking')
P('Apply Alaska\'s overvote, skipped-rank and repeated-name rules before omitting generic write-ins from the named sequence. Preserve the original rank cells. Unranked candidates impose no additional preference comparisons.')
Tbl([['Symbol','Meaning'],['b; w<sub>b</sub>','A distinct ranking pattern; the number of ballots with that pattern'],['R<sub>b</sub>; l<sub>b</sub>','Its ordered candidate sequence; its number of named candidates'],['i, j; m','Candidate indices; total number of modeled candidates (four per race)']],[110,406])
P('02  Count candidate-pair relationships','step');Eq('corank');Eq('adjacency')
P('C<sub>ij</sub> counts ballots ranking both candidates. A<sub>ij</sub> counts ballots where j immediately follows i. The indicator <b>1</b>{condition} is 1 when its condition holds and 0 otherwise; w<sub>b</sub> supplies the ballot weight.')
P('Adjacency is measured in the valid named sequence. It can cross a permitted blank rank or an omitted generic write-in after the ranking barriers have been applied.','note')
story.append(PageBreak())

P('Fit the candidate relationships','title')
P('From pairwise association to positions on a single line','deck')
P('03  Convert adjacency into dissimilarity','step');Eq('similarity');Eq('dissimilarity')
P('Set F<sub>ij</sub> = 0 when C<sub>ij</sub> = 0. S<sub>ij</sub> combines both adjacency directions: larger values indicate more frequent adjacency relative to co-ranking. The inverse-square-root transform turns greater association into smaller dissimilarity.')
P('Zero-similarity convention. For an off-diagonal pair with S<sub>ij</sub> = 0, the code substitutes 2 / S<sub>min</sub><super>+</super>, where S<sub>min</sub><super>+</super> is the smallest positive similarity. If there is no positive similarity, no axis is fitted. This is a finite implementation convention, not a measured distance.','note')
P('04  Fit a one-dimensional nonmetric MDS model','step');Eq('distance')
P('Each candidate receives a fitted coordinate x<sub>i</sub>. Nonmetric MDS seeks distances that approximately preserve the ordering of the input dissimilarities. Conceptually, the fitting loss is:')
Eq('loss')
P('Here f is an order-preserving transformation. The solver alternates isotonic regression and coordinate updates, with scale normalization. Repeated starts address local solutions; they do not guarantee a global optimum.')
P('Reported diagnostic: normalized Stress-1','label');Eq('stress1')
P('The saved fits use scikit-learn 1.6.1. In this exact diagnostic formula, d is the distance matrix at the solver\'s stress-evaluation step and d-hat is its normalized disparity matrix. The conceptual symmetric loss above is not the literal diagnostic returned by that version. Its disparity construction and stopping rule are version-specific. Stress measures fit to pair dissimilarities; gamma measures ballot compatibility.','note')
story.append(PageBreak())

P('Stabilize and scale the axis','title')
P('Repeated fits establish a common orientation and candidate ordering','deck')
P('05  Repeat, align and average','step');Eq('center')
P('Center each outer run r and align mirrored configurations; reflection preserves distances. Exclude nonfinite or collapsed configurations and coincident candidate positions under the numerical tolerance.')
P('Select the most frequent candidate order. R* denotes the aligned outer runs with that order. Average their centered coordinates:')
Eq('mean')
P('Break ties between modal orders by lower mean reported stress, then deterministically by candidate order. Average only runs with the selected order, before 0-to-1 normalization.')
P('Saved fit settings','label')
Tbl([['Outer runs','Initializations per run','Iteration limit','Tolerance'],['20','8','1,000','10<super>-6</super>']],[112,164,120,120])
P('Each outer run retains its best of eight initializations. Modal-order selection uses 20 outputs.','note')
P('06  Normalize and orient the displayed axis','step');Eq('normalize')
P('The minimum averaged coordinate becomes 0 and the maximum becomes 1. A display reflection changes direction without changing distances. Each election is fitted and normalized separately.')
P('Example: the saved Senate candidate axis','label');story.append(SenateAxis())
P('Dan J. denotes the outsider; Daniel S. denotes the incumbent. Original source names remain preserved in the data. The fitted axis is not a shared numerical ideology scale across elections.','note')
story.append(PageBreak())

P('Evaluate the ranking structure','title')
P('Consistency is evaluated after the candidate axis has been fitted','deck')
P('Consistent and inconsistent rankings','step')
P('A ranking is consistent with the fitted distance model if some voter position u makes its named candidates strictly increasing in distance, in the recorded order:')
Eq('compatibility')
P('If no such position exists, the ranking is spatially inconsistent. This is a statement about the model, not the ballot\'s eligibility under Alaska\'s counting rules. A compatible strict ranking has a nonzero-width feasible interval; the code uses a 10<super>-12</super> numerical tolerance.')
P('Gamma: the share of a stated ballot group that fits','step');Eq('gamma')
P('G identifies the scoring group. Empty named sequences are excluded. One- and two-name rankings automatically pass this test because unranked candidates impose no comparisons. The main results therefore emphasize three- and four-name rankings.')
Tbl([['Senate scoring group','Ballots','Observed gamma','Random mean'],['Three or four names','45,743','61.54%','41.57%'],['All nonempty rankings','243,006','92.76%','89.00%']],[186,86,122,122])
P('Random comparison: 49 datasets preserve the exact first-choice-by-ranking-length counts and randomize distinct later candidates uniformly without replacement. Each dataset receives its own fitted axis. The random mean is the average of those 49 consistency values.','note')
P('Estimated voter positions are a separate plotting step','step')
P('Under Mahshad\'s convention, n ballots with a compatible ranking are allocated evenly across the <b>closed interval</b> between its feasible bounds; single-name rankings are placed at their candidate. Interval endpoints can give distance ties. Their inclusion is a plotting convention; gamma still tests strict compatibility. Estimated voter positions are not uniquely recovered individual locations.')
P('Sources and scope','label')
P('Project: common/og_axis.py; axis_models/run_axes.py; voter_distributions/run_distributions.py; saved Senate model results. Ballot inputs: Rachel/FairVote\'s November 11, 2026 CSV snapshot. No ballot inputs, fitted coordinates or gamma results were changed for this document.','note')
P('<link href="https://scikit-learn.org/1.6/modules/generated/sklearn.manifold.MDS.html" color="#147E83">MDS documentation (scikit-learn 1.6.1)</link>  |  <link href="https://github.com/scikit-learn/scikit-learn/blob/1.6.1/sklearn/manifold/_mds.py" color="#147E83">Exact solver source</link>  |  <link href="https://www.elections.alaska.gov/election-information/" color="#147E83">Alaska ranking rules</link>','note')

raw=BytesIO()
doc=SimpleDocTemplate(raw,pagesize=(612,792),rightMargin=48,leftMargin=48,topMargin=61,bottomMargin=57,title='Alaska MDS: Mathematical Methods',author='Pejmon Shariati')
doc.build(story,onFirstPage=footer,onLaterPages=footer)
reader=PdfReader(raw);writer=PdfWriter()

for i,pg in enumerate(reader.pages):
 print('PAGE',i+1,pg.extract_text()[:120].replace('\n',' '),' ... ',pg.extract_text()[-150:].replace('\n',' '))
assert len(reader.pages)==4, f'Expected four pages; got {len(reader.pages)}'
for idx,page in enumerate(reader.pages):
 for q in [a for a in placements if a['page']==idx]:
  ep=PdfReader(BASE/'equations'/f"{q['name']}.pdf").pages[0]
  page.merge_transformed_page(ep,Transformation().scale(q['scale']).translate(q['x'],q['y']))
 writer.add_page(page)
writer.add_metadata({'/Title':'Alaska MDS: Mathematical Methods','/Author':'Pejmon Shariati','/Subject':'Six-step candidate-axis method, consistency and plotting conventions','/Keywords':'MDS, ranked ballots, Alaska, mathematical methods'})
out=BASE/'Alaska_MDS_Mathematical_Methods.pdf'
with out.open('wb') as f:writer.write(f)
(BASE/'equation_placements.json').write_text(json.dumps(placements,indent=2))
print('Built polished PDF:',len(reader.pages),'pages;',len(placements),'vector equations')
