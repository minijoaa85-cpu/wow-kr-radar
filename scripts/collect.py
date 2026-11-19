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
USER_AGENT = 'WoWKR-Radar/0.4 (public news feed metadata aggregator; respect original sources)'
# First-party feeds, editorial search feeds, and opt-in public Reddit RSS.
FEEDS = [
 ('Blizzard', 'global', 'https://news.google.com/rss/search?q='+quote('site:worldofwarcraft.blizzard.com/en-us/news/ "World of Warcraft" when:14d')+'&hl=en-US&gl=US&ceid=US:en'),
 ('Wowhead', 'global', 'https://news.google.com/rss/search?q='+quote('site:wowhead.com/news/ "Midnight" OR "Retail" when:14d')+'&hl=en-US&gl=US&ceid=US:en'),
 ('Inven', 'KR', 'https://news.google.com/rss/search?q='+quote('site:inven.co.kr "월드 오브 워크래프트" OR "와우" when:14d')+'&hl=ko&gl=KR&ceid=KR:ko'),
 ('MMO-Champion', 'global', 'https://news.google.com/rss/search?q='+quote('site:mmo-champion.com "World of Warcraft" when:14d')+'&hl=en-US&gl=US&ceid=US:en'),
 ('Reddit Competitive (indexed)', 'global', 'https://news.google.com/rss/search?q='+quote('site:reddit.com/r/CompetitiveWoW/ (mythic OR raid OR tuning OR season) when:14d')+'&hl=en-US&gl=US&ceid=US:en'),
 ('Reddit WoW (indexed)', 'global', 'https://news.google.com/rss/search?q='+quote('site:reddit.com/r/wow/ (Midnight OR patch OR raid OR dungeon) when:14d')+'&hl=en-US&gl=US&ceid=US:en'),
]
KEYWORDS = ('wow','warcraft','midnight','eclipse','raid','mythic','dungeon','hotfix','ptr','class','season','와우','한밤','쐐기','공격대','블리자드','직업','특성','레이드','패치','신화','던전')
BLOCK = ('forever','포에버','포에저','wow classic','classic wow','classic era','classic servers','classic realms','classic season','classic anniversary','cataclysm classic','mists of pandaria classic','burning crusade classic','wrath classic','hardcore realm','hardcore servers','season of discovery','wow forever','와우 포에버','와우포에버','포에버 서버','포에버 pvp','포에버 fix','포에버_fix','포에저','클래식 서버','클래식 시즌','클래식 하드코어','클래식 전문','디스커버리의 시즌','불타는 성전 클래식','판다리아의 안개 클래식')
EXCLUDE = ('invenraidframes3_forever','곰세툴팁','server board','서버 게시판','정보 게시판','latest news comments','news and guides - wowhead')
SIGNALS = ('midnight','eclipse','worldsoul','12.1','12.2','retail','live servers','the war within','war within','mythic+','m+','mythic dungeon','raid','dungeon','hotfix','class changes','class tuning','talent','patch','ptr','season 3','한밤','격냥','쐐기','공격대','레이드','본섭','소매','패치','핫픽스','밸런스','특성','직업','신화','던전','시즌 3','시간의 길')
NAVIGATION = ('홈페이지','게시판','포럼','뉴스와 가이드','news and guides','latest news comments','server forum')
MAX_AGE_DAYS = 15

def is_retail_news(title, src):
 t=title.casefold()
 if any(k in t for k in BLOCK+EXCLUDE+NAVIGATION): return False
 if src=='Inven' and ('[잡담]' in t or '[질문]' in t or '[포에버]' in t): return False
 if src=='Inven' and not any(k in t for k in ('한밤','본섭','쐐기','공격대','레이드','패치','핫픽스','밸런스','12.1','12.2','시즌 3','midnight','eclipse')): return False
 if any(k in t for k in SIGNALS): return True
 # General discussion is allowed only when it is clearly about the retail game.
 return src in ('Blizzard','Reddit') and any(k in t for k in ('wow','warcraft','와우'))

def normalize_title(title):
 return re.sub(r'\s+-\s+(?:Wowhead|인벤|와우 인벤|MMO-Champion|World of Warcraft)$', '', title, flags=re.I).strip()

def clean(s):
 return re.sub(r'\s+', ' ', re.sub('<[^>]+>', ' ', s or '')).strip()

def cat(title):
 t=title.lower()
 if any(x in t for x in ('hotfix','hotfixes','블루포스트','blue post','패치 노트','patch notes','개발자 공지')):return '공식·핫픽스'
 if any(x in t for x in ('roadmap','로드맵','release date','launch date','12.2','12.1.7','출시일','시즌 시작일')):return '로드맵'
 if any(x in t for x in ('class tuning','class changes','class balance','spec tuning','talent','nerf','buff','balance','직업 변경','직업 조정','특성 변경','버프','너프','밸런스')):return '직업·밸런스'
 if any(x in t for x in ('dungeon','raid','mythic','m+','warcraft logs','쐐기','레이드','공격대','던전','season 3','시즌 3')):return '쐐기·레이드'
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

def restore_translation_cache(items):
    try:
        previous=json.loads((DATA/'latest.json').read_text(encoding='utf-8')).get('items',[])
    except (OSError,ValueError):
        previous=[]
    cache={(x.get('source'),x.get('title_original')):x for x in previous if x.get('translated') and x.get('region')!='KR'}
    reused=0
    for x in items:
        cached=cache.get((x.get('source'),x.get('title_original')))
        if cached:
            x['title_ko']=cached.get('title_ko') or x['title_ko']
            x['summary_ko']=cached.get('summary_ko') or x['summary_ko']
            x['translated']=True
            reused+=1
    return reused

def translate(items):
    """Translate headline+feed snippet only. Never claim article-body summarization."""
    key=os.getenv('OPENAI_API_KEY','').strip()
    pending=[x for x in items if x['region']!='KR' and not x.get('translated')]
    if not key or not pending:return 0
    model=os.getenv('OPENAI_MODEL','gpt-4.1-mini')
    done=0
    for idx in range(0,min(len(pending),40),8):
        batch=pending[idx:idx+8]
        try:
            prompt=[
             {'role':'system','content':'You translate World of Warcraft retail news headlines and visible RSS snippets into Korean. Never add details not present in the supplied fields. Summaries must say it is a headline-based brief. Translate the title even if the snippet is empty. Preserve uncertainty, PTR/datamining qualifications. Return JSON object with results list of title_ko and summary_ko, exactly one for each input, in order.'},
             {'role':'user','content':json.dumps([{'title':x['title_original'],'snippet':x.get('original_snippet','')[:260]} for x in batch],ensure_ascii=False)}
            ]
            resp=requests.post('https://api.openai.com/v1/chat/completions',headers={'Authorization':'Bearer '+key},json={'model':model,'response_format':{'type':'json_object'},'messages':prompt},timeout=65)
            resp.raise_for_status()
            translated=json.loads(resp.json()['choices'][0]['message']['content'])['results']
            if not isinstance(translated,list) or len(translated)!=len(batch):raise ValueError('Translation count mismatch')
            for x,entry in zip(batch,translated):
                title=clean(entry.get('title_ko',''))
                summary=clean(entry.get('summary_ko',''))
                if not title or not summary:continue
                x['title_ko']=title
                x['summary_ko']=summary
                x['translated']=True
                done+=1
        except (requests.RequestException,KeyError,ValueError,TypeError) as exc:
            print('Translation batch failed:',str(exc)[:180])
    return done

def main():
 DATA.mkdir(exist_ok=True);HIST.mkdir(exist_ok=True)
 items=[];errors=[];success=0;feed_results=[]
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
   feed_results.append({'source':src,'status':'ok','count':count})
   print(src,'read:',count)
  except (requests.RequestException,ElementTree.ParseError,ValueError) as exc:
   errors.append({'source':src,'error':str(exc)[:180]});feed_results.append({'source':src,'status':'error','count':0});print('Feed failure:',src,exc)
  time.sleep(0.35)
 # Do not destroy saved latest with a temporary all-feed outage.
 if success==0:
  print('All feeds failed. Existing snapshots unchanged.');return 1
 items.sort(key=lambda x:x['published_at'],reverse=True)
 items=items[:120]
 cached=restore_translation_cache(items)
 translated=translate(items)
 for x in items:x.pop('original_snippet',None)
 latest={'generated_at':NOW.isoformat(),'status':'live' if items else 'empty','week':WEEK,'items':items,'collection':{'attempted':len(FEEDS),'success':success,'errors':errors,'translated':cached+translated>0,'translated_count':sum(1 for x in items if x.get('translated') and x['region']!='KR'),'reused_translations':cached,'new_translations':translated,'feed_results':feed_results}}
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
 weeks.append({'week':WEEK,'date':NOW.date().isoformat(),'count':len(hist['items'])})
 weeks.sort(key=lambda x:x['week'],reverse=True)
 ix.write_text(json.dumps({'weeks':weeks},ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
 print('Saved',len(items),'articles and',len(weeks),'weekly archives');return 0

if __name__=='__main__':raise SystemExit(main())
