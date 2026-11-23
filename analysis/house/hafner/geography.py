"""Descriptive Hafner geography from Rachel's fixed November 11 House records."""
from pathlib import Path
from collections import Counter, defaultdict
import csv, datetime, hashlib, json, re
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import pandas as pd
from IPython.display import display, Markdown

from analysis.shared.paths import INPUTS_ROOT, race_dir
ROOT=race_dir('us_house')/'hafner'
OUT=ROOT/'geography'
HAFNER='Hafner, Eric'
AREA={4:'Downtown Juneau / Douglas',9:'South Anchorage / Turnagain Arm / Whittier',
      10:'Dimond / Oceanview',11:'Hillside',12:'Southeast Anchorage',13:'South Midtown',
      14:'North Midtown',15:'Southwest Anchorage',16:'West Anchorage',17:'Downtown Anchorage',
      18:'Government Hill / JBER / North Muldoon',19:'Mountainview / Airport Heights',
      20:'University / U-Med',21:'East Anchorage',22:'Northeast Anchorage',
      23:'Eagle River area',24:'Chugiak / Eagle River area',25:'Palmer / Butte',
      31:'Downtown Fairbanks',32:'East Fairbanks / Fort Wainwright',
      35:'College / Ester / Chena Ridge',38:'Lower Kuskokwim',39:'Bering Straits / Yukon Delta',
      40:'Arctic',99:'Federal overseas administrative category'}


def write_csv(name, rows):
    with (OUT/name).open('w',encoding='utf-8',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)


def main(render=True):
    OUT.mkdir(parents=True,exist_ok=True)
    path=INPUTS_ROOT/'Alaska_20261103_US_House_11_11.csv'
    digest=hashlib.sha256(path.read_bytes()).hexdigest()
    assert digest=='b57fad2ef5a8845ba5b3da1eeb3c5e7cfb036c1c174af640b3acee65e45f8b48'
    districts=defaultdict(Counter); independent=defaultdict(Counter)
    precincts=defaultdict(Counter); modes=defaultdict(Counter)
    geo_modes=Counter(); anchor=Counter(); admin9=Counter(); whittier=Counter()
    with path.open(encoding='utf-8-sig',newline='') as f:
        for row in csv.DictReader(f):
            label=row['precinct']
            physical=bool(re.match(r'^\d{2}-\d{3}\b',label))
            match=(re.match(r'^(\d{2})-\d{3}\b',label)
                   or re.match(r'^District\s+(\d+)\s*-',label)
                   or re.match(r'^HD(\d+)\b',label))
            assert match,label
            hd=int(match.group(1));h=int(row['rank1']==HAFNER)
            assert hd in set(range(1,41))|{99}
            # Separate parsing route: tolerate double spaces in Question batches.
            if label.startswith('District '): hd_check=int(label.split()[1])
            elif label.startswith('HD'):hd_check=int(label.split()[0][2:])
            else:hd_check=int(label.split('-')[0])
            assert hd==hd_check
            for counter in [districts[hd],independent[hd_check],precincts[label],modes[row['countingGroup']]]:
                counter['house_records']+=1;counter['hafner_first']+=h
            if physical:geo_modes[row['countingGroup']]+=1
            if 10<=hd<=24 or (hd==9 and physical and 'Whittier' not in label):
                anchor['house_records']+=1;anchor['hafner_first']+=h
            if hd==9 and not physical:
                admin9['house_records']+=1;admin9['hafner_first']+=h
            if hd==9 and physical and 'Whittier' in label:
                whittier['house_records']+=1;whittier['hafner_first']+=h
    assert districts==independent
    total=sum(x['house_records'] for x in districts.values())
    n=sum(x['hafner_first'] for x in districts.values())
    assert (total,n)==(244705,17918)
    assert geo_modes=={'Election Day':151244}
    existing={r['precinct']:(int(r['hafner_first_ballots']),int(r['all_house_records_in_precinct']))
              for r in csv.DictReader((ROOT/'hafner_by_precinct.csv').open())}
    assert existing=={k:(v['hafner_first'],v['house_records']) for k,v in precincts.items() if v['hafner_first']>0}
    def records(counter, key):
        return [{key:k,**dict(v),'pct_Hafner_of_house_records':100*v['hafner_first']/v['house_records'],
                 'pct_of_all_Hafner_first':100*v['hafner_first']/n} for k,v in counter.items()]
    ds=records(districts,'house_district')
    for row in ds:row['area_label']=AREA.get(row['house_district'],'House district '+str(row['house_district']))
    ds.sort(key=lambda r:-r['hafner_first'])
    ps=records(precincts,'precinct')
    for row in ps:row['is_geographic_precinct']=bool(re.match(r'^\d{2}-\d{3}\b',row['precinct']))
    ps.sort(key=lambda r:-r['hafner_first'])
    physical=[r for r in ps if r['is_geographic_precinct']]
    meaningful=sorted((r for r in physical if r['house_records']>=100),key=lambda r:-r['pct_Hafner_of_house_records'])
    by_share=sorted((r for r in ds if r['house_district']!=99),key=lambda r:-r['pct_Hafner_of_house_records'])
    all_shares=sorted(physical,key=lambda r:-r['pct_Hafner_of_house_records'])
    assert ds[0]['house_district']==21 and ds[0]['hafner_first']==653
    assert by_share[0]['house_district']==18 and by_share[0]['hafner_first']==304
    assert physical[0]['precinct']=='21-715 East Anchorage No. 3' and physical[0]['hafner_first']==129
    assert meaningful[0]['precinct']=='03-345 Skagway' and meaningful[0]['hafner_first']==68
    assert anchor['hafner_first']==8216 and admin9['hafner_first']==184 and whittier['hafner_first']==10
    write_csv('districts_all_voting_modes.csv',ds)
    write_csv('precincts_and_administrative_batches.csv',ps)
    write_csv('geographic_precincts_by_Hafner_votes.csv',physical)
    write_csv('geographic_precincts_by_share.csv',all_shares)
    write_csv('geographic_precincts_share_min100.csv',meaningful)
    write_csv('counting_groups.csv',records(modes,'counting_group'))
    result={'status':'passed','generated_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),
        'source_filename':path.name,'source_sha256':digest,'source_version':'Rachel November 11, 2026',
        'all_House_records':total,'Hafner_literal_first':n,'statewide_record_share_pct':100*n/total,
        'districts':ds,'geographic_districts_by_share':by_share,
        'geographic_precincts_by_count':physical,'geographic_precincts_by_share_min100':meaningful,
        'top_geographic_precincts_by_share_no_threshold':all_shares[:10],
        'counting_groups':records(modes,'counting_group'),
        'geographic_precincts_all_Election_Day':True,'geographic_precinct_records':151244,
        'geographic_precincts_present':len(physical),
        'Anchorage_identifiable_subset':dict(anchor),
        'HD9_pooled_batches_not_city_assignable':dict(admin9),'Whittier_geographic_precinct':dict(whittier),
        'checks':{'two_district_parsers_agree':True,'all_precinct_counts_match_existing_source_audit':True,
                  'all_244705_records_and_17918_Hafner_ballots_accounted_for':True},
        'geography_reference_urls':[
            'https://www.elections.alaska.gov/research/district-maps/',
            'https://www.elections.alaska.gov/doc/maps/2023-precincts/HD18_May2023Final_Maps.pdf',
            'https://www.elections.alaska.gov/doc/forms/H07.pdf'],
        'limits':['All shares divide by every House source record in the indicated group, including blanks and overvotes.',
            'Precinct names with numeric geographic codes are Election Day only in this file; district-level absentee/early/Question batches cannot be allocated to a town from these CSVs.',
            'HD99 is an overseas administrative category, not a geographic stronghold.',
            'The minimum100 threshold is only a presentation filter; all small precincts remain exported.',
            'Anchorage subset comprises all records in HD10-24 and geographically identifiable non-Whittier HD9 precincts; this is a conservative area grouping, not a precise citywide tally.',
            'H07 is a linked 2022 designation reference; exact area boundaries require the current maps. District/precinct counts themselves use only Rachel labels.',
            'This is a dated scanned snapshot, not final statewide or complete city totals. No demographic or voter-intent inference is made.']}
    (OUT/'results.json').write_text(json.dumps(result,indent=2)+'\n')
    if render:render_figure(result)
    return result


def render_figure(result):
    fig,axs=plt.subplots(1,2,figsize=(14,8))
    count=[r for r in result['districts'] if r['house_district']!=99][:10]
    shares=result['geographic_districts_by_share'][:10]
    for ax,rows,field,title,color in [(axs[0],count,'hafner_first','Most Hafner-first votes','#377fae'),
            (axs[1],shares,'pct_Hafner_of_house_records','Highest Hafner share','#8061aa')]:
        labels=[f'HD {r["house_district"]} · {r["area_label"]}' for r in rows]
        vals=[r[field] for r in rows]
        ax.barh(labels,vals,color=color,height=.58);ax.invert_yaxis()
        ax.set_title(title,loc='left',fontweight='bold',fontsize=14,pad=17)
        ax.set_xlim(0,max(vals)*1.32)
        for i,(v,r) in enumerate(zip(vals,rows)):
            text=f'{v:,}' if field=='hafner_first' else f'{v:.1f}% ({r["hafner_first"]:,}/{r["house_records"]:,})'
            ax.text(v+max(vals)*.02,i,text,va='center',fontsize=9)
        ax.spines[['top','right','left']].set_visible(False);ax.tick_params(axis='y',length=0,labelsize=9)
        ax.grid(axis='x',color='#e7edf2');ax.set_axisbelow(True)
        ax.set_xlabel('Hafner-first ballots' if field=='hafner_first' else 'Share of all district House records (%)')
    fig.suptitle('Where Eric Hafner received support',x=.035,y=.98,ha='left',fontsize=19,fontweight='bold')
    fig.text(.035,.925,'Rachel’s November 11 snapshot · State House districts, combining all recorded voting modes',fontsize=11)
    fig.text(.035,.04,'Counts and shares answer different questions. District 99 is an overseas administrative category and is excluded from these rankings.\nArea labels are descriptive; House districts do not always match cities. Original precinct and administrative categories remain separately exported.',fontsize=9,color='#61798e')
    fig.subplots_adjust(left=.21,right=.94,top=.84,bottom=.15,wspace=1.65)
    for ext in ['png','svg']:fig.savefig(OUT/f'hafner_district_strongholds.{ext}',dpi=180,facecolor='white')
    plt.close(fig)


def show_geography(result):
    from analysis.reporting import presentation as show
    display(Markdown('**Anchorage is the clearest concentration in these records.** The three districts with the most Hafner-first votes are **HD21 (East Anchorage), HD13 (South Midtown), and HD10 (Dimond/Oceanview)**. Across identifiable Anchorage-area records, at least **8,216 of 17,918 Hafner-first ballots (45.85%)** are represented. This conservative grouping includes HD10–24 and non-Whittier geographic precincts in HD9; pooled HD9 early/absentee records cannot be assigned precisely between Anchorage and Whittier.\n\n**Most votes and highest share are different:** HD21 has **653 Hafner-first ballots out of 6,686 House records (9.77%)**; HD18 has the highest geographic-district share, **304/2,035 (14.94%)**, followed by HD22 at **558/3,922 (14.23%)**.'))
    show.image(OUT/'hafner_district_strongholds.png',width=1250)
    rows=result['geographic_precincts_by_share_min100'][:8]
    show.table([{'Geographic precinct':r['precinct'],'Hafner first':r['hafner_first'],
                'All House records':r['house_records'],'Hafner share':f'{r["pct_Hafner_of_house_records"]:.2f}%'} for r in rows],
               'Highest geographic-precinct shares with at least 100 source records (Election Day only)')
    display(Markdown('The largest single geographic-precinct vote count is **East Anchorage No.3: 129/1,032 (12.50%)**. **Skagway leads the share ranking among precincts with at least 100 records: 68/368 (18.48%)**. Smaller places can have higher percentages: **Chefornak is 8/30 (26.67%)**. The threshold avoids presenting a handful of ballots as a large electoral base; all precincts remain in the exports.\n\nThese geographic-precinct rows are **Election Day only** in Rachel’s file. District-wide early, absentee and questioned batches are included in the district chart but cannot be assigned to individual towns. **HD99 has 74/130 Hafner-first records (56.92%)**, but it is an overseas administrative category, not a city. These results describe a November11 snapshot, rather than final citywide totals.'))


def show_geography_details(result):
    from analysis.reporting import presentation as show
    def table_rows(rows, first_key, title):
        show.table([{'Location / category':str(r[first_key]),'Hafner first':f'{r["hafner_first"]:,}',
                     'All House records':f'{r["house_records"]:,}',
                     'Hafner share':f'{r["pct_Hafner_of_house_records"]:.2f}%',
                     'Share of all Hafner-first ballots':f'{r["pct_of_all_Hafner_first"]:.2f}%'} for r in rows],title)
    ds=[{**r,'district_label':f'HD {r["house_district"]} — {r["area_label"]}'} for r in result['districts']]
    table_rows(ds,'district_label','All districts and the separately labeled overseas category; all voting modes')
    table_rows(result['geographic_precincts_by_count'][:10],'precinct','Ten geographic precincts with the most Hafner-first votes (Election Day only)')
    table_rows(result['top_geographic_precincts_by_share_no_threshold'],'precinct','Highest geographic-precinct shares without a size filter: small denominators retained')
    table_rows(result['counting_groups'],'counting_group','Voting-method breakdown; these are not cities')
    display(Markdown('All **244,705 House records** and **17,918 Hafner-first ballots** are accounted for. Flexible district parsing retains double-spaced questioned-ballot labels. Precinct counts match the previously independently audited Hafner source aggregation. All geographic precincts, including zero-Hafner cases, and administrative batches are retained in `analysis/house/hafner/geography/`. **HD99 is not ranked as a geographic stronghold.** The 2022 district-designation sheet is a descriptive reference, while exact current boundaries require the linked district maps.'))


if __name__=='__main__':
    data=main();print(json.dumps({'status':data['status'],'Hafner_first':data['Hafner_literal_first']},indent=2))
