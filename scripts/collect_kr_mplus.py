#!/usr/bin/env python3
"""Fetch KR Mythic+ affix data from Raider.IO public API without inventing values."""
import datetime as dt
import json
from pathlib import Path
import requests

ROOT=Path(__file__).resolve().parents[1]
DEST=ROOT/'data'/'kr_mplus.json'
URL='https://raider.io/api/v1/mythic-plus/affixes'
NOW=dt.datetime.now(dt.timezone(dt.timedelta(hours=9))).isoformat()

def collect(session=requests):
    try:
        response=session.get(URL,params={'region':'kr','locale':'ko'},headers={'Accept':'application/json','User-Agent':'WoWKR-Radar/0.3 (public attribution raider.io)'},timeout=20)
        response.raise_for_status()
        raw=response.json()
        if not isinstance(raw,dict) or not isinstance(raw.get('affix_details'),list):
            raise ValueError('Raider.IO returned unexpected affix response structure')
        details=[{'name':str(x.get('name') or ''),'description':str(x.get('description') or ''),'icon':str(x.get('icon') or '')} for x in raw['affix_details'] if isinstance(x,dict) and x.get('name')]
        if not details:
            raise ValueError('No valid affixes found')
        data={'status':'live','region':'kr','retrieved_at':NOW,'title':str(raw.get('title') or ''),'affixes':details,'source':'Raider.IO','source_url':'https://raider.io/mythic-plus/affixes'}
    except (requests.RequestException,ValueError,KeyError,TypeError) as error:
        # Explicitly mark an unavailable feed rather than retaining stale data as "live".
        data={'status':'unavailable','region':'kr','retrieved_at':NOW,'affixes':[],'source':'Raider.IO','source_url':'https://raider.io/mythic-plus/affixes','error':str(error)[:180]}
    DEST.parent.mkdir(parents=True,exist_ok=True)
    DEST.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print('KR affixes:',data['status'],len(data['affixes']))
    return data

if __name__=='__main__':
    collect()
