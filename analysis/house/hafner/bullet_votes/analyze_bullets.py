"""Strict Hafner bullet cohort; literal rank1 choices in Senate and governor.

Only FairVote's pinned November11 CSVs are inputs. No source/notebook mutation.
"""
from pathlib import Path
from collections import Counter
import csv,json,sys,gzip,hashlib

from analysis.shared.paths import race_dir
BASE=race_dir('us_house')/'hafner'/'bullet_votes'
from analysis.shared.data import read_rows,normalized_id,RACES,source_path,sha256
H='Hafner, Eric';P='Peltola, Mary';K='Kreiss-Tomkins/Johnson';MISSING='Missing contest record'
LABEL={'Peltola, Mary':'Mary Peltola','Sullivan, Dan S.':'Daniel S. (incumbent)',
       'Sullivan, Daniel J. Jr.':'Dan J. (outsider)','Heikes, Gerald L.':'Gerald Heikes',
       'Kreiss-Tomkins/Johnson':'Kreiss-Tomkins / Johnson','Wilson/Shower':'Wilson / Shower',
       'Bronson/Church':'Bronson / Church','Taylor/English':'Taylor / English',
       'skipped':'Blank first rank','overvote':'First-rank overvote','Write-in':'Write-in',MISSING:MISSING}

def main():
    house={};seen=set();total=0;hafner_first=0;broader_named_only=0
    for index,row,tokens in read_rows('us_house'):
        total+=1;uid=normalized_id(row['ballotID']);assert uid not in seen;seen.add(uid)
        if tokens[0]==H:
            hafner_first+=1
            if tokens[1:]==('skipped',)*4:house[uid]=(index,row)
    n=len(house);assert n==7707 and hafner_first==17918 and total==244705
    other={};joins={};counts={};missing={};annotations={}
    for race in ['us_senate','governor']:
        records={};full_seen=set();annot=Counter()
        for index,row,tokens in read_rows(race):
            uid=normalized_id(row['ballotID']);assert uid not in full_seen;full_seen.add(uid)
            if uid in house:
                records[uid]={'source_row_index':index,'raw_row':row,'rank1':tokens[0]}
                for field in ['rank1_ambiguous_candidates','rank1_overvote_candidates']:
                    if row[field]:annot[field]+=1
        other[race]=records
        counter=Counter(records[uid]['rank1'] if uid in records else MISSING for uid in house)
        assert sum(counter.values())==n
        counts[race]=dict(counter);missing[race]=counter[MISSING];annotations[race]=dict(annot)
        joins[race]={'full_source_rows':len(full_seen),'matched_cohort_records':len(records),'missing':n-len(records),'no_duplicate_normalized_ids':True}
    joint=Counter((other['us_senate'][uid]['rank1'] if uid in other['us_senate'] else MISSING,
                   other['governor'][uid]['rank1'] if uid in other['governor'] else MISSING) for uid in house)
    assert sum(joint.values())==n
    comparisons=[]
    for race,counter in counts.items():
        # Explicit zeros show the complete candidate/category mapping.
        categories=RACES[race]['names']+['Write-in','skipped','overvote',MISSING]
        for token in categories:
            v=counter.get(token,0)
            comparisons.append({'race':race,'recorded_rank1':token,'public_label':LABEL[token],
                                'ballots':v,'cohort_denominator':n,'percent':100*v/n})
    with (BASE/'first_choices.csv').open('w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(comparisons[0]));w.writeheader();w.writerows(comparisons)
    jointrows=[{'senate_rank1':a,'governor_rank1':b,'ballots':v,'denominator':n,'percent':100*v/n} for (a,b),v in joint.most_common()]
    with (BASE/'joint_first_choices.csv').open('w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(jointrows[0]));w.writeheader();w.writerows(jointrows)
    with gzip.open(BASE/'linked_bullet_ballots.jsonl.gz','wt',encoding='utf-8') as f:
        for uid,(index,row) in sorted(house.items()):
            f.write(json.dumps({'normalized_ballot_id':uid,'house_source_row_index':index,'house_original_row':row,
                     'senate':other['us_senate'].get(uid),'governor':other['governor'].get(uid)})+'\n')
    result={'cohort':'Literal House rank1 Hafner; ranks2–5 all skipped (blank)',
            'definition':'Strict bullet; excludes repeated Hafner rankings, write-ins and overvotes at later ranks.',
            'snapshot':'FairVote November11,2026','source_files':{race:{'path':str(source_path(race)),
            'sha256':sha256(source_path(race))} for race in ['us_house','us_senate','governor']},
            'cohort_n':n,'all_hafner_literal_first':hafner_first,'share_of_hafner_first':100*n/hafner_first,
            'all_house_records':total,'joins':joins,'counts':counts,'missing':missing,
            'rank1_annotation_counts':annotations,
            'both_Peltola_and_Kreiss_Tomkins_literal_first':joint[P,K],
            'both_percent':100*joint[P,K]/n,
            'counting_basis':'Literal recorded rank1 in each other race; lower ranks are not promoted. Blank first ranks, overvotes, write-ins and missing records remain separate. Every percentage uses all7707strict bullet ballots.',
            'scope':'Descriptive cross-race choices, not a measure of voter knowledge or motivation.'}
    (BASE/'results.json').write_text(json.dumps(result,indent=2))
    print(json.dumps(result,indent=2))
    return result

if __name__=='__main__':main()
