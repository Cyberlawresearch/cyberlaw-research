(()=>{
'use strict';
const path='/articles/2026-10-08-tech-law-brief.html';
if(!location.pathname.endsWith(path))return;
const domestic=[
 {date:'2026-10-08',title:'人社部就《新就业形态劳动者权益保障办法》公开征求意见',meta:'2026-10-08 · 中国 · 人力资源社会保障部',original:'人力资源社会保障部关于《新就业形态劳动者权益保障办法（征求意见稿）》公开征求意见的通知',fact:'人力资源社会保障部10月8日发布《新就业形态劳动者权益保障办法（征求意见稿）》，向社会公开征求意见至11月8日。这是我国首次拟以规章形式，将企业实施劳动管理、但不完全符合确立劳动关系情形的新就业形态劳动者纳入劳动法律制度保障。征求意见稿共54条，涉及基本劳动权益、劳动规则与算法、企业用工分类、纠纷解决、监管职责和法律责任；目前仍处于公开征求意见阶段，尚未生效。',url:'https://www.news.cn/politics/20261008/6e01730616fc4900b2892af1e904914e/c.html',source:'人力资源社会保障部／新华社',analysis:['征求意见稿的关键不只是增加若干权益条款，而是以部门规章形式承认传统劳动关系与完全独立承揽之间存在需要劳动法最低保障的用工类型。平台的劳动规则、算法分配、奖惩和申诉程序因此可能成为可被行政监管和争议审查的用工管理行为。','《新就业形态用工分层分类规则及平台算法合规清单》：可对照劳动关系、不完全符合劳动关系和其他合作用工三类情形，梳理报酬、工时、奖惩、算法说明、个人信息、职业伤害和争议处理的责任主体与证据要求。','《平台用工“中间类型”的劳动法定位》：研究部门规章将受劳动管理但未完全建立劳动关系的劳动者纳入保护后，最低劳动标准、合同自由、责任主体和劳动关系认定之间如何衔接。','我国此前主要通过指导意见、平台劳动规则指引、算法和劳动报酬等专项指南，以及职业伤害保障试点完善新就业形态保护。此次征求意见稿首次以规章形式系统整合基本权益、算法规则、用工分类、争议解决和监管责任。','征求意见截至11月8日。最终制度的实际影响取决于“不完全符合确立劳动关系情形”的识别标准、平台与合作企业责任分配、算法规则的可审查程度，以及行政执法与争议解决程序能否衔接。']},
 {date:'2026-10-06',title:'DeepSeek据报新一轮融资认购额超过800亿元，拟为上市和国产算力生态储备资金',meta:'2026-10-06 · 中国 · 中国人工智能产业／DeepSeek',original:'DeepSeek set to net over $12 billion in new fundraising, source says',fact:'Reuters援引知情人士称，DeepSeek本轮融资已获得超过800亿元人民币的认购承诺，最终规模可能达到1000亿元，目标估值约5000亿元；宁德时代和腾讯据报作出较大金额承诺。公司正为潜在境内上市作准备，并与华为推进面向昇腾芯片的软件工具合作。融资规模、估值和投资者安排目前尚未由DeepSeek或相关投资者正式确认。',url:'https://www.reuters.com/world/asia-pacific/deepseek-raise-least-12-billion-tencent-backed-funding-bloomberg-news-reports-2026-10-06/',source:'Reuters'},
 {date:'2026-10-08',title:'腾讯据报考虑发行至多50亿美元境外债券，用于扩大AI和计算基础设施投入',meta:'2026-10-08 · 中国 · 腾讯控股',original:'Tencent mulls $5 billion bond sale to push AI ambitions, Bloomberg News reports',fact:'Reuters转引Bloomberg报道称，腾讯正在考虑通过境外债券发行筹集至多50亿美元，以支持人工智能和计算基础设施投入。报道所述方案仍处于考虑阶段，腾讯尚未发布正式发行公告，债券币种、期限、定价、承销安排和最终募集金额均有待确定。',url:'https://www.reuters.com/world/asia-pacific/tencent-mulls-5-billion-bond-sale-push-ai-ambitions-bloomberg-news-reports-2026-10-08/',source:'Reuters'},
 {date:'2026-10-08',title:'中国加快建设AI数据中心，运营和在建容量据报合计大幅扩张',meta:'2026-10-08 · 中国 · 中国AI数据中心产业',original:'China races to build data centres in bid for AI supremacy',fact:'Financial Times 10月8日报道，中国正依托能源、土地和建设能力加快数据中心布局。报道援引SemiAnalysis数据称，中国现有数据中心计算容量约24GW，另有约50GW在建；内蒙古乌兰察布已成为重要增长区域，华为、阿里巴巴和字节跳动等企业持续投入。报道同时指出，先进芯片供给、水资源、网络安全和项目实际利用率仍是关键约束。',url:'https://www.ft.com/content/e1dd8bff-b06d-4a40-bbb7-c0a6a36f1c8e',source:'Financial Times'}
];
function direct(item,sel){return item.querySelector(':scope > '+sel)}
function replaceShell(item,d,idx){
 item.id='research-item-domestic-'+idx;
 item.dataset.eventDate=d.date;
 item.dataset.originalTitle=d.original;
 item.setAttribute('data-citation',JSON.stringify({type:'news',cnTitle:d.title,originalTitle:d.original,sourceName:d.source,date:d.date,url:d.url,foreign:false}));
 direct(item,'h3').textContent=idx+'. '+d.title;
 direct(item,'.brief-meta').textContent=d.meta;
 let o=direct(item,'.brief-original');if(!o){o=document.createElement('p');o.className='brief-original';direct(item,'.brief-fact').before(o)}o.innerHTML='<strong>原始题名：</strong>'+d.original;
 direct(item,'.brief-fact').textContent=d.fact;
 const src=direct(item,'.source');src.innerHTML='原始来源：<a></a>';const a=src.querySelector('a');a.href=d.url;a.textContent=d.source;
}
function label(item,n){const h=direct(item,'h3');h.textContent=n+'. '+h.textContent.replace(/^\s*\d+[.、]\s*/,'')}
async function apply(){
 const wrap=document.querySelector('.article-body .article-wrap');if(!wrap)return;
 const items=[...wrap.querySelectorAll(':scope > .brief-item')];if(items.length!==20)return;
 const baseShells=items.slice(17),extra=baseShells[0].cloneNode(true),shells=[...baseShells,extra],kept=items.slice(0,17),intl=[...wrap.children].find(x=>x.tagName==='H2');
 let domesticHead=[...wrap.children].find(x=>x.tagName==='H2'&&x.textContent.trim()==='国内');
 if(!domesticHead){domesticHead=document.createElement('h2');domesticHead.textContent='国内';wrap.insertBefore(domesticHead,intl)}
 shells.forEach((x,i)=>{replaceShell(x,domestic[i],i+1);wrap.insertBefore(x,intl)});
 intl.textContent='国际';kept.forEach((x,i)=>label(x,i+5));
 const final=[...shells,...kept];
 const data=Object.assign({},...await Promise.all([1,2,3,4].map(n=>fetch('../assets/oct8-a'+n+'.json?v=3').then(r=>{if(!r.ok)throw Error('analysis '+n);return r.json()}))));
 final.forEach((item,i)=>{
   const row=i===0?domestic[0].analysis:data[i];
   if(!row)return;
   const ps=[...item.children].filter(x=>x.tagName==='P'&&(x.classList.contains('analysis-pending')||x.hasAttribute('data-a'))).slice(0,3);
   const labels=['法治研判：','智库选题参考：','论文选题：'];
   ps.forEach((p,j)=>{p.classList.remove('analysis-pending');p.removeAttribute('style');p.innerHTML='';const b=document.createElement('strong');b.textContent=labels[j];p.append(b,document.createTextNode(row[j]))});
   let s=direct(item,'script.brief-insight');if(!s){s=document.createElement('script');s.type='application/json';s.className='brief-insight';direct(item,'.source').before(s)}s.textContent=JSON.stringify({background:row[3],outlook:row[4]});
 });
 const lead=document.querySelector('.article-hero .lead');if(lead)lead.textContent='2026年10月8日 · 21条';
 document.body.dataset.analysisStatus='completed';
 document.dispatchEvent(new CustomEvent('oct8-news-corrected'));
}
if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',()=>apply().catch(console.error),{once:true});else apply().catch(console.error);
})();
