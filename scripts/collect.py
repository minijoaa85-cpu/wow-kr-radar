#!/usr/bin/env python3
"""Collect linked WoW retail news; create dated immutable weekly snapshots."""
import datetime as dt
import hashlib
import json
import os
from pathlib import Path
import re
import time
from urllib.parse import quote
from xml.etree import ElementTree
import requests

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / 'data'
HIST = DATA / 'history'
KST = dt.timezone(dt.timedelta(hours=9))
NOW = dt.datetime.now(KST)
WEEK = NOW.strftime('%G-W%V')
USER_AGENT = 'WoWKR-Radar/0.1 (public news feed metadata aggregator; respect original sources)'
# First-party feeds, editorial search feeds, and opt-in public Reddit RSS.
FEEDS = [
 ('Blizzard', 'global', 'https://news.google.com/rss/search?q='+quote('site:worldofwarcraft.blizzard.com/en-us/news/ "World of Warcraft" when:14d')+'&hl=en-US&gl=US&ceid=US:en'),
 ('Wowhead', 'global', 'https://news.google.com/rss/search?q='+quote('site:wowhead.com/news/ "Midnight" OR "Retail" when:14d')+'&hl=en-US&gl=US&ceid=US:en'),
 ('Inven', 'KR', 'https://news.google.com/rss/search?q='+quote('site:inven.co.kr "월드 오브 워크래프트" OR "와우" when:14d')+'&hl=ko&gl=KR&ceid=KR:ko'),
 ('MMO-Champion', 'global', 'https://news.google.com/rss/search?q='+quote('site:mmo-champion.com "World of Warcraft" when:14d')+'&hl=en-US&gl=US&ceid=US:en'),
 ('Reddit', 'global', 'https://www.reddit.com/r/CompetitiveWoW/new/.rss'),
 ('Reddit', 'global', 'https://www.reddit.com/r/wow/new/.rss'),
]
KEYWORDS = ('wow','warcraft','midnight','eclipse','raid','mythic','dungeon','hotfix','ptr','class','season','와우','한밤','쐐기','공격대','블리자드','직업','특성','레이드','패치','신화','던전')
BLOCK = ('wow classic','classic wow','classic era','classic servers','classic realms','classic season','classic anniversary','cataclysm classic','mists of pandaria classic','burning crusade classic','wrath classic','hardcore realm','hardcore servers','season of discovery','wow forever','와우 포에버','와우포에버','포에버 서버','포에버 pvp','포에버 fix','포에버_fix','포에저','클래식 서버','클래식 시즌','클래식 하드코어','클래식 전문','디스커버리의 시즌','불타는 성전 클래식','판다리아의 안개 클래식')
EXCLUDE = ('invenraidframes3_forever','곰세툴팁','server board','서버 게시판','정보 게시판','latest news comments','news and guides - wowhead')
SIGNALS = ('midnight','eclipse','worldsoul','12.1','12.2','retail','live servers','the war within','war within','mythic+','m+','mythic dungeon','raid','dungeon','hotfix','class changes','class tuning','talent','patch','ptr','season 3','한밤','격냥','쐐기','공격대','레이드','본섭','소매','패치','핫픽스','밸런스','특성','직업','신화','던전','시즌 3','시간의 길')
NAVIGATION = ('홈페이지','게시판','포럼','뉴스와 가이드','news and guides','latest news comments','server forum')
MAX_AGE_DAYS = 15

def is_retail_news(title, src):
 t=title.casefold()
 if any(k in t for k in BLOCK+EXCLUDE+NAVIGATION): return False
 if src=='Inven' and ('[잡담]' in t or '[질문]' in t or '[포에버]' in t): return False
 if any(k in t for k in SIGNALS): return True
 # General discussion is allowed only when it is clearly about the retail game.
 return src in ('Blizzard','Reddit') and any(k in t for k in ('wow','warcraft','와우'))

def normalize_title(title):
 return re.sub(r'\\s+-\\s+(?:Wowhead|인벤|와우 인벤|MMO-Champion|World of Warcraft)$','',title,flags=re.I).strip()

def clean(s):
 return re.sub(r'\s+', ' ', re.sub('<[^>]+>', ' ', s or '')).strip()

def cat(title):
 t=title.lower()
 if any(x in t for x in ('hotfix','hotfixes','블루포스트','blue post','패치 노트','patch notes','개발자 공지')):return '공식·핫픽스'
 if any(x in t for x in ('season 3','시즌 3','roadmap','로드맵','release date','launch date','12.2','12.1.7','출시일')):return '로드맵'
 if any(x in t for x in ('class','spec','hunter','mage','druid','priest','talent','nerf','buff','balance','직업','특성','버프','너프','밸런스')):return '직업·밸런스'
 if any(x in t for x in ('dungeon','raid','mythic','m+','warcraft logs','쐐기','레이드','공격대','던전')):return '쐐기·레이드'
 if any(x in t for x in ('ptr','eclipse','patch','시즌','확장팩')):return '로드맵'
 return '커뮤니티'

def get_text(el, name):
 ch=el.find(name)
 return clean(''.join(ch.itertext()) if ch is not None else '')

def parse_date(s):
 if not s:return NOW.isoformat()
 from email.utils import parsedate_to_datetime
 try:return parsedate_to_datetime(s).astimezone(dt.timezone.utc).isoformat()
 except (TypeError,ValueError):
  try:return dt.datetime.fromisoformat(s.replace('Z','+00:00')).astimezone(dt.timezone.utc).isoformat()
  except ValueError:return NOW.isoformat()

def feed_items(xml):
 root=ElementTree.fromstring(xml)
 entries=root.findall('.//item')
 if entries:
  for e in entries:
   yield {'title':get_text(e,'title'),'url':get_text(e,'link'),'published_at':parse_date(get_text(e,'pubDate')),'description':get_text(e,'description')}
 else:
  ns={'a':'http://www.w3.org/2005/Atom'}
  for e in root.findall('.//a:entry',ns):
   link=e.find('a:link',ns)
   yield {'title':get_text(e,'{http://www.w3.org/2005/Atom}title'),'url':link.get('href','') if link is not None else '', 'published_at':parse_date(get_text(e,'{http://www.w3.org/2005/Atom}updated')),'description':get_text(e,'{http://www.w3.org/2005/Atom}summary')}

def translate(items):
 """Optional compact Korean summaries. No API key -> titles preserved and status explicit."""
 key=os.getenv('OPENAI_API_KEY','').strip()
 if not key:return False
 model=os.getenv('OPENAI_MODEL','gpt-4.1-mini')
 for idx in range(0,len(items),8):
  batch=items[idx:idx+8]
  try:
   payload={'model':model,'temperature':0,'response_format':{'type':'json_object'},'messages':[
    {'role':'system','content':'You translate World of Warcraft RETAIL news headlines into natural Korean and create precise one-sentence Korean summaries. Do not hallucinate facts, dates, balance changes, or details not explicitly in title and snippet. Keep game terminology standard in Korean. Return JSON {"results":[{"title_ko":"...","summary_ko":"..."},...]}, preserving input order and exact count.'},
    {'role':'user','content':json.dumps([{'title':x['title_original'],'snippet':x['original_snippet'][:300]} for x in batch],ensure_ascii=False)}]}
   resp=requests.post('https://api.openai.com/v1/chat/completions',headers={'Authorization':'Bearer '+key},json=payload,timeout=70)
   resp.raise_for_status()
   out=json.loads(resp.json()['choices'][0]['message']['content'])['results']
   if len(out)!=len(batch):raise ValueError('Translation response count mismatch')
   for item,tr in zip(batch,out):
    item['title_ko']=clean(tr.get('title_ko')) or item['title_original']
    item['summary_ko']=clean(tr.get('summary_ko')) or '원문에서 자세한 내용을 확인하세요.'
    item['translated']=True
  except (requests.RequestException,KeyError,ValueError,json.JSONDecodeError) as ex:
   print('Translation unavailable for batch:',str(ex)[:200]);continue
 return any(x.get('translated') for x in items)

def main():
 DATA.mkdir(exist_ok=True);HIST.mkdir(exist_ok=True)
 items=[];errors=[];success=0
 seen=set()
 for src,region,url in FEEDS:
  try:
   r=requests.get(url,headers={'User-Agent':USER_AGENT,'Accept':'application/rss+xml,application/atom+xml,application/xml'},timeout=25)
   r.raise_for_status(); count=0
   for entry in feed_items(r.content):
    title=entry['title'];low=title.lower()
    if not title or not entry['url']:continue
    if not is_retail_news(title, src):continue
    try:
     posted=dt.datetime.fromisoformat(entry['published_at'])
     if NOW.astimezone(dt.timezone.utc)-posted>dt.timedelta(days=MAX_AGE_DAYS):continue
    except ValueError:continue
    # Google News titles carry a source suffix. The link remains the source-discovery link.
    normalized=normalize_title(title)
    key=re.sub(r'[^a-z0-9가-힣]','',normalized.lower())[:110]
    if key in seen:continue
    seen.add(key)
    id_=hashlib.sha256((src+entry['url']).encode()).hexdigest()[:16]
    item={'id':id_,'title_ko':normalized if region=='KR' else title,'title_original':title,'summary_ko':'원문 링크에서 자세한 내용을 확인하세요.' if region=='KR' else '해외 기사 · 한국어 요약 미생성 (OPENAI_API_KEY 설정 필요)', 'original_snippet':entry['description'][:500],'source':src,'region':region,'category':('국내 소식' if region=='KR' else cat(title)),'published_at':entry['published_at'],'url':entry['url'],'verified':False,'translated':region=='KR','sample':False}
    items.append(item);count+=1
    if count>=30:break
   success+=1
   print(src,'read:',count)
  except (requests.RequestException,ElementTree.ParseError,ValueError) as exc:
   errors.append({'source':src,'error':str(exc)[:180]});print('Feed failure:',src,exc)
  time.sleep(0.35)
 # Do not destroy saved latest with a temporary all-feed outage.
 if success==0:
  print('All feeds failed. Existing snapshots unchanged.');return 1
 items.sort(key=lambda x:x['published_at'],reverse=True)
 items=items[:120]
 translated=translate([x for x in items if x['region']!='KR'])
 for x in items:x.pop('original_snippet',None)
 latest={'generated_at':NOW.isoformat(),'status':'live' if items else 'empty','week':WEEK,'items':items,'collection':{'attempted':len(FEEDS),'success':success,'errors':errors,'translated':translated}}
 (DATA/'latest.json').write_text(json.dumps(latest,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
 # Merge instead of overwrite: manual reruns may add headlines during the same week.
 p=HIST/(WEEK+'.json')
 if p.exists():
  old=json.loads(p.read_text(encoding='utf-8'))
  prior={x['id']:x for x in old.get('items',[])}
  for x in items:prior[x['id']]=x
  old['items']=sorted((v for v in prior.values() if is_retail_news(v.get('title_original',''), v.get('source',''))),key=lambda x:x['published_at'],reverse=True)
  old['updated_at']=NOW.isoformat();hist=old
 else:hist={**latest,'created_at':NOW.isoformat(),'updated_at':NOW.isoformat()}
 p.write_text(json.dumps(hist,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
 ix=HIST/'index.json'
 try:weeks=json.loads(ix.read_text(encoding='utf-8')).get('weeks',[])
 except (ValueError,FileNotFoundError):weeks=[]
 weeks=[x for x in weeks if x.get('week')!=WEEK]
 weeks.append({'week':WEEK,'date':NOW.date().isoformat(),'count':len(hist['items']),'added':len([x for x in items if x['id'] not in {y['id'] for y in (old.get('items',[]) if 'old' in locals() else [])}])})
 weeks.sort(key=lambda x:x['week'],reverse=True)
 ix.write_text(json.dumps({'weeks':weeks},ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
 print('Saved',len(items),'articles and',len(weeks),'weekly archives');return 0

if __name__=='__main__':raise SystemExit(main())
