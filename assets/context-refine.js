(()=>{
const script=document.currentScript;
const assetBase=script?new URL('.',script.src):new URL('assets/',location.href);
const siteRoot=new URL('../',assetBase);
const esc=s=>String(s??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const norm=s=>(s||'').toLowerCase().replace(/[\s\p{P}\p{S}]+/gu,'');
const TOPICS={
'智能体AI':['智能体','agentic','ai agent','自主代理'],
'生成式AI与大模型':['生成式ai','生成式人工智能','generative ai','大模型','基础模型','foundation model'],
'AI安全与前沿能力':['ai安全','模型安全','前沿模型','前沿能力','红队','事故披露'],
'AI风险分级与持续监管':['风险分级','动态监管','持续评估','监管沙盒','risk-based'],
'AI行政应用':['政府大模型','公共部门ai','行政自动化','自动化行政','ai政务'],
'算法歧视与公平':['算法歧视','algorithmic discrimination','招聘算法','算法公平'],
'自动化决策与正当程序':['自动化决策','automated decision','due process','正当程序'],
'机器遗忘与删除权':['机器遗忘','machine unlearning','删除权','被遗忘权'],
'AI职业伦理与专业责任':['职业伦理','法律职业','律师','专业注意义务','认识论责任'],
'AI与民主法治':['民主','公共理由','民主认识论','公共讨论'],
'数据要素与公共数据':['数据要素','公共数据','数据交易','授权运营'],
'数据跨境':['数据跨境','跨境数据','cross-border data','数据出境'],
'个人信息与隐私保护':['个人信息','隐私','gdpr','data protection','pipl'],
'生物识别':['生物识别','人脸识别','biometric','facial recognition'],
'儿童与未成年人数据':['儿童','未成年人','children','minor'],
'平台责任与内容治理':['平台责任','内容治理','推荐算法','平台治理','social media'],
'反垄断与市场力量':['反垄断','antitrust','市场支配','competition authority'],
'平台竞争与自我优待':['平台竞争','二选一','自我优待','self-preferencing','应用商店'],
'AI训练与版权':['ai训练','训练数据','fair use','合理使用','训练版权'],
'知识产权与技术竞争':['知识产权','版权','著作权','copyright','patent'],
'网络安全事件与漏洞':['网络安全','cybersecurity','漏洞','入侵','勒索'],
'关键基础设施安全':['关键基础设施','critical infrastructure','基础设施安全','反破坏'],
'后量子密码':['后量子','post-quantum','pqc'],
'芯片与出口管制':['芯片','半导体','出口管制','export control','gpu'],
'算力与数据中心':['算力','数据中心','compute','词元','算力网'],
'深度伪造与合成内容':['深度伪造','deepfake','合成内容','数字水印'],
'选举与AI':['选举','election','投票','选民'],
'自主武器':['自主武器','autonomous weapon','致命自主武器'],
'国家安全与军事AI':['国家安全','national security','军事','国防'],
'国际AI治理':['ai治理','人工智能治理','ai act','ai office','全球ai治理'],
'AI产品责任':['产品责任','product liability','缺陷产品','损害赔偿'],
'司法AI':['司法人工智能','智能法院','辅助裁判','judicial ai','adjudication'],
'预测性执法':['预测性执法','predictive policing','预测性司法','再犯风险'],
'AI审计':['ai审计','算法审计','algorithm audit','fairness audit'],
'数据访问与Data Act':['data act','数据访问权','联网产品','身份认证','授权访问']
};
const topicNames=text=>{const low=(text||'').toLowerCase();return Object.entries(TOPICS).filter(([,ws])=>ws.some(w=>low.includes(w))).map(([t])=>t)};
const fetchJson=async n=>{try{return await fetch(new URL(n,assetBase)).then(r=>r.json())}catch{return[]}};
let indexes;
const getIndexes=()=>indexes||(indexes=Promise.all([fetchJson('news-index.json'),fetchJson('newworks-index.json')]).then(([news,works])=>({news,works})));
const targetFor=btn=>btn.closest('.ctx-actions')?.parentElement;
const titleFor=target=>(target?.querySelector('h3,h2')?.textContent||document.querySelector('main h1')?.textContent||document.title).replace(/^\s*\d+[.、]\s*/,'').trim();
const textFor=target=>`${titleFor(target)} ${target?.innerText||''}`;
function topThemes(target,items){
  const own=topicNames(textFor(target));
  if(!own.length)return[];
  const counts=new Map(own.map(t=>[t,0]));
  for(const x of items)for(const t of x.topics||[])if(counts.has(t))counts.set(t,counts.get(t)+1);
  return [...counts.entries()].filter(([,n])=>n>0).sort((a,b)=>b[1]-a[1]||a[0].localeCompare(b[0])).slice(0,3).map(([t])=>t);
}
function themeRow(label,themes){
  return `<section class="ctx-theme-block"><h4>${label}</h4>${themes.length?`<div class="ctx-topic-row">${themes.map(t=>`<span>${esc(t)}</span>`).join('')}</div>`:'<p class="ctx-empty">暂无明显相关主题。</p>'}</section>`;
}
function renderRelated(panel,target,news,works){
  const nt=topThemes(target,news),wt=topThemes(target,works);
  panel.innerHTML=`<div class="ctx-panel-title">关联阅读</div>${themeRow('相关新闻主题',nt)}${themeRow('相关研究新作主题',wt)}`;
}
const grams=s=>{const x=norm(s),a=new Set();for(let i=0;i<x.length-1;i++)a.add(x.slice(i,i+2));return a};
const sim=(a,b)=>{const A=grams(a),B=grams(b);if(!A.size||!B.size)return 0;let hit=0;for(const x of A)if(B.has(x))hit++;return hit/Math.max(1,Math.min(A.size,B.size))};
const GENERIC=new Set(['人工智能','生成式ai','生成式人工智能','数据','平台','网络安全','科技','监管','政策','规则','中国','美国','欧盟','委员会','法院','政府','部门','公司','模型','系统','计划']);
function anchors(text){
  const src=text||'',out=[],seen=new Set();
  const push=(v,w)=>{v=(v||'').trim().replace(/^《|》$|^“|”$/g,'');const k=norm(v);if(k.length<3||GENERIC.has(k)||seen.has(k))return;seen.add(k);out.push({v,k,w})};
  for(const m of src.matchAll(/《([^》]{3,40})》/g))push(m[1],4);
  for(const m of src.matchAll(/“([^”]{3,30})”/g))push(m[1],3);
  for(const m of src.matchAll(/\b(?:OpenAI|Microsoft|Google|Meta|Tesla|NVIDIA|TikTok|ByteDance|Amazon|Apple|Anthropic|DeepMind|CNIL|FTC|DOJ|SEC|NHTSA|CISA|FCC|ICO|CMA|Ofcom|PIPC|KFTC|PPC|JFTC|GDPR|DSA|DMA|SAVE|ChatGPT|Cybercab)\b/gi))push(m[0],3);
  for(const m of src.matchAll(/\b[A-Z][A-Z0-9.-]{2,12}\b/g))push(m[0],2);
  for(const m of src.matchAll(/[\u4e00-\u9fffA-Za-z0-9·]{2,22}(?:委员会|管理局|法院|检察院|公司|平台|数据库|法案|条例|办法|指令|协议|模型|系统|产品)/g))push(m[0],2);
  return out.slice(0,24);
}
function sharedAnchors(cur,cand){
  const ca=anchors(cur),xa=anchors(cand),shared=[];
  for(const a of ca)for(const b of xa){if(a.k===b.k||(a.k.length>=5&&b.k.includes(a.k))||(b.k.length>=5&&a.k.includes(b.k))){shared.push({v:a.v,w:Math.max(a.w,b.w)});break}}
  return shared;
}
function isDirect(target,x){
  const currentTitle=titleFor(target),current=`${currentTitle} ${target?.querySelector('.brief-meta')?.textContent||''}`;
  const candidate=`${x.title||''} ${x.meta||''} ${(x.keywords||[]).join(' ')}`;
  const shared=sharedAnchors(current,candidate),strong=shared.filter(a=>a.w>=3),medium=shared.filter(a=>a.w>=2);
  const ts=sim(currentTitle,x.title||'');
  if(strong.some(a=>a.w>=4))return 100+ts*10;
  if(strong.length>=2)return 90+ts*10;
  if(strong.length===1&&medium.length>=2&&ts>=.22)return 80+ts*10;
  if(strong.length===1&&ts>=.34)return 70+ts*10;
  if(medium.length>=2&&ts>=.38)return 60+ts*10;
  return -1;
}
function strictTimeline(target,news){
  if(!target?.matches('.brief-item')&&!target?.closest('.brief-item'))return[];
  const currentId=target.id||'';
  const ranked=[];
  for(const x of news){
    if(currentId&&x.anchor===currentId&&location.pathname.endsWith('/'+x.path))continue;
    const score=isDirect(target,x);if(score<0)continue;ranked.push([x,score]);
  }
  ranked.sort((a,b)=>b[1]-a[1]||String(a[0].date).localeCompare(String(b[0].date)));
  const out=[];
  for(const [x] of ranked){if(out.some(y=>y.date===x.date&&sim(y.title,x.title)>.72))continue;out.push(x);if(out.length>=4)break}
  return out.sort((a,b)=>String(a.date).localeCompare(String(b.date)));
}
function renderTimeline(panel,target,news){
  const xs=strictTimeline(target,news);
  panel.innerHTML=`<div class="ctx-panel-title">专题时间线</div>${xs.length?`<div class="ctx-timeline">${xs.map(x=>`<a href="${new URL(x.path,siteRoot).href}#${encodeURIComponent(x.anchor||'')}"><time>${esc(x.date||'')}</time><span><strong>${esc(x.title||'')}</strong>${x.meta?`<small>${esc(x.meta)}</small>`:''}</span></a>`).join('')}</div>`:'<p class="ctx-empty">暂未找到与当前事项存在直接延续关系的历史节点。</p>'}`;
}
function openPanel(btn,mode,render){
  const actions=btn.closest('.ctx-actions'),panel=actions?.querySelector('.ctx-inline-panel');if(!panel)return;
  if(panel.dataset.refineMode===mode&&panel.classList.contains('show')){panel.classList.remove('show');return}
  panel.dataset.refineMode=mode;render(panel);panel.classList.add('show');
}
document.addEventListener('click',async e=>{
  const btn=e.target.closest('.ctx-actions [data-act="related"],.ctx-actions [data-act="timeline"]');if(!btn)return;
  e.preventDefault();e.stopImmediatePropagation();
  const target=targetFor(btn);const {news,works}=await getIndexes();
  if(btn.dataset.act==='related')openPanel(btn,'related-refined',p=>renderRelated(p,target,news,works));
  else openPanel(btn,'timeline-refined',p=>renderTimeline(p,target,news));
},true);
})();