import './style.css';
const cats=['전체','공식·핫픽스','직업·밸런스','쐐기·레이드','로드맵','국내 소식','커뮤니티','기타'];
const sources=['전체','Blizzard','Wowhead','Inven','Reddit Competitive (indexed)','Reddit WoW (indexed)','MMO-Champion'];
const state={cat:'전체',src:'전체',q:'',tab:'overview',week:'latest',items:[],history:[],releases:[],meta:null,priorIds:new Set(),showOriginal:false,myWatch:[],watchSpecs:[],mplus:null,krRuns:null,dpsLoaded:false,dpsIndex:null,dpsWeeks:[],dpsClass:'hunter',dpsSpec:'marksmanship hunter',dpsMetric:'avg_dps'};
const $=id=>document.getElementById(id);
const safe=s=>String(s??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const formatted=d=>{if(!d)return '날짜 미상';const t=new Date(d);return Number.isNaN(t.getTime())?'날짜 미상':new Intl.DateTimeFormat('ko-KR',{timeZone:'Asia/Seoul',month:'short',day:'numeric'}).format(t)};
const yearweek=d=>{let t=new Date(d);return new Intl.DateTimeFormat('ko-KR',{timeZone:'Asia/Seoul',dateStyle:'medium'}).format(t)};
const icon={overview:'◈',news:'▤',classes:'⚔',endgame:'⬡',roadmap:'▦',history:'◷',versions:'▤',watch:'✦',krmplus:'⬡',dps:'◩'};
const menus=[['overview','종합 현황'],['news','뉴스 피드'],['classes','직업 / 밸런스'],['endgame','쐐기 / 레이드'],['krmplus','한국 쐐기'],['dps','DPS 주간 추이'],['roadmap','시즌 로드맵']];
const optionMenus=[['watch','My Watch'],['history','주간 히스토리'],['versions','개발 히스토리']];
let signalTimer;
const watchClasses=[
 ['전사',['warrior','전사']],['성기사',['paladin','성기사']],['사냥꾼',['hunter','사냥꾼','격냥','야냥','생냥']],
 ['도적',['rogue','도적']],['사제',['priest','사제']],['죽음의 기사',['death knight','deathknight','죽음의 기사','죽기']],
 ['주술사',['shaman','주술사']],['마법사',['mage','마법사']],['흑마법사',['warlock','흑마법사']],
 ['수도사',['monk','수도사']],['드루이드',['druid','드루이드']],['악마사냥꾼',['demon hunter','악마사냥꾼','악사']],
 ['기원사',['evoker','기원사']]
];
const specOptions={
 '전사':[['무기','arms','무기'],['분노','fury','분노'],['방어','protection warrior','방어 전사']],
 '성기사':[['신성','holy paladin','신기'],['보호','protection paladin','보기'],['징벌','retribution','징기']],
 '사냥꾼':[['야수','beast mastery','야냥'],['사격','marksmanship','격냥'],['생존','survival hunter','생냥']],
 '도적':[['암살','assassination rogue','암살'],['무법','outlaw rogue','무법'],['잠행','subtlety rogue','잠행']],
 '사제':[['수양','discipline priest','수사'],['신성','holy priest','신사'],['암흑','shadow priest','암사']],
 '죽음의 기사':[['혈기','blood death knight','혈죽'],['냉기','frost death knight','냉죽'],['부정','unholy death knight','부죽']],
 '주술사':[['정기','elemental shaman','정술'],['고양','enhancement shaman','고술'],['복원','restoration shaman','복술']],
 '마법사':[['비전','arcane mage','비법'],['화염','fire mage','화법'],['냉기','frost mage','냉법']],
 '흑마법사':[['고통','affliction','고흑'],['악마','demonology','악흑'],['파괴','destruction warlock','파흑']],
 '수도사':[['양조','brewmaster','양조'],['운무','mistweaver','운무'],['풍운','windwalker','풍운']],
 '드루이드':[['조화','balance druid','조드'],['야성','feral druid','야드'],['수호','guardian druid','수드'],['회복','restoration druid','회드']],
 '악마사냥꾼':[['파멸','havoc','악딜'],['복수','vengeance demon hunter','악탱']],
 '기원사':[['황폐','devastation evoker','황폐'],['보존','preservation evoker','보존'],['증강','augmentation evoker','증강']]
};
try{state.myWatch=JSON.parse(localStorage.getItem('wowkr_mywatch_v1')||'[]').filter(x=>watchClasses.some(w=>w[0]===x));}catch(e){state.myWatch=[]}
try{state.watchSpecs=JSON.parse(localStorage.getItem('wowkr_watchspec_v1')||'[]').filter(x=>typeof x==='string'&&x.includes(':'));}catch(e){state.watchSpecs=[]}
const watched=x=>state.myWatch.some(name=>{
 const text=(x.title_original+' '+x.title_ko+' '+x.summary_ko).toLowerCase();
 const active=state.watchSpecs.filter(token=>token.startsWith(name+':'));
 if(active.length){
  return active.some(token=>{const spec=specOptions[name]?.find(z=>name+':'+z[0]===token);return spec&&[spec[1],spec[2],name+' '+spec[0]].some(term=>text.includes(term.toLowerCase()));});
 }
 return (watchClasses.find(w=>w[0]===name)?.[1]||[]).some(term=>text.includes(term));
});
function init(){document.querySelector('#app').innerHTML=`<div class="shell"><aside class="sidebar"><div class="brand"><div class="brand-icon">W</div><div><strong>WoW KR Radar</strong><small>AZEROTH INTELLIGENCE</small></div></div><div class="side-label">COMMAND CENTER</div><nav id="nav"></nav><div class="side-bottom"><span class="live-dot"></span> <span id="side-status">데이터 로딩 중</span><div class="side-note">한국 본섭 · 아시아/서울<br>뉴스 출처와 원문을 항상 표시합니다.</div></div></aside><main><header class="top"><div><span class="eyebrow">WORLD OF WARCRAFT · RETAIL</span><h1 id="page-title">아제로스 주간 브리핑</h1><p class="subtitle">한국 플레이어를 위한 글로벌 와우 정보 레이더</p></div><div class="top-actions"><span class="chip">🇰🇷 한국 시간 KST</span><span class="chip" id="updated">확인 중</span><a class="button" href="https://worldofwarcraft.blizzard.com/ko-kr/news" target="_blank" rel="noopener">공식 소식 ↗</a></div></header><div id="content"></div><footer>WoW KR Radar v0.4.1 · 비공식 팬 대시보드 · Blizzard 및 모든 매체의 소식은 각 소유자에게 귀속됩니다. · 기사 전문을 재게시하지 않습니다.</footer></main><aside class="utility-sidebar" aria-label="옵션 메뉴"><div class="utility-heading"><span class="utility-eyebrow">PERSONAL SPACE</span><strong>옵션 · 기록</strong><p>필요할 때 꺼내보는 개인화 메뉴와 아카이브</p></div><nav id="option-nav" aria-label="개인화 및 히스토리"></nav><div class="utility-foot">기본 정보는 왼쪽 메뉴에서 확인하세요.</div></aside></div>`;renderNav();load();}
function renderNav(){
 const item=([k,t],optional=false)=>`<button type="button" class="nav-item ${optional?'utility-item':''} ${state.tab===k?'selected':''}" data-tab="${k}" aria-current="${state.tab===k?'page':'false'}"><span class="nav-icon">${icon[k]}</span><span>${t}</span></button>`;
 $('nav').innerHTML=menus.map(x=>item(x)).join('');
 $('option-nav').innerHTML=optionMenus.map(x=>item(x,true)).join('');
 document.querySelectorAll('[data-tab]').forEach(el=>el.onclick=()=>{state.tab=el.dataset.tab;renderNav();render();window.scrollTo({top:0,behavior:'smooth'});});
}
async function load(){try{let [latest,hist,versionRes]=await Promise.all([fetch('./data/latest.json?ts='+Date.now()),fetch('./data/history/index.json?ts='+Date.now()),fetch('./data/releases.json?ts='+Date.now())]);if(!latest.ok)throw Error('최신 데이터 파일 없음');state.meta=await latest.json();state.items=state.meta.items||[];state.history=(await hist.json()).weeks||[];state.releases=versionRes.ok?(await versionRes.json()).entries||[]:[];try{const m=await fetch('./data/kr_mplus.json?ts='+Date.now());state.mplus=m.ok?await m.json():null;}catch(e){state.mplus=null;}try{const r=await fetch('./data/kr_runs.json?ts='+Date.now());state.krRuns=r.ok?await r.json():null;}catch(e){state.krRuns=null;}try{const previous=state.history.find(w=>w.week!==state.meta.week);if(previous){const p=await fetch('./data/history/'+encodeURIComponent(previous.week)+'.json');if(p.ok)state.priorIds=new Set((await p.json()).items.map(x=>x.id));}}catch(e){console.warn('Previous snapshot unavailable',e)}render()}catch(e){$('content').innerHTML=`<div class="empty">데이터를 불러오지 못했습니다: ${safe(e.message)}. GitHub Pages에 배포되었는지 확인하세요.</div>`;}}
const curated=i=>i.filter(x=>state.cat==='전체'||x.category===state.cat).filter(x=>state.src==='전체'||x.source===state.src).filter(x=>(x.title_ko+' '+x.summary_ko+' '+x.source+' '+x.title_original).toLowerCase().includes(state.q.toLowerCase()));
function filters(){return `<div class="filters"><div class="filter-scroll">${cats.map(c=>`<button data-cat="${safe(c)}" class="filter ${state.cat===c?'on':''}">${safe(c)}</button>`).join('')}</div><div class="filter-control"><select id="source">${sources.map(s=>`<option ${state.src===s?'selected':''}>${s}</option>`).join('')}</select><label class="original-toggle"><input type="checkbox" id="original-toggle" ${state.showOriginal?'checked':''}/> 원제 보기</label><input type="search" id="search" value="${safe(state.q)}" placeholder="기사 / 직업 / 키워드 검색" aria-label="뉴스 검색"/></div></div>`}
function bindFilters(){if($('original-toggle'))$('original-toggle').onchange=e=>{state.showOriginal=e.target.checked;render()};document.querySelectorAll('[data-cat]').forEach(b=>b.onclick=()=>{state.cat=b.dataset.cat;render()});if($('source'))$('source').onchange=e=>{state.src=e.target.value;render()};if($('search'))$('search').oninput=e=>{state.q=e.target.value;clearTimeout(signalTimer);signalTimer=setTimeout(()=>{let cursor=document.activeElement?.id==='search';render();if(cursor){$('search')?.focus();$('search')?.setSelectionRange(state.q.length,state.q.length)}},150)}}
function cards(items){return items.length?items.map(x=>`<article class="article"><div class="art-top"><span class="source ${safe(x.source.toLowerCase().replace(/[^a-z]/g,''))}">${safe(x.source)}</span><span class="kind">${safe(x.category||'기타')}</span><span class="muted small">${formatted(x.published_at)} KST</span>${x.sample?'<span class="sample">초기 안내</span>':''}${!state.priorIds.has(x.id)&&state.priorIds.size?'<span class="sample">NEW</span>':''}${x.region!=='KR'&&!x.translated?'<span class="sample">미번역</span>':''}</div><a href="${safe(x.url)}" target="_blank" rel="noopener noreferrer" class="article-title">${safe(x.title_ko||x.title_original)} <span class="arrow">↗</span></a><p>${safe(x.summary_ko||'원문에서 상세 내용을 확인하세요.')}${state.showOriginal&&x.title_original&&x.title_original!==x.title_ko?'<br><span class="muted">원제: '+safe(x.title_original)+'</span>':''}</p><div class="article-foot"><span>${x.region==='KR'?'🇰🇷 국내':'🌐 글로벌'} · ${x.source==='Blizzard'?'Blizzard 검색 결과 · 원문 검증 필요': '외부 출처'}${x.url?.includes('news.google.com')?' · Google News 경유':''}</span><a href="${safe(x.url)}" target="_blank" rel="noopener noreferrer">원문 보기 ↗</a></div></article>`).join(''):'<div class="empty">조건에 맞는 항목이 없습니다. 필터를 변경해 보세요.</div>'}
function chooseItems(){return state.tab==='classes'?state.items.filter(x=>x.category==='직업·밸런스'):state.tab==='endgame'?state.items.filter(x=>x.category==='쐐기·레이드'):state.tab==='roadmap'?state.items.filter(x=>x.category==='로드맵'):state.items}
function heading(name,sub){return `<div class="section-heading"><div><h2>${name}</h2><p>${sub}</p></div></div>`}
function render(){if(!state.meta)return;let sample=state.meta.status==='starter_sample';$('updated').innerText= '기준 '+yearweek(state.meta.generated_at);$('side-status').innerText=sample?'초기 데이터 · 자동 수집 대기':'자동 수집 '+(state.meta.collection?.success||0)+'개 피드';$('page-title').innerText=({overview:'아제로스 주간 브리핑',news:'글로벌 뉴스 피드',classes:'직업·밸런스 인텔리전스',endgame:'쐐기·레이드 인사이트',roadmap:'시즌 업데이트 로드맵',history:'주간 뉴스 히스토리',versions:'개발 버전 히스토리',watch:'My Watch 관심 직업',krmplus:'한국 쐐기 브리핑',dps:'주간 DPS 추이'})[state.tab];if(state.tab==='history'){history();return};if(state.tab==='versions'){versionHistory();return};if(state.tab==='watch'){renderWatch();return};if(state.tab==='krmplus'){renderKrMplus();return};if(state.tab==='dps'){renderDps();return};let news=chooseItems();let count=news.length;let html='';if(state.tab==='overview')html+=`<section class="hero"><div class="hero-text"><span class="hero-label"><span class="live-dot"></span> WEEKLY WATCH · ${safe(state.meta.week)}</span><h2>아제로스의 변화,<br><em>한눈에 파악하세요.</em></h2><p>공식 발표부터 해외 메타, 한국 커뮤니티까지.<br>주간 업데이트와 과거 기록을 하나의 화면에서.</p><div class="hero-buttons"><button id="go-news" class="primary">이번 주 소식 확인 ↗</button><button id="go-hist" class="secondary">이전 브리핑 보기</button></div></div><div class="hero-graphic"><div class="radar-circle c1"></div><div class="radar-circle c2"></div><div class="radar-circle c3"></div><div class="radar-sweep"></div><div class="radar-core">W</div><span class="orbit one">✦</span><span class="orbit two">✦</span></div></section><div class="stats"><div class="stat"><small>수집된 항목</small><strong>${state.items.filter(x=>!x.sample).length}</strong><span>자동 수집 항목</span></div><div class="stat"><small>모니터링 정보원</small><strong>6<span class="unit">종</span></strong><span>국내 · 해외 포함</span></div><div class="stat"><small>보관된 주간 기록</small><strong>${state.history.length}</strong><span>누적 스냅샷</span></div><div class="stat"><small>이번 주</small><strong class="week-label">${safe(state.meta.week)}</strong><span>매주 월요일 07:00 KST</span></div></div>`;
if(state.tab==='overview')html+=`<section class="notice quality"><b>수집 품질</b><span>피드 성공 ${Number(state.meta.collection?.success||0)}/${Number(state.meta.collection?.attempted||0)} · 오류 ${Number(state.meta.collection?.errors?.length||0)}건 · 해외 제목/요약 번역 ${Number(state.meta.collection?.translated_count||0)}건 · 신규 번역 ${Number(state.meta.collection?.new_translations||0)}건 · 지난주 대비 신규 ${state.priorIds.size?state.items.filter(x=>!state.priorIds.has(x.id)).length+'건':'이전 주 기록 없음'}<br>제목 기반 자동 분류이며 원문 확인이 필요합니다. 외부 링크는 Google News를 경유할 수 있습니다.</span></section>`;
if(state.tab==='overview'&&state.meta.collection?.feed_results?.length){
 const rows=state.meta.collection.feed_results;
 html+=`<section class="feed"><details class="feed-health"><summary>정보원별 수집 현황 · ${rows.filter(x=>x.status==='ok').length}/${rows.length}개 피드 연결</summary><div class="health-grid">${rows.map((x,i)=>`<div class="health-item"><span>${safe(x.source)}${x.source.startsWith('Reddit')?' · 검색 색인 기반':''}</span><strong class="${x.status==='ok'?'ok':'failed'}">${x.status==='ok'?safe(x.count)+'건 수집':'수집 실패'}</strong></div>`).join('')}</div><p>검색·커뮤니티 서비스의 제한으로 빈 피드나 HTTP 오류가 발생할 수 있습니다. 수집 실패를 기사 0건과 구분합니다.</p></details></section>`;
}
if(state.tab==='roadmap')html+=`<div class="roadmap-banner"><h2>공식 로드맵 · 출시 일정</h2><p>아래 일정은 공식 확정 날짜가 아닐 수 있습니다. 날짜 미확정 콘텐츠는 추측으로 확정 표시하지 않습니다.</p><div class="milestones"><div><span>12.1.7</span><b>Echoes of the Worldcore</b><small>2026년 12월 초 · 현지 일정 기준</small></div><div><span>12.2</span><b>Eclipse 업데이트</b><small>겨울 시즌 · 상세 날짜 미확정</small></div><div><span>시즌 3</span><b>레이드 / 쐐기</b><small>시작일 공식 확정 여부 별도 검증</small></div></div><a href="https://worldofwarcraft.blizzard.com/en-us/news/24301145/world-of-warcraft-at-blizzcon-2026-news-round-up" target="_blank" rel="noopener">블리자드 로드맵 원문 확인 ↗</a></div>`;
if(sample)html+=`<div class="notice"><b>데모 데이터 표시 중</b><span>첫 GitHub Actions 수집이 실행되기 전입니다. 아래 링크는 실제 정보원으로 연결되지만, 자동 수집·자동 번역이 수행된 기사로 표시하지 않습니다.</span></div>`;
html+=`<section class="feed">${heading(state.tab==='overview'?'최신 인텔리전스':'수집 뉴스','기사 제목·RSS 기반 짧은 정보와 원문 링크 · 항목 '+count+'개')}${filters()}<div class="article-grid">${cards(curated(news))}</div></section>`;
if(state.tab==='overview')html+=`<section class="links">${heading('바로 가기','주요 소스와 게임 데이터 포털')}<div class="link-grid">${[['Blizzard KR','https://worldofwarcraft.blizzard.com/ko-kr/news'],['Wowhead Retail','https://www.wowhead.com/wow/retail/news'],['와우 인벤','https://www.inven.co.kr/wow/'],['Reddit Competitive','https://www.reddit.com/r/CompetitiveWoW/'],['Raider.IO','https://raider.io/'],['Warcraft Logs','https://www.warcraftlogs.com/']].map(([name,url])=>`<a href="${url}" target="_blank" rel="noopener">${name}<span>↗</span></a>`).join('')}</div></section>`;
$('content').innerHTML=html;bindFilters();if($('go-news'))$('go-news').onclick=()=>{state.tab='news';renderNav();render()};if($('go-hist'))$('go-hist').onclick=()=>{state.tab='history';renderNav();render()};}
function history(){const items=state.history;$('content').innerHTML=`<section class="hist-intro"><h2>주간 브리핑 아카이브</h2><p>자동 수집이 성공한 주차별 데이터는 JSON 파일로 영구 저장됩니다. 새 주가 시작되어도 과거 뉴스는 그대로 유지합니다.</p></section>${items.length?`<div class="timeline">${items.map(w=>`<article class="history-card"><div><b>${safe(w.week)}</b><p>${safe(w.date||'')}</p></div><strong>${Number(w.count||0)}개 기사</strong><a href="./data/history/${encodeURIComponent(w.week)}.json" download>주간 기록 JSON ↓</a><button class="history-view" data-week="${safe(w.week)}">기사 보기 ↗</button></article>`).join('')}</div><div id="history-results"></div>`:`<div class="empty">아직 생성된 주간 기록이 없습니다. 매주 월요일 자동 수집이 실행되면 이곳에 누적됩니다.</div>`}`;document.querySelectorAll('[data-week]').forEach(el=>el.onclick=async()=>{let r=await fetch('./data/history/'+encodeURIComponent(el.dataset.week)+'.json');if(r.ok){let d=await r.json();$('history-results').innerHTML=heading(safe(d.week)+' 보관 뉴스',d.items.length+'개 기사')+'<div class="article-grid">'+cards(d.items)+'</div>';$('history-results').scrollIntoView({behavior:'smooth'})}})}
function renderWatch(){
 const relevant=state.items.filter(watched);
 const selectedClasses=state.myWatch;
 $('content').innerHTML=`<section class="hist-intro"><span class="eyebrow">PERSONALIZED RETAIL NEWS</span><h2>My Watch · 직업 / 전문화</h2><p>관심 직업을 선택한 다음 전문화까지 좁힐 수 있습니다. 키워드 기반 뉴스 필터이며 실제 게임 성능 순위는 아닙니다. 선택 정보는 이 브라우저에만 보관됩니다.</p></section>
 <div class="watch-grid">${watchClasses.map(([name])=>`<label class="watch-option"><input type="checkbox" data-watch="${safe(name)}" ${selectedClasses.includes(name)?'checked':''}><span>${safe(name)}</span></label>`).join('')}</div>
 ${selectedClasses.length?`<section class="watch-spec-section"><h3>전문화 상세 선택 <small>(선택하지 않으면 해당 직업 전체)</small></h3>
 <div class="watch-spec-grid">${selectedClasses.map(name=>`<div class="watch-spec-group"><b>${safe(name)}</b>${(specOptions[name]||[]).map(spec=>`<label><input type="checkbox" data-spec="${safe(name+':'+spec[0])}" ${state.watchSpecs.includes(name+':'+spec[0])?'checked':''}> ${safe(spec[0])}</label>`).join('')}</div>`).join('')}</div></section>`:''}
 <section class="feed">${heading('관심 직업 소식',selectedClasses.length?`관심 직업 ${selectedClasses.join(' · ')} · 관련 뉴스 ${relevant.length}건`:'먼저 관심 직업을 선택하세요')}
 <div class="article-grid">${selectedClasses.length?cards(relevant):'<div class="empty">관심 직업을 선택하면 관련 뉴스가 나타납니다.</div>'}</div></section>`;
 document.querySelectorAll('[data-watch]').forEach(el=>el.onchange=()=>{state.myWatch=Array.from(document.querySelectorAll('[data-watch]:checked')).map(n=>n.dataset.watch);state.watchSpecs=state.watchSpecs.filter(token=>state.myWatch.some(n=>token.startsWith(n+':')));try{localStorage.setItem('wowkr_mywatch_v1',JSON.stringify(state.myWatch));localStorage.setItem('wowkr_watchspec_v1',JSON.stringify(state.watchSpecs));}catch(e){}renderWatch();});
 document.querySelectorAll('[data-spec]').forEach(el=>el.onchange=()=>{state.watchSpecs=Array.from(document.querySelectorAll('[data-spec]:checked')).map(n=>n.dataset.spec);try{localStorage.setItem('wowkr_watchspec_v1',JSON.stringify(state.watchSpecs));}catch(e){}renderWatch();});
}
function renderKrMplus(){
 const m=state.mplus;
 const live=m?.status==='live'&&Array.isArray(m.affixes)&&m.affixes.length>0;
 const title=live?safe(m.title||'KR 지역 이번 주 속성'):'현재 한국 지역 쐐기 속성을 가져오지 못했습니다';
 $('content').innerHTML=`<section class="hist-intro"><span class="eyebrow">MYTHIC+ · KOREA REGION</span><h2>한국 지역 쐐기 브리핑</h2><p>Raider.IO 공개 API를 통해 한국(KR) 지역 주간 쐐기 속성을 가져옵니다. 게임 내 상태나 서버별 캐릭터 순위를 임의로 추정하지 않습니다.</p></section>
 <div class="mplus-panel"><div class="mplus-header"><div><h3>${title}</h3><p>${live?'마지막 수집: '+safe(yearweek(m.retrieved_at)):'API 결과 없음 · 수집 상태를 확인하세요'}</p></div><a href="https://raider.io/mythic-plus/affixes" target="_blank" rel="noopener noreferrer">Raider.IO에서 확인 ↗</a></div>
 ${live?`<div class="mplus-affixes">${m.affixes.map(a=>`<article class="mplus-affix"><b>${safe(a.name)}</b><p>${safe(a.description)}</p></article>`).join('')}</div>`:'<div class="empty">외부 API에 접근하지 못했거나 응답 형식이 바뀌었습니다. 아래 공식 데이터 출처에서 확인하세요.</div>'}
 <p class="mplus-caption">출처: Raider.IO · 데이터 기준은 API 응답에 따름 · 실시간 순위/직업 메타는 아직 연결되지 않았습니다.</p></div>
 <section class="feed">${heading('한국 지역 상위 쐐기 기록 스냅샷','Raider.IO 공개 API 응답 일부 · 지역 전체 순위나 직업별 티어를 의미하지 않습니다')}
 ${state.krRuns?.status==='live'&&state.krRuns.runs?.length?`<div class="kr-runs-table"><table><thead><tr><th>던전</th><th>단수</th><th>점수</th><th>원문</th></tr></thead><tbody>${state.krRuns.runs.map(r=>`<tr><td>${safe(r.dungeon)}</td><td>+${Number(r.level)}</td><td>${r.score==null?'—':Number(r.score).toFixed(1)}</td><td>${r.url?'<a href="'+safe(r.url)+'" target="_blank" rel="noopener noreferrer">기록 확인 ↗</a>':'출처 내 확인'}</td></tr>`).join('')}</tbody></table><p class="mplus-caption">수집: ${safe(yearweek(state.krRuns.retrieved_at))} · 자료 출처: Raider.IO · 수집한 기록 순서이며 공식 한국 서버 전체 순위가 아닙니다.</p></div>`: '<div class="empty">한국 지역 기록 API 응답을 검증할 수 없어 표를 표시하지 않습니다. Raider.IO 원문을 이용해 주세요.</div>'}
 </section>
 <section class="links">${heading('한국 서버 관련 참고 사이트','실제 순위와 로그는 원문에서 확인하세요')}<div class="link-grid">
 <a href="https://raider.io/" target="_blank" rel="noopener noreferrer">Raider.IO <span>↗</span></a>
 <a href="https://www.warcraftlogs.com/" target="_blank" rel="noopener noreferrer">Warcraft Logs <span>↗</span></a>
 <a href="https://worldofwarcraft.blizzard.com/ko-kr/" target="_blank" rel="noopener noreferrer">블리자드 한국 <span>↗</span></a></div></section>`;
}
const dpsClassLabels={'death-knight':'죽음의 기사','demon-hunter':'악마사냥꾼',druid:'드루이드',evoker:'기원사',hunter:'사냥꾼',mage:'마법사',monk:'수도사',paladin:'성기사',priest:'사제',rogue:'도적',shaman:'주술사',warlock:'흑마법사',warrior:'전사'};
const dpsNameMap={'assassination rogue':'암살 도적','subtlety rogue':'잠행 도적','outlaw rogue':'무법 도적','elemental shaman':'정기 주술사','enhancement shaman':'고양 주술사','arms warrior':'무기 전사','fury warrior':'분노 전사','devourer demon-hunter':'포식 악마사냥꾼','havoc demon-hunter':'파멸 악마사냥꾼','demonology warlock':'악마 흑마법사','affliction warlock':'고통 흑마법사','destruction warlock':'파괴 흑마법사','windwalker monk':'풍운 수도사','frost death-knight':'냉기 죽음의 기사','unholy death-knight':'부정 죽음의 기사','fire mage':'화염 마법사','arcane mage':'비전 마법사','frost mage':'냉기 마법사','marksmanship hunter':'사격 사냥꾼','beast-mastery hunter':'야수 사냥꾼','survival hunter':'생존 사냥꾼','retribution paladin':'징벌 성기사','feral druid':'야성 드루이드','balance druid':'조화 드루이드','shadow priest':'암흑 사제','devastation evoker':'황폐 기원사','augmentation evoker':'증강 기원사'};
async function loadDps(){
 if(state.dpsLoaded)return;
 state.dpsLoaded=true;
 try{
  const r=await fetch('./data/dps/index.json?ts='+Date.now());
  if(!r.ok)throw Error('DPS 인덱스 접근 불가');
  const ix=await r.json();state.dpsIndex=ix;
  const recent=(ix.periods||[]).slice(0,12);
  const result=await Promise.all(recent.map(async p=>{
   if(!/^period-\d+\.json$/.test(p.file||''))return null;
   try{const r=await fetch('./data/dps/'+p.file);return r.ok?await r.json():null;}catch(e){return null;}
  }));
  state.dpsWeeks=result.filter(x=>x&&x.status==='ok').sort((a,b)=>a.period-b.period);
 }catch(e){state.dpsIndex={status:'unavailable',error:e.message};state.dpsWeeks=[];}
 if(state.tab==='dps')renderDps();
}
function dpsChart(entries,metric){
 const valid=entries.filter(x=>x.entry&&Number.isFinite(x.entry[metric]));
 if(!valid.length)return '<div class="empty">선택한 전문화의 확인된 주별 DPS 기록이 없습니다.</div>';
 const values=valid.map(x=>x.entry[metric]/1000);
 let lo=Math.floor(Math.min(...values)*.95/10)*10,hi=Math.ceil(Math.max(...values)*1.05/10)*10;
 if(hi<=lo)hi=lo+10;
 const xx=i=>valid.length===1?440:70+i*800/(valid.length-1);
 const yy=v=>236-(v-lo)*185/(hi-lo);
 const dots=valid.map((p,i)=>`<circle cx="${xx(i)}" cy="${yy(values[i])}" r="5" fill="#e4b56d"><title>Period ${p.period}: ${Math.round(p.entry[metric]).toLocaleString('ko-KR')} DPS · 표본 ${p.entry.runs.toLocaleString('ko-KR')}회</title></circle>`).join('');
 const ticks=Array.from({length:5},(_,i)=>{const val=lo+(hi-lo)*i/4;const y=yy(val);return `<line x1="65" y1="${y}" x2="880" y2="${y}" stroke="#34475a" stroke-dasharray="4 6"/><text x="57" y="${y+4}" text-anchor="end" fill="#9eb2c7" font-size="13">${Math.round(val)}K</text>`}).join('');
 const points=valid.map((p,i)=>xx(i)+','+yy(values[i])).join(' ');
 const labels=valid.map((p,i)=>`<text x="${xx(i)}" y="262" text-anchor="middle" fill="#9eb2c7" font-size="12">${p.period}</text>`).join('');
 return `<div class="dps-chart-wrap"><svg viewBox="0 0 920 280" role="img" aria-label="Period별 ${metric==='avg_dps'?'평균':'상위 5%'} DPS 추이">${ticks}<polyline points="${points}" fill="none" stroke="#e4b56d" stroke-width="3" stroke-linejoin="round"/>${dots}${labels}</svg></div>`;
}
function renderDps(){
 if(!state.dpsLoaded){$('content').innerHTML='<div class="empty">MythicStats 주간 자료를 확인하는 중입니다.</div>';loadDps();return;}
 const weeks=state.dpsWeeks,latest=weeks.at(-1);
 const all=latest?.items||[];
 const classes=[...new Set(all.map(x=>x.class))].sort();
 if(classes.length&&!classes.includes(state.dpsClass))state.dpsClass=classes[0];
 const choices=all.filter(x=>x.class===state.dpsClass);
 if(choices.length&&!choices.some(x=>x.name===state.dpsSpec))state.dpsSpec=choices[0].name;
 const entries=weeks.map(w=>({period:w.period,entry:w.items.find(x=>x.name===state.dpsSpec),url:w.source_url})).filter(x=>x.entry);
 const current=entries.at(-1)?.entry;
 const m=state.dpsMetric;
 $('content').innerHTML=`<section class="hist-intro"><span class="eyebrow">MYTHICSTATS · WEEKLY DAMAGE TREND</span><h2>쐐기 전문화 DPS 주간 추이</h2><p>Mythicstats의 Warcraft Logs 기반 공개 통계에서 <b>전체 던전 시간 기준 DPS</b>를 주간 Period로 추적합니다. 현재 원본 화면의 쐐기 <b>16~24단</b> 범위, 표본 수와 기간 차이를 함께 확인하세요.</p><a class="dps-source-link" href="https://mythicstats.com/dps" target="_blank" rel="noopener noreferrer">Mythicstats 원본 열기 ↗</a></section>
 ${weeks.length?`<section class="dps-panel">
 <div class="dps-controls"><label>직업<select id="dps-class">${classes.map(x=>`<option value="${safe(x)}" ${state.dpsClass===x?'selected':''}>${safe(dpsClassLabels[x]||x)}</option>`).join('')}</select></label><label>전문화<select id="dps-spec">${choices.map(x=>`<option value="${safe(x.name)}" ${state.dpsSpec===x.name?'selected':''}>${safe(dpsNameMap[x.name]||x.name)}</option>`).join('')}</select></label><label>분석 기준<select id="dps-metric"><option value="avg_dps" ${m==='avg_dps'?'selected':''}>평균 DPS</option><option value="top_dps" ${m==='top_dps'?'selected':''}>상위 5% DPS</option></select></label></div>
 <div class="dps-summary"><div><small>선택 전문화</small><strong>${safe(dpsNameMap[state.dpsSpec]||state.dpsSpec)}</strong></div><div><small>최근 평균 DPS</small><strong>${current?Math.round(current.avg_dps/1000).toLocaleString('ko-KR')+'K':'—'}</strong></div><div><small>최근 순위 / 표본</small><strong>${current?'#'+current.rank+' · '+current.runs.toLocaleString('ko-KR')+'회':'—'}</strong></div><div><small>수집 Period</small><strong>${weeks.length}주</strong></div></div>
 <h3>${m==='avg_dps'?'평균':'상위 5%'} DPS 추이</h3>
 ${dpsChart(entries,m)}
 <p class="dps-note">${weeks.length<2?'현재 검증된 주간 자료가 1개라 비교선은 아직 생성되지 않았습니다. 이후 자동 수집 시 누적됩니다.':'같은 전문화의 주별 수치를 연결했습니다. 시즌·패치·단수·표본 차이는 직접 성능 변화와 구분해야 합니다.'}</p>
 <div class="kr-runs-table"><table><thead><tr><th>Period</th><th>순위</th><th>Avg DPS</th><th>Top 5%</th><th>Runs</th><th>출처</th></tr></thead><tbody>${entries.slice().reverse().map(w=>`<tr><td>${w.period}</td><td>#${w.entry.rank}</td><td>${Math.round(w.entry.avg_dps/1000).toLocaleString('ko-KR')}K</td><td>${Math.round(w.entry.top_dps/1000).toLocaleString('ko-KR')}K</td><td>${w.entry.runs.toLocaleString('ko-KR')}</td><td><a href="${safe(w.url)}" target="_blank" rel="noopener noreferrer">원문 ↗</a></td></tr>`).join('')}</tbody></table></div></section>`:'<div class="empty">아직 검증된 Mythicstats DPS 주간 수치가 없습니다. 수집 워크플로가 실행되면 이곳에 저장됩니다. 원본 사이트에서 바로 확인할 수 있습니다.</div>'}
 <p class="version-footnote">출처: <a href="https://mythicstats.com/dps" target="_blank" rel="noopener noreferrer">Mythicstats</a> · 쐐기 16~24단 전체 던전 시간 DPS (WCL 계산 기준) · 주간 시작 시 표본 수가 적을 수 있음 · 기존 Period는 자동 저장됩니다.</p>`;
 const cls=$('dps-class');if(cls)cls.onchange=e=>{state.dpsClass=e.target.value;state.dpsSpec='';renderDps()};
 const spec=$('dps-spec');if(spec)spec.onchange=e=>{state.dpsSpec=e.target.value;renderDps()};
 const metric=$('dps-metric');if(metric)metric.onchange=e=>{state.dpsMetric=e.target.value;renderDps()};
}
function versionHistory(){
  const items=state.releases||[];
  $('content').innerHTML=`<section class="hist-intro"><span class="eyebrow">VERSION CONTROL · CHANGELOG</span><h2>WoW KR Radar 개발 히스토리</h2><p>사이트 개발·업데이트 내역을 주간 뉴스 기록과 별도로 관리합니다. 버전별 주요 변경사항과 GitHub 코드 이력 및 요약 보고서를 확인할 수 있습니다.</p><div class="version-mini-stats"><span>현재 버전 <strong>V0.4.1</strong></span><span>기록된 버전 <strong>${items.length}개</strong></span><span>문서 <strong>PDF · PPTX</strong></span></div></section>
  ${items.length?'<div class="release-list">'+items.map((r,index)=>`
    <article class="release-card">
      <div class="release-top"><span class="release-version">V${safe(r.version)}</span><span class="kind">${safe(r.type)}</span>${index===0?'<span class="sample">최신 버전</span>':''}<time>${safe(r.date)}</time></div>
      <h3>${safe(r.title)}</h3><p class="release-summary">${safe(r.summary)}</p>
      <details ${index===0?'open':''}><summary>주요 변경사항 ${r.changes.length}개 · 상세 보기</summary><ul>${r.changes.map(x=>'<li>'+safe(x)+'</li>').join('')}</ul>${r.notes.length?'<div class="release-note">'+r.notes.map(x=>'<p>※ '+safe(x)+'</p>').join('')+'</div>':''}</details>
      <div class="release-actions">
        <a href="./reports/WoW_KR_Radar_v${encodeURIComponent(r.version)}_History.pdf" download>PDF 요약 다운로드 ↓</a>
        <a href="./reports/WoW_KR_Radar_v${encodeURIComponent(r.version)}_History.pptx" download>PPTX 장표 다운로드 ↓</a>
        <a target="_blank" rel="noopener noreferrer" href="https://github.com/minijoaa85-cpu/wow-kr-radar/commit/${encodeURIComponent(r.commit)}">코드 변경 이력 ↗</a>
      </div>
    </article>`).join('')+'</div>':'<div class="empty">아직 등록된 개발 버전 기록이 없습니다.</div>'}
  <p class="version-footnote">다운로드 자료는 주요 변경점 요약 문서이며 과거 전체 화면이나 실행 상태를 복원하는 코드 백업 파일은 아닙니다.</p>`;
}
init();
