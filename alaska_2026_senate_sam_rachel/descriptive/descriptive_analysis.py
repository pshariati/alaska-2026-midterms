"""Rachel-only linked descriptive analysis. No raw CVR/v1/v2 ballot input is read.

Candidate IDs and party labels are explicit static analysis annotations; Rachel's
files contain candidate names and no voter-party field. Lower-rank 'overvote'
tokens carry no candidate identities and remain unknown throughout this analysis.
"""
from pathlib import Path
from collections import Counter,defaultdict
import argparse,csv,gzip,hashlib,itertools,json,sqlite3,tempfile,datetime
R=Path(__file__).resolve().parent
ROOT=R.parent
J=lambda value:json.dumps(value,ensure_ascii=False,separators=(',',':'))
SLUGS={'governor':'Governor','us_house':'House','us_senate':'Senate'}
SENATE_IDS=[524,525,526,527]
ANNOTATIONS={
524:('Heikes, Gerald L.','Republican','us_senate'),525:('Peltola, Mary','Democrat','us_senate'),526:('Sullivan, Daniel J. Jr.','No listed affiliation','us_senate'),527:('Sullivan, Dan S.','Republican','us_senate'),373:('Write-in','Write-in','us_senate'),
528:('Begich, Nick','Republican','us_house'),529:('Hafner, Eric','Democrat','us_house'),530:('Hill, Bill','Nonpartisan','us_house'),531:('McDermott, James C. "Jim"','Libertarian','us_house'),374:('Write-in','Write-in','us_house'),
537:('Bronson/Church','Republican','governor'),538:('Kreiss-Tomkins/Johnson','Democrat/Nonpartisan','governor'),536:('Taylor/English','Republican','governor'),539:('Wilson/Shower','Republican','governor'),380:('Write-in','Write-in','governor')}
BY_NAME={slug:{v[0]:k for k,v in ANNOTATIONS.items() if v[2]==slug} for slug in SLUGS}
SPECIAL={'skipped','overvote'}

def digest(path):
 h=hashlib.sha256()
 with path.open('rb') as f:
  for b in iter(lambda:f.read(1048576),b''):h.update(b)
 return h.hexdigest()

def normalize_id(value):
 pieces=value.rstrip('_').split('_')
 if len(pieces)!=3 or not all(p.isdecimal() for p in pieces):raise ValueError(f'Unexpected ballotID: {value!r}')
 return ':'.join(str(int(p)) for p in pieces)

def prefix(tokens,slug):
 populated=[i for i,x in enumerate(tokens,1) if x!='skipped']
 if not populated:return [],'blank',None
 last=max(populated);out=[];empty=0
 for rank,token in enumerate(tokens[:last],1):
  if token=='skipped':
   empty+=1
   if empty>=2:return out,'two_consecutive_skips',rank
  elif token=='overvote':return out,'overvote',rank
  else:
   empty=0;candidate=BY_NAME[slug][token]
   if candidate not in out:out.append(candidate)
 return out,'end_of_ranks',None

def first(token,slug):
 return 'blank_rank1' if token=='skipped' else 'overvote_rank1' if token=='overvote' else BY_NAME[slug][token]

def category(p,d):
 if p is None and d is None:return 'neither_explicitly_ranked'
 if p is None:return 'senator_only_explicitly_ranked'
 if d is None:return 'peltola_only_explicitly_ranked'
 if p==d:return 'same_rank'
 return 'peltola_above_senator_both_ranked' if p<d else 'senator_above_peltola_both_ranked'

def comparison(tokens):
 p=next((i for i,x in enumerate(tokens,1) if x=='Peltola, Mary'),None)
 d=next((i for i,x in enumerate(tokens,1) if x=='Sullivan, Dan S.'),None)
 visible=category(p,d)
 hidden=[i for i,x in enumerate(tokens,1) if x=='overvote']
 possibilities=set()
 # Each unknown overvote can include neither finalist, P only, D only, or both.
 # All four projections are feasible because three other candidate rows exist.
 # No actual candidate identity is filled in or used in the main result.
 for projections in itertools.product(range(4),repeat=len(hidden)):
  pr=[p] if p else [];dr=[d] if d else []
  for rank,mask in zip(hidden,projections):
   if mask&1:pr.append(rank)
   if mask&2:dr.append(rank)
  possibilities.add(category(min(pr) if pr else None,min(dr) if dr else None))
 return visible,possibilities

def write_csv(path,rows):
 with path.open('w',newline='',encoding='utf-8') as f:
  w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)

def ingest(source):
 counts={};provenance={};token_counts={};normalization={}
 metadata={str(k):dict(name=v[0],party_label=v[1],contest=v[2],annotation_source='Static candidate-name/party reference annotations; not a field in Rachel CSVs and not voter party registration',id_source='Stable internal analysis identifier assigned explicitly by this script') for k,v in ANNOTATIONS.items()}
 (R/'candidate_metadata.json').write_text(json.dumps(metadata,indent=2,ensure_ascii=False))
 temp=tempfile.NamedTemporaryFile(prefix='rachel_link_',suffix='.sqlite',delete=False);dbpath=Path(temp.name);temp.close()
 db=sqlite3.connect(dbpath);db.execute('PRAGMA journal_mode=OFF');db.execute('PRAGMA synchronous=OFF')
 db.execute('CREATE TABLE ballots(contest TEXT, uid TEXT, row_index INT, raw_id TEXT, record_json TEXT, tokens_json TEXT, structural_json TEXT, alaska_json TEXT, PRIMARY KEY(contest,uid))')
 for slug,race in SLUGS.items():
  p=source/f'Alaska_20261103_US_{race}_11_11.csv';provenance[slug]=dict(filename=p.name,sha256=digest(p),bytes=p.stat().st_size);tokens_counter=Counter();n=0;modified=0
  with p.open(encoding='utf-8-sig',newline='') as f:
   reader=csv.DictReader(f);fields=reader.fieldnames
   if fields is None or len(fields)!=15:raise ValueError('Expected Rachel15-column schema')
   for i,row in enumerate(reader):
    uid=normalize_id(row['ballotID']);modified+=row['ballotID']!=uid
    tokens=[row[f'rank{r}'] for r in range(1,6)]
    unknown=set(tokens)-set(BY_NAME[slug])-SPECIAL
    if unknown:raise ValueError(f'Unknown Rachel rank tokens: {unknown!r}')
    tokens_counter.update(tokens);pref,reason,stop=prefix(tokens,slug);alaska=[x for x in pref if ANNOTATIONS[x][1]!='Write-in']
    try:db.execute('INSERT INTO ballots VALUES(?,?,?,?,?,?,?,?)',(slug,uid,i,row['ballotID'],J(row),J(tokens),J(pref),J(alaska)))
    except sqlite3.IntegrityError:raise ValueError(f'Duplicate/colliding normalized ID in {slug}: {uid}')
    n+=1
  db.commit();counts[slug]=n;token_counts[slug]=dict(tokens_counter);normalization[slug]=dict(normalized_ids=n,collisions=0,source_columns=fields)
 senate_ids={r[0] for r in db.execute("SELECT uid FROM ballots WHERE contest='us_senate'")}
 house_ids={r[0] for r in db.execute("SELECT uid FROM ballots WHERE contest='us_house'")}
 gov_ids={r[0] for r in db.execute("SELECT uid FROM ballots WHERE contest='governor'")}
 if senate_ids!=house_ids:raise ValueError('Senate and House ID sets differ; do not guess joins')
 if not gov_ids<=senate_ids:raise ValueError('Governor has unmatched extra IDs')
 missing=senate_ids-gov_ids
 columns=['ballot_uid','senate_source_row_index','governor_present_in_rachel_file']+[slug+'_'+field for slug in SLUGS for field in ['source_row_index','original_row_json','rank_tokens_json','structural_prefix_json','alaska_prefix_json','rank1_ambiguous_candidates','rank1_overvote_candidates']]
 query="""SELECT s.uid,s.row_index,s.record_json,s.tokens_json,s.structural_json,s.alaska_json,h.row_index,h.record_json,h.tokens_json,h.structural_json,h.alaska_json,g.row_index,g.record_json,g.tokens_json,g.structural_json,g.alaska_json FROM ballots s JOIN ballots h ON h.uid=s.uid AND h.contest='us_house' LEFT JOIN ballots g ON g.uid=s.uid AND g.contest='governor' WHERE s.contest='us_senate' ORDER BY s.row_index"""
 with gzip.open(R/'linked_ballots.csv.gz','wt',encoding='utf-8',newline='',compresslevel=1) as f:
  w=csv.DictWriter(f,fieldnames=columns);w.writeheader()
  for rec in db.execute(query):
   uid,si,srecord,stokens,spref,apref,*rest=rec
   row=dict(ballot_uid=uid,senate_source_row_index=si,governor_present_in_rachel_file=uid not in missing)
   for slug,values in [('us_senate',(si,srecord,stokens,spref,apref)),('us_house',rest[:5]),('governor',rest[5:])]:
    idx,original,tokens,pref,alaska=values;originalrow=json.loads(original) if original else None
    row[slug+'_source_row_index']=idx if idx is not None else ''
    row[slug+'_original_row_json']=original or '';row[slug+'_rank_tokens_json']=tokens or '';row[slug+'_structural_prefix_json']=pref or '';row[slug+'_alaska_prefix_json']=alaska or ''
    row[slug+'_rank1_ambiguous_candidates']=originalrow['rank1_ambiguous_candidates'] if originalrow else ''
    row[slug+'_rank1_overvote_candidates']=originalrow['rank1_overvote_candidates'] if originalrow else ''
   w.writerow(row)
 db.close();dbpath.unlink()
 result=dict(ballot_input_policy='ONLY the three Rachel CSVs. No old CVR, normalized CSV, linked GZ, or raw rank patterns are read.',inputs=provenance,rows=counts,id_join=dict(method='Normalize raw ballotID by stripping trailing underscores, split3decimal parts, integer-normalize each part, join with colon; join on normalized ID, not row position',senate_house_ids_identical=True,governor_subset_of_federal=True,missing_governor_rows=len(missing),normalization=normalization),rank_token_counts=token_counts,linked_gzip_sha256=digest(R/'linked_ballots.csv.gz'),script_sha256=digest(Path(__file__)),created_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),original_column_preservation='Every15-column original row retained as original_row_json, plus original input CSV files. Hidden lower-overvote identities remain unknown.')
 (R/'source_provenance.json').write_text(json.dumps(result,indent=2,ensure_ascii=False));return result

def analyze():
 cohort=Counter();sensitivity=Counter();legalq1=Counter();legal_sensitivity=Counter();q1=Counter();completeq1=Counter();sensitiveq1=Counter();possiblefreq=Counter();bounds=Counter();flags=Counter();crosstab=Counter();partytable=Counter();interpreted=Counter();interp_party=Counter();senate_patterns=Counter();prefix_patterns=Counter();total=0
 good={'peltola_above_senator_both_ranked','peltola_only_explicitly_ranked'}
 def party(x):return ANNOTATIONS[x][1] if isinstance(x,int) else x
 def label(x):return ANNOTATIONS[x][0] if isinstance(x,int) else x
 with gzip.open(R/'linked_ballots.csv.gz','rt',encoding='utf-8',newline='') as f:
  for row in csv.DictReader(f):
   total+=1;tokens=json.loads(row['us_senate_rank_tokens_json']);pref=json.loads(row['us_senate_structural_prefix_json']);apref=json.loads(row['us_senate_alaska_prefix_json'])
   s=first(tokens[0],'us_senate');si=pref[0] if pref else 'no_interpretable_first_choice';cohort[s]+=1;sensitivity[si]+=1;senate_patterns[tuple(tokens)]+=1;prefix_patterns[tuple(pref)]+=1
   if s==526:
    lp=apref.index(525) if 525 in apref else None
    ld=apref.index(527) if 527 in apref else None
    legalq1[category(lp,ld)]+=1
    visible,poss=comparison(tokens);q1[visible]+=1;completeq1['overvote_identity_unavailable' if 'overvote' in tokens else visible]+=1;possiblefreq[tuple(sorted(poss))]+=1
    bounds['definite_both_ranked_peltola_above']+=poss=={'peltola_above_senator_both_ranked'}
    bounds['possible_both_ranked_peltola_above']+='peltola_above_senator_both_ranked' in poss
    bounds['definite_peltola_before_or_senator_unranked']+=poss<=good
    bounds['possible_peltola_before_or_senator_unranked']+=bool(poss&good)
    bounds['comparison_unresolved_due_hidden_overvote']+=len(poss)>1
    flags['lower_overvote_ballots']+='overvote' in tokens[1:]
    flags['nonempty_rank1_ambiguous_metadata']+=bool(row['us_senate_rank1_ambiguous_candidates'])
    choice=next((x for x in apref if x in [525,527]),None);flags['transfer_to_peltola' if choice==525 else 'transfer_to_senator' if choice==527 else 'transfer_to_neither_finalist']+=1
   if si==526:
    sensitiveq1[comparison(tokens)[0]]+=1
    lp=apref.index(525) if 525 in apref else None
    ld=apref.index(527) if 527 in apref else None
    legal_sensitivity[category(lp,ld)]+=1
   for slug in ['governor','us_house']:
    tt=json.loads(row[slug+'_rank_tokens_json']) if row[slug+'_rank_tokens_json'] else None
    cp=json.loads(row[slug+'_structural_prefix_json']) if row[slug+'_structural_prefix_json'] else None
    x=first(tt[0],slug) if tt is not None else 'not_in_governor_file'
    xi=cp[0] if cp else ('not_in_governor_file' if tt is None else 'no_interpretable_first_choice')
    if s in SENATE_IDS:crosstab[(s,slug,str(x))]+=1;partytable[(s,slug,party(x))]+=1
    if si in SENATE_IDS:interpreted[(si,slug,str(xi))]+=1;interp_party[(si,slug,party(xi))]+=1
 for counts,denom,name,partymode in [(crosstab,cohort,'first_choice_candidate_crosstabs.csv',False),(partytable,cohort,'first_choice_party_crosstabs.csv',True),(interpreted,sensitivity,'interpreted_first_choice_candidate_sensitivity.csv',False),(interp_party,sensitivity,'interpreted_first_choice_party_sensitivity.csv',True)]:
  rows=[]
  for (s,slug,value),n in sorted(counts.items()):
   x=int(value) if value.isdecimal() else value
   rows.append(dict(senate_candidate_id=s,senate_candidate=label(s),senate_cohort_n=denom[s],other_contest=slug,other_first_choice=value if partymode else label(x),other_candidate_id='' if partymode or not isinstance(x,int) else x,other_party=value if partymode else party(x),ballots=n,pct_of_senate_cohort=100*n/denom[s]))
  for s in SENATE_IDS:
   for slug in ['governor','us_house']:assert sum(n for (cid,con,x),n in counts.items() if cid==s and con==slug)==denom[s]
  write_csv(R/name,rows)
 assert sum(cohort.values())==total and sum(q1.values())==cohort[526]
 result=dict(primary_analysis='Alaska-countable preference prefixes; original visible-name statistics retained only as supplementary descriptions',question1_usable_prefix_categories=dict(legalq1),question1_structural_cohort_usable_categories=dict(legal_sensitivity),total_linked_ballots=total,literal_rank1_senate_cohorts={label(k):v for k,v in cohort.items()},structural_first_choice_senate_cohorts={label(k):v for k,v in sensitivity.items()},question1_literal_rank1_daniel_j_n=cohort[526],question1_visible_named_slot_categories=dict(q1),question1_complete_identity_categories=dict(completeq1),question1_partial_information_bounds=dict(bounds),question1_flags_and_finalist_transfers=dict(flags),question1_structural_first_choice_daniel_j_n=sensitivity[526],question1_structural_cohort_visible_named_categories=dict(sensitiveq1),question1_hidden_overvote_possible_category_frequencies=[dict(possible_categories=list(k),ballots=n) for k,n in sorted(possiblefreq.items())],definitions=dict(primary_preference_rule='Keep valid ranks before first overvote or second consecutive internal skip; collapse repeated candidates; exclude unresolved generic write-ins only after evaluating original occupied ranks. Do not discard earlier valid preferences or the ballot.',primary_cohort='The same literal Rachel rank1 Daniel J. cohort is retained for comparability; first-usable-choice cohort sensitivity is separately labeled.',first_choice='Literal Rachel rank1 named candidate; skipped and overvote remain separate categories. Main ranking cells take precedence; original ambiguity metadata remain flags, not silently interpreted votes.',hidden_overvotes='Lower overvote tokens do not identify candidates. Explicit-slot comparisons are only observed named slots; absence from those slots is not absence from hidden overvotes.',definite_comparison='Same strict both-ranked ordering holds for every projected Peltola/Dan membership consistent with hidden overvote tokens.',bounds='Enumerates only feasible finalist-membership projections of each hidden overvote, without reconstructing identities. Bounds are partial-information sensitivity, not counts of actual hidden identities.',partisanship='Static chosen-candidate party annotations, not voter party registration. Rachel files contain no voter party variable.',governor_missing='Row absent from Rachel governor CSV after ID join. Not filled from another source and not coded as an undervote.',sensitivity='Structural-prefix first choice in all3contests, promoting single skipped ranks, preserving generic Write-in; overvote tokens stop subsequent interpretation.'))
 assert sum(legalq1.values())==cohort[526] and sum(legal_sensitivity.values())==sensitivity[526]
 legalrows=[dict(category=k,ballots=n,pct_of_literal_daniel_cohort=100*n/cohort[526]) for k,n in sorted(legalq1.items())]
 write_csv(R/'usable_preference_comparison.csv',legalrows)
 (R/'descriptive_results.json').write_text(json.dumps(result,indent=2,ensure_ascii=False))
 (R/'input_rank_patterns.json').write_text(json.dumps([dict(rank_tokens=list(k),ballot_count=n) for k,n in sorted(senate_patterns.items())],indent=2,ensure_ascii=False))
 (R/'structural_preference_patterns.json').write_text(json.dumps([dict(prefix_ids=list(k),ballot_count=n) for k,n in sorted(prefix_patterns.items())],indent=2))
 print(json.dumps(result,indent=2));return result

if __name__=='__main__':
 parser=argparse.ArgumentParser();parser.add_argument('--source',type=Path,default=ROOT/'inputs');parser.add_argument('--reuse-linked',action='store_true');args=parser.parse_args()
 if not args.reuse_linked:ingest(args.source)
 analyze()
