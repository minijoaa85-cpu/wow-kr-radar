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
AGENT='WoWKR-Radar/0.4.1 (weekly attributed summary; source mythicstats.com/dps)'
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
 'evoker':['devastation','augmentation']
}
KNOWN={f'{spec} {cls}':(cls,spec) for cls,specs in SPEC_CLASSES.items() for spec in specs}
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

def read_page(html,requested=None,now=None):
    soup=BeautifulSoup(html,'html.parser')
    for el in soup(['script','style','noscript']):el.decompose()
    text=' '.join(soup.stripped_strings)
    m=HEAD.search(text)
    if not m:raise ValueError('No Mythicstats source period on page')
    period=int(m.group(1))
    if requested is not None and period!=requested:raise ValueError(f'Expected period {requested}, got {period}')
    a=re.search(r'\bDamage specs\b',text,re.I)
    b=re.search(r'\bTank specs\b',text,re.I)
    if not a or not b or b.start()<=a.end():raise ValueError('DPS section not found')
    section=text[a.end():b.start()]
    # Source site renders ranking as rank, change, tier, Avg, Top, Runs, spec.
    # Parse only known damage specs to avoid mixing tank/healer values.
    names='|'.join(sorted(map(re.escape,KNOWN),key=len,reverse=True))
    rx=re.compile(r'(?<!\S)(\d{1,2})\s+(0|[↑↓]\s?\d+|[+-]\d+)\s+([SABCDF])\s+(\d+(?:[.,]\d+)?[KMB]?)\s+(\d+(?:[.,]\d+)?[KMB]?)\s+(\d+(?:[.,]\d+)?[KMB]?)\s+('+names+r')\b',re.I)
    items=[];seen=set()
    for match in rx.finditer(section):
        rank,change,tier,avg,top,runs,name=match.groups()
        key=name.casefold()
        if key in seen:continue
        seen.add(key)
        cls,spec=KNOWN[key]
        items.append({'spec':spec,'class':cls,'name':key,'rank':int(rank),'tier':tier,
                      'avg_dps':number(avg),'top_dps':number(top),'runs':number(runs)})
    if len(items)<15:raise ValueError(f'Only {len(items)} DPS specs parsed; refusing partial source data')
    items.sort(key=lambda x:x['rank'])
    return {'period':period,'captured_at':(now or datetime.now(KST)).isoformat(),
            'source':'Mythicstats','source_url':f'{SOURCE}?period={period}',
            'scope':'Mythic+ dungeon-wide DPS; source displayed keystone bracket',
            'keys':'16-24','items':items,'status':'ok'}

def collect(session=requests,backfill_limit=7):
    now=datetime.now(KST)
    try:
        response=session.get(SOURCE,headers={'User-Agent':AGENT,'Accept':'text/html'},timeout=24)
        response.raise_for_status()
        current=read_page(response.text,now=now)
    except (requests.RequestException,ValueError) as exc:
        print('Mythicstats unavailable:',str(exc)[:200])
        return False

    try:history=json.loads(INDEX.read_text(encoding='utf-8')).get('periods',[])
    except (OSError,ValueError):history=[]
    existing={int(x['period']):x for x in history if isinstance(x,dict) and str(x.get('period','')).isdigit()}
    snapshots=[current]
    # One-time bootstrap, up to seven earlier source periods, strictly validated.
    if len(existing)<2 and backfill_limit:
        for period in range(current['period']-1,max(0,current['period']-backfill_limit-1),-1):
            if period in existing:continue
            time.sleep(1.5)
            try:
                response=session.get(SOURCE,params={'period':period},headers={'User-Agent':AGENT},timeout=24)
                response.raise_for_status()
                snapshots.append(read_page(response.text,requested=period,now=now))
            except (requests.RequestException,ValueError) as exc:
                print('Skipping unavailable source period',period,str(exc)[:150])
    for d in snapshots:
        period=d['period']
        file=f'period-{period}.json'
        (DATA/file).write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
        existing[period]={'period':period,'captured_at':d['captured_at'],'file':file,'spec_count':len(d['items'])}
    periods=sorted(existing.values(),key=lambda x:x['period'],reverse=True)[:100]
    INDEX.write_text(json.dumps({'status':'ok','source':'Mythicstats','source_url':SOURCE,'last_collected':now.isoformat(),
        'metric':'Overall dungeon DPS from Warcraft Logs, including out-of-combat time','keys':'16-24','periods':periods},
        ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print('Mythicstats saved',len(snapshots),'verified period(s),',len(current['items']),'DPS specs')
    return True

if __name__=='__main__':
    collect()
