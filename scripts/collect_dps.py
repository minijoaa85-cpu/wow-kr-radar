#!/usr/bin/env python3
"""Small attributed weekly metric snapshots from public Mythicstats /dps pages.
Stores only brief per-specialization numeric metrics, not page contents.
Never invents unavailable weeks. One initial bounded historical backfill, then weekly snapshots.
"""
from __future__ import annotations
from datetime import datetime, timedelta, timezone
from pathlib import Path
import json
import re
import time

import requests
from bs4 import BeautifulSoup

ROOT=Path(__file__).resolve().parents[1]
DATA=ROOT/'data'/'dps'
DATA.mkdir(parents=True,exist_ok=True)
INDEX=DATA/'index.json'
SOURCE='https://mythicstats.com/dps'
AGENT='WoWKR-Radar/0.4.3 (weekly attributed summary; source mythicstats.com/dps)'
KST=timezone(timedelta(hours=9))
SPEC_CLASSES={
 'rogue':['assassination','subtlety','outlaw'],
 'shaman':['elemental','enhancement'],
 'warrior':['arms','fury'],
 'demon-hunter':['devourer','havoc'],
 'warlock':['demonology','affliction','destruction'],
 'monk':['windwalker'],
 'death-knight':['frost','unholy'],
 'mage':['fire','arcane','frost'],
 'hunter':['marksmanship','beast-mastery','survival'],
 'paladin':['retribution'],
 'druid':['feral','balance'],
 'priest':['shadow'],
 'evoker':['devastation','augmentation','preservation'],
 'paladin':['retribution','protection','holy'],
 'druid':['feral','balance','guardian','restoration'],
 'priest':['shadow','discipline','holy'],
 'shaman':['elemental','enhancement','restoration'],
 'warrior':['arms','fury','protection'],
 'demon-hunter':['devourer','havoc','vengeance'],
 'death-knight':['frost','unholy','blood'],
 'monk':['windwalker','brewmaster','mistweaver']
}
KNOWN={f'{spec} {cls}':(cls,spec) for cls,specs in SPEC_CLASSES.items() for spec in specs}
ROLE_SPECS={
 'tank':{'blood death-knight','vengeance demon-hunter','guardian druid','protection warrior','protection paladin','brewmaster monk'},
 'healer':{'preservation evoker','mistweaver monk','holy paladin','restoration shaman','discipline priest','holy priest','restoration druid'}
}
ROLE_MIN={'damage':20,'tank':6,'healer':7}
PERIOD_URL='https://mythicstats.com/period'

METRIC=re.compile(r'^\d+(?:[.,]\d+)?[KMB]?$',re.I)
TIER=re.compile(r'^[SABCDF]$')
RANK=re.compile(r'^\d{1,2}$')
DIFF=re.compile(r'^(?:0|[↑↓]\d+|[+-]\d+)$')
HEAD=re.compile(r'Period\s+(\d{2,6})\b',re.I)

def number(token):
    token=token.replace(',','').strip().upper()
    if not METRIC.fullmatch(token):raise ValueError('Bad metric '+token)
    multiplier={'K':1000,'M':1_000_000,'B':1_000_000_000}
    return int(round(float(token[:-1])*multiplier[token[-1]])) if token[-1] in multiplier else int(float(token))

def discover_periods(html):
    """Use official source period/season index, no guessed expansion cutoff."""
    soup=BeautifulSoup(html,'html.parser')
    for el in soup(['script','style','noscript']):el.decompose()
    text=' '.join(soup.stripped_strings)
    rows=re.findall(r'(?<!\d)(\d{4})\s+(mid[1-9][0-9]*)\b',text,re.I)
    return sorted({int(p):season.lower() for p,season in rows}.items())

def read_page(html,requested=None,now=None,season=None):
    soup=BeautifulSoup(html,'html.parser')
    for el in soup(['script','style','noscript']):el.decompose()
    text=' '.join(soup.stripped_strings)
    m=HEAD.search(text)
    if not m:raise ValueError('No Mythicstats source period on page')
    period=int(m.group(1))
    if requested is not None and period!=requested:raise ValueError(f'Expected period {requested}, got {period}')
    rx_names='|'.join(sorted(map(re.escape,KNOWN),key=len,reverse=True))
    row_rx=re.compile(r'(?<!\S)(\d{1,2})\s+(0|[↑↓]\s?\d+|[+-]\d+)\s+([SABCDF])\s+(\d+(?:[.,]\d+)?[KMB]?)\s+(\d+(?:[.,]\d+)?[KMB]?)\s+(\d+(?:[.,]\d+)?[KMB]?)\s+('+rx_names+r')\b',re.I)
    positions=[(role, re.search(r'\b'+head+r' specs\b',text,re.I)) for role,head in [('damage','Damage'),('tank','Tank'),('healer','Healer')]]
    if any(x[1] is None for x in positions):raise ValueError('One or more role sections missing')
    bracket=re.search(r'Mythic\+\s+(\d+)-(\d+)\s+keys',text,re.I)
    keystone_range=(bracket.group(1)+'-'+bracket.group(2)) if bracket else 'not stated'
    items=[]
    for idx,(role,head) in enumerate(positions):
        ending=positions[idx+1][1].start() if idx+1<len(positions) else (text.find('About this summary',head.end()) if 'About this summary' in text[head.end():] else len(text))
        segment=text[head.end():ending]
        current=[];seen=set()
        for match in row_rx.finditer(segment):
            rank,change,tier,avg,top,runs,name=match.groups()
            key=name.casefold()
            if key in seen:continue
            declared_role='tank' if key in ROLE_SPECS['tank'] else 'healer' if key in ROLE_SPECS['healer'] else 'damage'
            if declared_role!=role:continue
            seen.add(key)
            cls,spec=KNOWN[key]
            current.append({'spec':spec,'class':cls,'name':key,'role':role,'rank':int(rank),'tier':tier,
             'avg_dps':number(avg),'top_dps':number(top),'runs':number(runs)})
        if len(current)<ROLE_MIN[role]:
            raise ValueError(f'{role}: {len(current)} specs only; refusing incomplete source data')
        items.extend(sorted(current,key=lambda item:item['rank']))
    return {'period':period,'season':season,'captured_at':(now or datetime.now(KST)).isoformat(),
      'source':'Mythicstats','source_url':f'{SOURCE}?period={period}',
      'scope':'Mythic+ dungeon-wide DPS; all 3 roles from source','keys':keystone_range,'items':items,'status':'ok'}

def collect(session=requests, backfill_limit=None):
    now=datetime.now(KST)
    try:
        p_response=session.get(PERIOD_URL,headers={'User-Agent':AGENT},timeout=24)
        p_response.raise_for_status()
        periods=discover_periods(p_response.text)
        if not periods:raise ValueError('No verified Midnight periods in source index')
    except (requests.RequestException,ValueError) as exc:
        print('Mythicstats period index unavailable:',str(exc)[:200])
        return False
    # The period index paginates older weeks. The official MID1 season chart
    # enumerates verified weeks 1056-1075, including those omitted by page 1.
    try:
        season_page=session.get('https://mythicstats.com/season/mid1',headers={'User-Agent':AGENT},timeout=24)
        season_page.raise_for_status()
        season_soup=BeautifulSoup(season_page.text,'html.parser')
        for el in season_soup(['script','style','noscript']):el.decompose()
        season_text=' '.join(season_soup.stripped_strings)
        old_week_ids={int(n) for n in re.findall(r'(?<!\d)(10\d{2})\s+Blood\b',season_text,re.I)}
        periods=sorted({**dict(periods),**{p:'mid1' for p in old_week_ids if 1000<=p<min(dict(periods))}}.items())
    except (requests.RequestException,ValueError):
        pass
    try:history=json.loads(INDEX.read_text(encoding='utf-8')).get('periods',[])
    except (OSError,ValueError):history=[]
    existing={int(x['period']):x for x in history if isinstance(x,dict) and str(x.get('period','')).isdigit()}
    season_lookup=dict(periods)
    stored=[];failures=[]
    for period,season in periods:
        oldfile=DATA/f'period-{period}.json'
        # Upgrade old damage-only snapshots to all roles. Preserve other existing valid full snapshots.
        if oldfile.exists():
            try:
                previous=json.loads(oldfile.read_text(encoding='utf-8'))
                roles={x.get('role') for x in previous.get('items',[])}
                if roles=={'damage','tank','healer'} and previous.get('season')==season and period < max(dict(periods))-1:
                    existing[period]={'period':period,'season':season,'file':oldfile.name,'spec_count':len(previous['items']),'captured_at':previous.get('captured_at')}
                    continue
            except (ValueError,OSError):pass
        if backfill_limit is not None and len(stored)>=backfill_limit:break
        try:
            # First try the canonical filter. Some older seasons require an explicit season or dungeon query.
            options=[{'period':period,'dungeon':''}]
            if season=='mid1':
                options.extend([{'period':period,'season':season,'dungeon':''},{'period':period,'season':season}])
            else:
                options.append({'period':period})
            record=None
            last_error=''
            for params in options:
                try:
                    response=session.get(SOURCE,params=params,headers={'User-Agent':AGENT,'Accept':'text/html'},timeout=24)
                    response.raise_for_status()
                    record=read_page(response.text,requested=period,now=now,season=season)
                    break
                except (requests.RequestException,ValueError) as inner:
                    last_error=str(inner)[:150]
                    time.sleep(0.25)
            if record is None:raise ValueError(last_error or 'No matching source period')
            oldfile.write_text(json.dumps(record,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
            existing[period]={'period':period,'season':season,'file':oldfile.name,'spec_count':len(record['items']),'captured_at':record['captured_at']}
            stored.append(period)
        except (requests.RequestException,ValueError) as exc:
            failures.append(period)
            print('Skipping unverified source period',period,str(exc)[:150])
        time.sleep(0.35)
    # Only include periods belonging to verified Midnight season index and actually present on disk.
    archived=[v for p,v in existing.items() if p in season_lookup and (DATA/v['file']).exists() and v.get('spec_count',0)>=33]
    archived.sort(key=lambda x:x['period'],reverse=True)
    index={'status':'ok' if archived else 'unavailable','source':'Mythicstats','source_url':SOURCE,
      'period_source':PERIOD_URL,'last_collected':now.isoformat(),'metric':'Overall dungeon DPS from Warcraft Logs, including noncombat time',
      'keys':'source period-specific','seasons':sorted(set(season_lookup.values()),key=lambda z:int(z[3:])),'expected_periods':len(periods),'missing_periods':[p for p,_ in periods if p not in {x['period'] for x in archived}],
      'season_periods':[{'period':p,'season':sn} for p,sn in periods], 'periods':archived}
    INDEX.write_text(json.dumps(index,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print('Mythicstats seasons',sorted(set(season_lookup.values())),'verified:',len(archived),'of',len(periods),'periods;',len(stored),'new;',len(failures),'unverified')
    return len(archived)>0

if __name__=='__main__':
    collect()
