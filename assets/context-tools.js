(()=>{
const READ='cyberlawReadingListV1';
const script=document.currentScript;
const assetBase=script?new URL('.',script.src):new URL('assets/',location.href);
const siteRoot=new URL('../',assetBase);
const esc=s=>String(s??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const load=(k,d)=>{try{const v=JSON.parse(localStorage.getItem(k)||'');return v??d}catch{return d}};
const save=(k,v)=>localStorage.setItem(k,JSON.stringify(v));
const clean=u=>{try{const x=new URL(u,location.href);x.search='';x.hash='';return x.href}catch{return u}};
const pagePath=()=>location.pathname.split('/cyberlaw-research/')[1]||location.pathname.replace(/^\//,'');
const pageTitle=()=>document.querySelector('main h1')?.textContent.trim()||document.title.replace(/｜.*$/,'').trim();
const pageDate=()=>{const raw=(document.querySelector('.eyebrow')?.textContent||'')+' '+document.title;const m=raw.match(/(20\d{2})[.\/-](\d{1,2})[.\/-](\d{1,2})/);return m?`${m[1]}-${String(+m[2]).padStart(2,'0')}-${String(+m[3]).padStart(2,'0')}`:''};
const cnDate=d=>{const m=(d||'').match(/(20\d{2})-(\d{2})-(\d{2})/);return m?`${m[1]}年${+m[2]}月${+m[3]}日`:d||''};
const today=()=>{const d=new Date();return `${d.getFullYear()}-${String(d.getMonth()+1).padStart(2,'0')}-${String(d.getDate()).padStart(2,'0')}`};
const TAG_RULES={
'人工智能':['人工智能','AI','算法','模型','大模型','智能体','agentic','generative'],
'数据与隐私':['数据','隐私','个人信息','GDPR','privacy','data protection','数据要素'],
'平台治理':['平台','platform','内容治理','推荐系统','社交媒体'],
'竞争法':['反垄断','竞争','垄断','antitrust','competition'],
'网络安全':['网络安全','cyber','安全事件','漏洞','CISA','关键基础设施'],
'知识产权':['版权','著作权','知识产权','copyright','patent'],
'算法行政':['行政','政府','公共部门','自动化决策','due process','正当程序'],
'国际治理':['欧盟','EU','美国','韩国','日本','新加坡','国际','global','跨境'],
'数字法治':['法治','rule of law','程序','权利','责任','监管']
};
const NEWS_TOPIC_RULES={
'智能体AI':['智能体','agentic','ai agent','自主代理'],
'生成式AI':['生成式ai','生成式人工智能','generative ai','大模型','基础模型','foundation model'],
'AI安全':['ai安全','模型安全','前沿模型','失控','对齐','红队','事故披露'],
'AI行政应用':['政府大模型','政务助手','公共部门ai','行政自动化','自动化行政','ai政务'],
'算法歧视':['算法歧视','algorithmic discrimination','招聘算法','就业算法','公平性'],
'自动化决策':['自动化决策','automated decision','adm','算法决定'],
'数据要素':['数据要素','公共数据','数据产品','数据交易','数据市场','授权运营'],
'数据跨境':['数据跨境','跨境数据','cross-border data','数据出境'],
'个人信息保护':['个人信息','隐私','gdpr','data protection','pipl','删除权','被遗忘权'],
'生物识别':['生物识别','人脸识别','面部识别','biometric','facial recognition'],
'儿童数据':['儿童','未成年人','children','minor','kids'],
'平台责任':['平台责任','内容治理','推荐算法','平台治理','social media','在线平台'],
'反垄断':['反垄断','antitrust','垄断','市场支配','competition authority'],
'平台竞争':['平台竞争','二选一','自我优待','self-preferencing','应用商店','app store'],
'知识产权':['知识产权','版权','著作权','copyright','patent'],
'AI训练版权':['ai训练','训练数据','fair use','合理使用','版权训练','训练版权'],
'网络安全':['网络安全','cybersecurity','漏洞','入侵','勒索','ransomware'],
'关键基础设施':['关键基础设施','critical infrastructure','基础设施安全','反破坏'],
'后量子密码':['后量子','post-quantum','pqc','量子密码'],
'芯片与出口管制':['芯片','半导体','出口管制','export control','gpu','先进计算'],
'算力基础设施':['算力','数据中心','compute','token','词元','算力网'],
'深度伪造':['深度伪造','deepfake','合成内容','数字水印'],
'选举与AI':['选举','election','投票','选民','campaign'],
'自主武器':['自主武器','autonomous weapon','laws','致命自主武器'],
'国家安全':['国家安全','national security','军事','国防','军方'],
'国际AI治理':['ai治理','人工智能治理','ai act','ai office','全球ai治理','国际规则'],
'竞争与知识产权':['知识产权反垄断','ip antitrust','patent antitrust']
};
const STOPWORDS=new Set(['中国','美国','欧盟','英国','韩国','日本','新加坡','澳大利亚','巴西','印度','德国','法国','发布','公布','表示','提出','推进','推动','加强','监管','管理','政策','规则','办法','意见','计划','人工智能','科技','数字','网络','数据','平台','研究','关于','相关','进一步','正式','最新']);
const tagsFor=text=>{const low=(text||'').toLowerCase();return Object.entries(TAG_RULES).filter(([,ws])=>ws.some(w=>low.includes(w.toLowerCase()))).map(([t])=>t).slice(0,6)};
const topicsFor=text=>{const low=(text||'').toLowerCase();return Object.entries(NEWS_TOPIC_RULES).filter(([,ws])=>ws.some(w=>low.includes(w.toLowerCase()))).map(([t])=>t)};
function keywordsFor(title,meta,text){const src=`${title} ${meta} ${(text||'').slice(0,800)}`,out=[],seen=new Set();for(const m of src.matchAll(/\b[A-Z][A-Z0-9.-]{1,12}\b|\b[A-Za-z][A-Za-z0-9.-]{2,24}\b/g))out.push(m[0]);for(const m of src.matchAll(/[“《]([^”》]{2,18})[”》]/g))out.push(m[1]);for(const part of title.replace(/^\s*\d+[.、]\s*/,'').split(/[：:，,；;、“”《》()（）\-—]/)){const p=part.trim();if(p.length>=2&&p.length<=14&&!STOPWORDS.has(p))out.push(p)}return out.filter(x=>{const k=x.trim().toLowerCase();if(k.length<2||seen.has(k))return false;seen.add(k);return true}).slice(0,18)}
let toastTimer;function toast(msg){let e=document.querySelector('.fav-toast');if(!e){e=document.createElement('div');e.className='fav-toast';document.body.appendChild(e)}e.textContent=msg;requestAnimationFrame(()=>e.classList.add('show'));clearTimeout(toastTimer);toastTimer=setTimeout(()=>e.classList.remove('show'),1500)}
async function copyText(s,msg='已复制'){try{await navigator.clipboard.writeText(s);toast(msg)}catch{toast('复制失败')}}
async function index(){try{return await fetch(new URL('research-index.json',assetBase)).then(r=>r.json())}catch{return[]}}
async function newsIndex(){try{return await fetch(new URL('news-index.json',assetBase)).then(r=>r.json())}catch{return[]}}
function itemInfo(target,idx,articleLevel=false){
 const h=articleLevel?null:target.querySelector('h3,h2');
 const title=(h?.textContent||pageTitle()).replace(/^\s*\d+[.、]\s*/,'').trim();
 const meta=target.querySelector('.brief-meta')?.textContent.trim()||'';
 const source=target.querySelector('.source a');
 const text=target.innerText||'';
 const tags=tagsFor(title+' '+text),topics=topicsFor(title+' '+meta+' '+text),keywords=keywordsFor(title,meta,text);
 const date=pageDate();let itemDate=date;
 const md=meta.match(/(?:(20\d{2})年)?(\d{1,2})月(\d{1,2})日/);if(md)itemDate=`${md[1]||date.slice(0,4)}-${String(+md[2]).padStart(2,'0')}-${String(+md[3]).padStart(2,'0')}`;
 const institution=meta.split('·').map(s=>s.trim()).filter(Boolean).slice(-1)[0]||'网信法研究每日推送';
 const site=source?.textContent.trim()||'网信法研究每日推送';
 const url=source?.href||clean(location.href)+(target.id?`#${target.id}`:'');
 return {title,meta,text,tags,topics,keywords,date:itemDate,institution,site,url,id:target.id||`research-item-${idx+1}`,articleLevel};
}
function citation(info,fmt){
 const d=info.date||pageDate(),access=today(),author=info.institution||info.site||'网信法研究每日推送',url=info.url,title=info.title,site=info.site||'网信法研究每日推送';
 if(fmt==='law')return `${author}：《${title}》，载${site}${d?cnDate(d):''}，${url}。`;
 if(fmt==='bluebook')return `${author}, ${title}, ${site}${d?` (${d})`:''}, ${url}.`;
 if(fmt==='bibtex')return `@online{cyberlaw${(d||access).replaceAll('-','')},\n  author={${author}},\n  title={${title}},\n  date={${d||''}},\n  url={${url}},\n  urldate={${access}}\n}`;
 if(fmt==='ris')return `TY  - ELEC\nTI  - ${title}\nAU  - ${author}\nPY  - ${(d||'').slice(0,4)}\nUR  - ${url}\nY2  - ${access}\nER  -`;
 return `${author}. ${title}[EB/OL]. ${d?`(${d})`:''}[${access}]. ${url}.`;
}
function relatedRecords(info,all,limit=5){const cur=pagePath();const score=x=>{if(x.path===cur)return-1;let s=(x.tags||[]).filter(t=>info.tags.includes(t)).length*4;if(x.category&&document.body.innerText.includes(x.category))s+=1;return s};return all.map(x=>[x,score(x)]).filter(([,s])=>s>0).sort((a,b)=>b[1]-a[1]||String(b[0].date).localeCompare(String(a[0].date))).slice(0,limit).map(([x])=>x)}
function norm(s){return (s||'').toLowerCase().replace(/[\s\p{P}\p{S}]+/gu,'')}
function ngrams(s,n=2){const x=norm(s),set=new Set();for(let i=0;i<=x.length-n;i++)set.add(x.slice(i,i+n));return set}
function titleSimilarity(a,b){const A=ngrams(a),B=ngrams(b);if(!A.size||!B.size)return 0;let hit=0;for(const x of A)if(B.has(x))hit++;return hit/Math.max(1,Math.min(A.size,B.size))}
function keywordHits(info,x){const hay=norm(`${x.title} ${(x.keywords||[]).join(' ')} ${x.meta||''}`);let hit=0;for(const k of info.keywords||[]){const nk=norm(k);if(nk.length>=3&&hay.includes(nk))hit++}return Math.min(hit,4)}
function timelineScore(info,x){
 const currentId=`${pagePath()}#${info.id}`;if(x.id===currentId)return -1;
 const topicHits=(x.topics||[]).filter(t=>(info.topics||[]).includes(t)).length;
 const kw=keywordHits(info,x),sim=titleSimilarity(info.title,x.title);
 const broad=(x.tags||[]).filter(t=>(info.tags||[]).includes(t)).length;
 let score=topicHits*10+kw*6+sim*12+Math.min(broad,2)*1.5;
 // Broad tags alone must never create a timeline relationship.
 if(topicHits===0&&kw===0&&sim<0.24)return -1;
 if(topicHits===0&&kw===1&&sim<0.12)return -1;
 return score;
}
function closestNews(info,all,limit=6){
 const ranked=all.map(x=>[x,timelineScore(info,x)]).filter(([,s])=>s>=11).sort((a,b)=>b[1]-a[1]||String(a[0].date).localeCompare(String(b[0].date)));
 // Avoid multiple near-duplicate headlines from the same day unless the wording is materially different.
 const picked=[];
 for(const [x,s] of ranked){if(picked.some(y=>y.date===x.date&&titleSimilarity(y.title,x.title)>.72))continue;picked.push({...x,_score:s});if(picked.length>=limit)break}
 return picked.sort((a,b)=>String(a.date).localeCompare(String(b.date)));
}
function readItems(){return load(READ,[])}
function isRead(info){return readItems().some(x=>x.itemKey===`${clean(location.href)}#${info.id}`)}
function toggleRead(info,button){let a=readItems(),key=`${clean(location.href)}#${info.id}`,i=a.findIndex(x=>x.itemKey===key);if(i>=0){a.splice(i,1);toast('已从稍后读移除')}else{a.unshift({id:'r_'+Date.now().toString(36),itemKey:key,pageUrl:clean(location.href)+(info.id?`#${info.id}`:''),title:info.title,category:document.querySelector('.eyebrow')?.textContent.trim()||'',date:info.date,createdAt:new Date().toISOString(),tags:info.tags,project:'',note:''});toast('已加入稍后读')}save(READ,a);button.textContent=isRead(info)?'✓ 稍后读':'稍后读'}
function renderRelated(panel,info,all){const xs=relatedRecords(info,all,6);panel.innerHTML=`<div class="ctx-panel-title">关联阅读</div>${xs.length?`<div class="ctx-related">${xs.map(x=>`<a href="${new URL(x.path,siteRoot).href}"><strong>${esc(x.title)}</strong><span>${esc(x.date||'')} · ${esc(x.category||'')}</span></a>`).join('')}</div>`:'<p class="ctx-empty">暂无高度相关的历史内容。</p>'}`}
function renderTimeline(panel,info,news){const xs=closestNews(info,news,6);panel.innerHTML=`<div class="ctx-panel-title">相关新闻时间线</div><p class="ctx-timeline-note">已统计站内 <strong>${news.length}</strong> 条历史新闻，仅显示与当前内容最密切相关的${xs.length?` ${xs.length} 条`:''}。</p>${xs.length?`<div class="ctx-timeline">${xs.map(x=>`<a href="${new URL(x.path,siteRoot).href}#${encodeURIComponent(x.anchor)}"><time>${esc(x.date||'')}</time><span><strong>${esc(x.title)}</strong>${x.meta?`<small>${esc(x.meta)}</small>`:''}</span></a>`).join('')}</div>`:'<p class="ctx-empty">当前内容与既往新闻尚未形成足够紧密的事件链，不强行生成时间线。</p>'}`}
function renderCitation(panel,info){panel.innerHTML=`<div class="ctx-panel-title">引用与导出</div><div class="ctx-cite-tabs"><button data-fmt="gb">GB/T 7714</button><button data-fmt="law">《法学引注手册》</button><button data-fmt="bluebook">Bluebook</button><button data-fmt="bibtex">BibTeX</button><button data-fmt="ris">RIS</button></div><pre class="ctx-citation"></pre><button class="ctx-copy">复制当前格式</button>`;const out=panel.querySelector('.ctx-citation'),tabs=[...panel.querySelectorAll('[data-fmt]')];let fmt='gb';const show=()=>{out.textContent=citation(info,fmt);tabs.forEach(b=>b.classList.toggle('active',b.dataset.fmt===fmt))};tabs.forEach(b=>b.onclick=()=>{fmt=b.dataset.fmt;show()});panel.querySelector('.ctx-copy').onclick=()=>copyText(citation(info,fmt),'引用已复制');show()}
function makeActions(target,idx,all,news,articleLevel=false){if(target.querySelector(':scope > .ctx-actions'))return;target.id=target.id||`research-item-${idx+1}`;const info=itemInfo(target,idx,articleLevel);const wrap=document.createElement('div');wrap.className='ctx-actions';wrap.innerHTML=`<button data-act="read">${isRead(info)?'✓ 稍后读':'稍后读'}</button><button data-act="related">关联阅读</button><button data-act="timeline">专题时间线</button><button data-act="cite">引用</button>`;const panel=document.createElement('div');panel.className='ctx-inline-panel';wrap.appendChild(panel);const read=wrap.querySelector('[data-act="read"]');read.onclick=()=>toggleRead(info,read);wrap.querySelector('[data-act="related"]').onclick=()=>{const open=panel.dataset.mode==='related'&&panel.classList.contains('show');panel.dataset.mode='related';if(open){panel.classList.remove('show');return}renderRelated(panel,info,all);panel.classList.add('show')};wrap.querySelector('[data-act="timeline"]').onclick=()=>{const open=panel.dataset.mode==='timeline'&&panel.classList.contains('show');panel.dataset.mode='timeline';if(open){panel.classList.remove('show');return}renderTimeline(panel,info,news);panel.classList.add('show')};wrap.querySelector('[data-act="cite"]').onclick=()=>{const open=panel.dataset.mode==='cite'&&panel.classList.contains('show');panel.dataset.mode='cite';if(open){panel.classList.remove('show');return}renderCitation(panel,info);panel.classList.add('show')};if(articleLevel){const first=target.firstElementChild;first?target.insertBefore(wrap,first):target.appendChild(wrap)}else target.appendChild(wrap);if(location.hash===`#${target.id}`)setTimeout(()=>target.scrollIntoView({block:'start'}),80)}
async function init(){const css=new URL('context-tools.css',assetBase).href;if(!document.querySelector(`link[href="${css}"]`)){const l=document.createElement('link');l.rel='stylesheet';l.href=css;document.head.appendChild(l)}const [all,news]=await Promise.all([index(),newsIndex()]);let items=[...document.querySelectorAll('.article-body .brief-item')];if(items.length){items.forEach((x,i)=>makeActions(x,i,all,news,false));return}const root=document.querySelector('.article-body .article-wrap,.article-body,.article .reading,.article');if(root)makeActions(root,0,all,news,true)}
document.addEventListener('DOMContentLoaded',init);
})();