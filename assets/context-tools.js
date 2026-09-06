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
const tagsFor=text=>{const low=(text||'').toLowerCase();return Object.entries(TAG_RULES).filter(([,ws])=>ws.some(w=>low.includes(w.toLowerCase()))).map(([t])=>t).slice(0,6)};
let toastTimer;function toast(msg){let e=document.querySelector('.fav-toast');if(!e){e=document.createElement('div');e.className='fav-toast';document.body.appendChild(e)}e.textContent=msg;requestAnimationFrame(()=>e.classList.add('show'));clearTimeout(toastTimer);toastTimer=setTimeout(()=>e.classList.remove('show'),1500)}
async function copyText(s,msg='已复制'){try{await navigator.clipboard.writeText(s);toast(msg)}catch{toast('复制失败')}}
async function index(){try{return await fetch(new URL('research-index.json',assetBase)).then(r=>r.json())}catch{return[]}}
function itemInfo(target,idx){
 const h=target.querySelector('h3,h2');
 const title=(h?.textContent||pageTitle()).replace(/^\s*\d+[.、]\s*/,'').trim();
 const meta=target.querySelector('.brief-meta')?.textContent.trim()||'';
 const source=target.querySelector('.source a');
 const text=target.innerText||'';
 const tags=tagsFor(title+' '+text);
 const date=pageDate();
 let itemDate=date;
 const md=meta.match(/(?:(20\d{2})年)?(\d{1,2})月(\d{1,2})日/);
 if(md)itemDate=`${md[1]||date.slice(0,4)}-${String(+md[2]).padStart(2,'0')}-${String(+md[3]).padStart(2,'0')}`;
 const institution=meta.split('·').map(s=>s.trim()).filter(Boolean).slice(-1)[0]||'网信法研究每日推送';
 const site=source?.textContent.trim()||'网信法研究每日推送';
 const url=source?.href||clean(location.href)+(target.id?`#${target.id}`:'');
 return {title,meta,text,tags,date:itemDate,institution,site,url,id:target.id||`research-item-${idx+1}`};
}
function citation(info,fmt){
 const d=info.date||pageDate(), access=today(), author=info.institution||info.site||'网信法研究每日推送', url=info.url, title=info.title, site=info.site||'网信法研究每日推送';
 if(fmt==='law')return `${author}：《${title}》，载${site}${d?cnDate(d):''}，${url}。`;
 if(fmt==='bluebook')return `${author}, ${title}, ${site}${d?` (${d})`:''}, ${url}.`;
 if(fmt==='bibtex')return `@online{cyberlaw${(d||access).replaceAll('-','')},\n  author={${author}},\n  title={${title}},\n  date={${d||''}},\n  url={${url}},\n  urldate={${access}}\n}`;
 if(fmt==='ris')return `TY  - ELEC\nTI  - ${title}\nAU  - ${author}\nPY  - ${(d||'').slice(0,4)}\nUR  - ${url}\nY2  - ${access}\nER  -`;
 return `${author}. ${title}[EB/OL]. ${d?`(${d})`:''}[${access}]. ${url}.`;
}
function relatedRecords(info,all,limit=5){
 const cur=pagePath();
 const score=x=>{if(x.path===cur)return-1;let s=(x.tags||[]).filter(t=>info.tags.includes(t)).length*4;if(x.category&&document.body.innerText.includes(x.category))s+=1;return s};
 return all.map(x=>[x,score(x)]).filter(([,s])=>s>0).sort((a,b)=>b[1]-a[1]||String(b[0].date).localeCompare(String(a[0].date))).slice(0,limit).map(([x])=>x);
}
function readItems(){return load(READ,[])}
function isRead(info){return readItems().some(x=>x.itemKey===`${clean(location.href)}#${info.id}`)}
function toggleRead(info,button){let a=readItems(),key=`${clean(location.href)}#${info.id}`,i=a.findIndex(x=>x.itemKey===key);if(i>=0){a.splice(i,1);toast('已从稍后读移除')}else{a.unshift({id:'r_'+Date.now().toString(36),itemKey:key,pageUrl:clean(location.href)+(info.id?`#${info.id}`:''),title:info.title,category:document.querySelector('.eyebrow')?.textContent.trim()||'',date:info.date,createdAt:new Date().toISOString(),tags:info.tags,project:'',note:''});toast('已加入稍后读')}save(READ,a);button.textContent=isRead(info)?'✓ 稍后读':'稍后读'}
function renderRelated(panel,info,all){const xs=relatedRecords(info,all,6);panel.innerHTML=`<div class="ctx-panel-title">关联阅读</div>${xs.length?`<div class="ctx-related">${xs.map(x=>`<a href="${new URL(x.path,siteRoot).href}"><strong>${esc(x.title)}</strong><span>${esc(x.date||'')} · ${esc(x.category||'')}</span></a>`).join('')}</div>`:'<p class="ctx-empty">暂无高度相关的历史内容。</p>'}`}
function renderTimeline(panel,info,all){const xs=relatedRecords(info,all,12).sort((a,b)=>String(b.date).localeCompare(String(a.date))).slice(0,8);panel.innerHTML=`<div class="ctx-panel-title">专题脉络</div><div class="ctx-topic-row">${info.tags.map(t=>`<span>${esc(t)}</span>`).join('')}</div>${xs.length?`<div class="ctx-timeline">${xs.map(x=>`<a href="${new URL(x.path,siteRoot).href}"><time>${esc(x.date||'')}</time><span>${esc(x.title)}</span></a>`).join('')}</div>`:'<p class="ctx-empty">当前主题尚未形成足够的历史脉络。</p>'}`}
function renderCitation(panel,info){panel.innerHTML=`<div class="ctx-panel-title">引用与导出</div><div class="ctx-cite-tabs"><button data-fmt="gb">GB/T 7714</button><button data-fmt="law">《法学引注手册》</button><button data-fmt="bluebook">Bluebook</button><button data-fmt="bibtex">BibTeX</button><button data-fmt="ris">RIS</button></div><pre class="ctx-citation"></pre><button class="ctx-copy">复制当前格式</button>`;const out=panel.querySelector('.ctx-citation'),tabs=[...panel.querySelectorAll('[data-fmt]')];let fmt='gb';const show=()=>{out.textContent=citation(info,fmt);tabs.forEach(b=>b.classList.toggle('active',b.dataset.fmt===fmt))};tabs.forEach(b=>b.onclick=()=>{fmt=b.dataset.fmt;show()});panel.querySelector('.ctx-copy').onclick=()=>copyText(citation(info,fmt),'引用已复制');show()}
function makeActions(target,idx,all,articleLevel=false){if(target.querySelector(':scope > .ctx-actions'))return;target.id=target.id||`research-item-${idx+1}`;const info=itemInfo(target,idx);const wrap=document.createElement('div');wrap.className='ctx-actions';wrap.innerHTML=`<button data-act="read">${isRead(info)?'✓ 稍后读':'稍后读'}</button><button data-act="related">关联阅读</button><button data-act="timeline">专题脉络</button><button data-act="cite">引用</button>`;const panel=document.createElement('div');panel.className='ctx-inline-panel';wrap.appendChild(panel);const read=wrap.querySelector('[data-act="read"]');read.onclick=()=>toggleRead(info,read);wrap.querySelector('[data-act="related"]').onclick=()=>{const open=panel.dataset.mode==='related'&&panel.classList.contains('show');panel.dataset.mode='related';if(open){panel.classList.remove('show');return}renderRelated(panel,info,all);panel.classList.add('show')};wrap.querySelector('[data-act="timeline"]').onclick=()=>{const open=panel.dataset.mode==='timeline'&&panel.classList.contains('show');panel.dataset.mode='timeline';if(open){panel.classList.remove('show');return}renderTimeline(panel,info,all);panel.classList.add('show')};wrap.querySelector('[data-act="cite"]').onclick=()=>{const open=panel.dataset.mode==='cite'&&panel.classList.contains('show');panel.dataset.mode='cite';if(open){panel.classList.remove('show');return}renderCitation(panel,info);panel.classList.add('show')};if(articleLevel){const first=target.firstElementChild;first?target.insertBefore(wrap,first):target.appendChild(wrap)}else target.appendChild(wrap)}
async function init(){const css=new URL('context-tools.css',assetBase).href;if(!document.querySelector(`link[href="${css}"]`)){const l=document.createElement('link');l.rel='stylesheet';l.href=css;document.head.appendChild(l)}const all=await index();let items=[...document.querySelectorAll('.article-body .brief-item')];if(items.length){items.forEach((x,i)=>makeActions(x,i,all,false));return}const root=document.querySelector('.article-body .article-wrap,.article-body,.article .reading,.article');if(root)makeActions(root,0,all,true)}
document.addEventListener('DOMContentLoaded',init);
})();