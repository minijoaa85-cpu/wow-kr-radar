#!/usr/bin/env python3
"""Fetch a limited snapshot of Korean Mythic+ runs, without inferring spec meta."""
import datetime as dt
import json
from pathlib import Path
from urllib.parse import urlparse
import requests

DEST=Path(__file__).resolve().parents[1]/'data'/'kr_runs.json'
API='https://raider.io/api/v1/mythic-plus/runs'
NOW=lambda: dt.datetime.now(dt.timezone(dt.timedelta(hours=9))).isoformat()

def safe_link(value):
    if not isinstance(value,str): return ''
    p=urlparse(value)
    return value if p.scheme=='https' and p.hostname in ('raider.io','www.raider.io') else ''

def parse_runs(raw):
    if not isinstance(raw,dict) or not isinstance(raw.get('runs'),list):
        raise ValueError('API did not provide a runs array')
    parsed=[]
    for run in raw['runs'][:20]:
        if not isinstance(run,dict): continue
        try:
            level=int(run.get('mythic_level') or run.get('level') or 0)
        except (TypeError,ValueError): continue
        if level<2 or level>60: continue
        dungeon=run.get('dungeon')
        if isinstance(dungeon,dict): dungeon=dungeon.get('name')
        if not isinstance(dungeon,str) or not dungeon.strip(): continue
        score=run.get('score')
        try: score=round(float(score),1) if score is not None else None
        except (TypeError,ValueError): score=None
        if score is not None and not (0<=score<=1000):score=None
        link=safe_link(run.get('url') or run.get('run_url') or '')
        # No rank number assigned; API's list order is not a universal KR player ranking.
        parsed.append({'dungeon':dungeon[:110],'level':level,'score':score,'url':link})
    return parsed

def collect(session=requests, destination=None):
    target=destination or DEST
    result={'status':'unavailable','region':'kr','retrieved_at':NOW(),'source':'Raider.IO','source_url':'https://raider.io/mythic-plus-rankings/season-mn-2/all/kr/leaderboards','runs':[]}
    try:
        resp=session.get(API,params={'region':'kr','page':0},timeout=20,headers={'Accept':'application/json','User-Agent':'WoWKR-Radar/0.4'})
        resp.raise_for_status()
        runs=parse_runs(resp.json())
        if not runs: raise ValueError('API returned no valid runs')
        result['status']='live'
        result['runs']=runs
        result['source_url']='https://raider.io/mythic-plus-rankings'
    except (requests.RequestException,TypeError,ValueError,KeyError) as error:
        result['error']=str(error)[:180]
    target.parent.mkdir(parents=True,exist_ok=True)
    target.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print('KR runs:',result['status'],len(result['runs']))
    return result

if __name__=='__main__':
    collect()
