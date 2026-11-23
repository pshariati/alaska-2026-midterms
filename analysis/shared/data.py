"""Shared source definitions and Alaska-prefix preparation for the statewide analysis."""
from pathlib import Path
from collections import Counter
import csv,hashlib,json,re

from analysis.shared.paths import INPUTS_ROOT
SLUGS=['us_senate','governor','us_house']
RACES={
 'us_senate':{'filename':'Alaska_20261103_US_Senate_11_11.csv','title':'Senate',
 'sha256':'3f0a1a946f23d2d1195f98c5ee5f123916d5f91ede334397465692d5e7f2d972',
 'ids':[524,525,526,527],
 'names':['Heikes, Gerald L.','Peltola, Mary','Sullivan, Daniel J. Jr.','Sullivan, Dan S.']},
 'governor':{'filename':'Alaska_20261103_US_Governor_11_11.csv','title':'Governor',
 'sha256':'3d76cd612870025d9c470f78a60d0bde0cd274aeb9a4e57d575704b588f4b8b3',
 'ids':[537,538,536,539],
 'names':['Bronson/Church','Kreiss-Tomkins/Johnson','Taylor/English','Wilson/Shower']},
 'us_house':{'filename':'Alaska_20261103_US_House_11_11.csv','title':'House',
 'sha256':'b57fad2ef5a8845ba5b3da1eeb3c5e7cfb036c1c174af640b3acee65e45f8b48',
 'ids':[528,529,530,531],
 'names':['Begich, Nick','Hafner, Eric','Hill, Bill','McDermott, James C. "Jim"']}}
SENATE_LABELS={524:'Gerald Heikes',525:'Mary Peltola',526:'Daniel J. Sullivan Jr.',527:'Dan S. Sullivan'}
SENATE_ORDER=[525,526,524,527]

def sha256(path):
 h=hashlib.sha256()
 with Path(path).open('rb') as f:
  for chunk in iter(lambda:f.read(1048576),b''):h.update(chunk)
 return h.hexdigest()

def source_path(slug):return INPUTS_ROOT/RACES[slug]['filename']

def normalized_id(value):
 match=re.fullmatch(r'([0-9]+)_([0-9]+)_([0-9]+)_?',value)
 if not match:raise ValueError('Unrecognized ballot ID: '+repr(value))
 return ':'.join(str(int(part)) for part in match.groups())

def countable_tokens(tokens):
 """Keep occupied write-in ranks while applying barriers, then deduplicate names."""
 last=max((i for i,x in enumerate(tokens) if x!='skipped'),default=-1)
 result=[];skips=0;reason='blank' if last<0 else 'end_of_ranks';barrier_rank=None
 for i,token in enumerate(tokens[:last+1]):
  if token=='skipped':
   skips+=1
   if skips==2:reason='two_consecutive_skips';barrier_rank=i+1;break
   continue
  skips=0
  if token=='overvote':reason='overvote';barrier_rank=i+1;break
  if token not in result:result.append(token)
 return tuple(result),reason,barrier_rank

def read_rows(slug):
 path=source_path(slug)
 if not path.is_file():raise FileNotFoundError('Supply the pinned Rachel/FairVote November 11 input at '+str(path)+'; see docs/DATA.md')
 if sha256(path)!=RACES[slug]['sha256']:raise ValueError('Supplied source version changed: '+str(path))
 allowed=set(RACES[slug]['names'])|{'Write-in','skipped','overvote'}
 with path.open(encoding='utf-8-sig',newline='') as f:
  reader=csv.DictReader(f)
  if not all('rank'+str(i) in reader.fieldnames for i in range(1,6)):raise ValueError('Missing rank columns')
  for index,row in enumerate(reader):
   tokens=tuple(row['rank'+str(i)] for i in range(1,6))
   if set(tokens)-allowed:raise ValueError('Unknown token(s): '+str(set(tokens)-allowed))
   yield index,row,tokens

def profile(slug):
 counts=Counter();seen=set();reasons=Counter();rows=0
 names=RACES[slug]['names']
 for _,row,tokens in read_rows(slug):
  uid=normalized_id(row['ballotID'])
  if uid in seen:raise ValueError('Duplicate normalized ballot ID: '+uid)
  seen.add(uid);rows+=1
  pref,reason,_=countable_tokens(tokens);reasons[reason]+=1
  counts[tuple(names.index(x) for x in pref if x!='Write-in')]+=1
 assert sum(counts.values())==rows
 return dict(counts),{'source_filename':RACES[slug]['filename'],'source_sha256':RACES[slug]['sha256'],
  'source_rows':rows,'unique_normalized_ids':len(seen),'stop_reasons':dict(reasons),
  'candidate_ids_are_internal_annotations':True,'writein_removed_only_after_barriers':True}
