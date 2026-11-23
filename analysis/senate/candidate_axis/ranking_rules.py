"""Rank interpretation of Rachel's CSV tokens only; no prior CVR data is read.

The IDs in this module are analysis lookup labels assigned to Rachel's candidate
names, not identifiers claimed to appear in Rachel's CSV.
"""
NAME_TO_INTERNAL_ID={
    'Heikes, Gerald L.':524,
    'Peltola, Mary':525,
    'Sullivan, Daniel J. Jr.':526,
    'Sullivan, Dan S.':527,
    'Write-in':373,
}

def interpret_tokens(tokens):
    tokens=[str(x).strip() for x in tokens]
    unknown=[x for x in tokens if x not in NAME_TO_INTERNAL_ID and x not in ['skipped','overvote','']]
    if unknown:raise ValueError(f'Unknown Rachel CSV token(s): {unknown}')
    occupied=[i for i,t in enumerate(tokens,1) if t not in ['skipped','']]
    if not occupied:return [],'blank',None
    last=max(occupied);pref=[];blanks=0
    for rank,token in enumerate(tokens[:last],1):
        if token in ['skipped','']:
            blanks+=1
            if blanks>=2:return pref,'two_consecutive_skips',rank
            continue
        blanks=0
        if token=='overvote':return pref,'overvote',rank
        candidate=NAME_TO_INTERNAL_ID[token]
        if candidate not in pref:pref.append(candidate)
    return pref,'end_of_ranks',None
