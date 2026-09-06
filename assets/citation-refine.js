(()=>{
const script=document.currentScript;
const assetBase=script?new URL('.',script.src):new URL('assets/',location.href);
const esc=s=>String(s??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const today=()=>new Date().toISOString().slice(0,10);
const cnDate=d=>{const m=String(d||'').match(/(20\d{2})[-./年](\d{1,2})[-./月](\d{1,2})/);return m?`${m[1]}年${+m[2]}月${+m[3]}日`:d||''};
const cleanText=s=>String(s||'').replace(/\s+/g,' ').trim();
const pageTitle=()=>document.querySelector('main h1')?.textContent.trim()||document.title.replace(/｜.*$/,'').trim();
const pageLead=()=>cleanText(document.querySelector('.article-hero .lead')?.textContent||'');
const targetFor=btn=>btn.closest('.ctx-actions')?.parentElement;
const targetTitle=t=>(t?.querySelector('h3,h2')?.textContent||pageTitle()).replace(/^\s*\d+[.、]\s*/,'').trim();
const targetMeta=t=>cleanText(t?.querySelector('.brief-meta')?.textContent||pageLead());
const sourceLink=t=>t?.querySelector('.source a')||document.querySelector('.article-body .source a');
const dateFrom=s=>{const m=String(s||'').match(/(?:(20\d{2})年)?(\d{1,2})月(\d{1,2})日/);if(m){const y=m[1]||String(new Date().getFullYear());return `${y}-${String(+m[2]).padStart(2,'0')}-${String(+m[3]).padStart(2,'0')}`}const y=String(s||'').match(/\b(19|20)\d{2}\b/);return y?y[0]:''};
const doiFrom=u=>{const m=decodeURIComponent(u||'').match(/10\.\d{4,9}\/[A-Za-z0-9._;()/:+-]+/);return m?m[0].replace(/[).,;]+$/,''):''};
const quoteTitle=s=>{const m=String(s||'').match(/[“"]([^”"]+)[”"]/);return m?m[1].trim():''};
const field=(s,re)=>{const m=String(s||'').match(re);return m?m[1].trim():''};
function materialType(){const dt=document.title;if(dt.includes('全球科技法简报'))return'news';if(dt.includes('科技法研究新作'))return'newwork';if(dt.includes('经典'))return'book';if(dt.includes('论文'))return'article';return'web'}
function parseArticleMeta(meta,src){
 const originalTitle=quoteTitle(meta),author=originalTitle?cleanText(meta.split(/[·,]/)[0]):'',year=field(meta,/\b((?:19|20)\d{2})\b/),volume=field(meta,/Vol\.?\s*([0-9A-Za-z.-]+)/i),issue=field(meta,/(?:No\.?|Issue)\s*([0-9A-Za-z.-]+)/i),pages=field(meta,/pp?\.?\s*([0-9]+(?:\s*[–—-]\s*[0-9]+)?)/i),articleNo=field(meta,/Article\s+([0-9A-Za-z.-]+)/i),doi=doiFrom(src?.href||'');
 let journal='';
 if(originalTitle){let rest=meta.slice(meta.indexOf(originalTitle)+originalTitle.length).replace(/^[”"\s,·]+/,'');rest=rest.split(/\s+·\s+/)[0];journal=cleanText(rest.replace(/,?\s*Vol\..*$/i,'').replace(/,?\s*(?:19|20)\d{2}.*$/,'')).replace(/^<|>$/g,'')}
 return{type:'article',author,originalTitle,journal,year,volume,issue,pages,articleNo,doi,url:src?.href||''};
}
function parseBook(){
 const lead=pageLead(),m=lead.match(/^([^,]+),\s*(.+)$/),author=m?m[1].trim():'',originalTitle=m?m[2].trim():pageTitle();const body=cleanText(document.querySelector('.article-body')?.innerText||'');
 let year='',publisher='';const rev=body.match(/(?:修订版|新版)[^。；]{0,25}?(\d{4})年由([^。；]{2,90}?)出版/i),pub=body.match(/(\d{4})年由([^。；]{2,90}?)出版/i),first=body.match(/初版于(\d{4})年/);
 if(rev){year=rev[1];publisher=rev[2].trim()}else if(pub){year=pub[1];publisher=pub[2].trim()}else if(first)year=first[1];
 publisher=publisher.replace(/^(?:the\s+)?/i,'').trim();return{type:'book',author,originalTitle,publisher,year,url:sourceLink(document.body)?.href||''};
}
function infoFor(target){
 const type=materialType(),src=sourceLink(target),meta=targetMeta(target),cnTitle=targetTitle(target),access=today();
 if(type==='book')return{...parseBook(),cnTitle,access};
 if(type==='article'){const x=parseArticleMeta(pageLead(),src);return{...x,cnTitle,access};}
 if(type==='newwork'){const x=parseArticleMeta(meta,src);const looksArticle=!!(x.journal||x.volume||x.issue||x.pages||x.articleNo||x.doi);if(looksArticle)return{...x,cnTitle,access};const parts=meta.split(/\s+·\s+/).map(cleanText).filter(Boolean),publisher=parts.slice(2).find(p=>/Press|出版社|Publishing|University/i.test(p))||'',year=x.year;return{type:'book',author:parts[0]||x.author,originalTitle:x.originalTitle||cnTitle,publisher,year,url:src?.href||'',cnTitle,access};}
 if(type==='news'){
  const originalTitle=target?.dataset.originalTitle||src?.dataset.originalTitle||src?.getAttribute('title')||'';const sourceName=cleanText(src?.textContent||'');const date=dateFrom(meta);const foreign=!/中国|北京|上海|深圳|福建|内蒙古|国家|国务院|最高人民|市场监管|网信|工信|数据局/.test(meta);
  return{type:'news',cnTitle,originalTitle:cleanText(originalTitle)||cnTitle,sourceName,date,url:src?.href||location.href,foreign,access};
 }
 return{type:'web',cnTitle,originalTitle:cnTitle,sourceName:'网信法研究每日推送',date:dateFrom(meta),url:location.href,access};
}
const pagesStart=p=>String(p||'').split(/[–—-]/)[0].trim();
function gb(i){if(i.type==='article')return`${i.author||''}. ${i.originalTitle||i.cnTitle}[J]. ${i.journal||''}${i.year?`, ${i.year}`:''}${i.volume?`, ${i.volume}`:''}${i.issue?`(${i.issue})`:''}${i.pages?`: ${i.pages}`:''}.${i.doi?` DOI:${i.doi}.`:i.url?` ${i.url}.`:''}`.replace(/\.\s*\./g,'.');if(i.type==='book')return`${i.author||''}. ${i.originalTitle||i.cnTitle}[M]. ${i.publisher||''}${i.year?`, ${i.year}`:''}.${i.url?` ${i.url}.`:''}`.replace(/\.\s*\./g,'.');return`${i.sourceName||''}. ${i.originalTitle||i.cnTitle}[EB/OL]. ${i.date?`(${i.date})`:''}[${i.access}]. ${i.url}.`;}
function law(i){if(i.type==='article')return`${i.author||''}, “${i.originalTitle||i.cnTitle},” ${i.journal||''}${i.volume?`, Vol. ${i.volume}`:''}${i.issue?`, No. ${i.issue}`:''}${i.year?` (${i.year})`:''}${i.pages?`, pp. ${i.pages}`:''}${i.doi?`, DOI: ${i.doi}`:''}.`;if(i.type==='book')return`${i.author||''}, ${i.originalTitle||i.cnTitle}, ${i.publisher||''}${i.year?`, ${i.year}`:''}.`;if(i.foreign)return`${i.sourceName||''}, “${i.originalTitle||i.cnTitle},” ${i.date||''}, ${i.url}.`;return`${i.sourceName||''}：《${i.originalTitle||i.cnTitle}》，${i.date?cnDate(i.date):''}，${i.url}。`;}
function bluebook(i){if(i.type==='article')return`${i.author||''}, ${i.originalTitle||i.cnTitle}, ${i.volume||''} ${i.journal||''} ${pagesStart(i.pages)||i.articleNo||''} (${i.year||''})${i.doi?`, https://doi.org/${i.doi}`:i.url?`, ${i.url}`:''}.`.replace(/\s+/g,' ').replace(' ,',',');if(i.type==='book')return`${i.author||''}, ${i.originalTitle||i.cnTitle}${i.publisher||i.year?` (${[i.publisher,i.year].filter(Boolean).join(' ')})`:''}.`;return`${i.sourceName||''}, ${i.originalTitle||i.cnTitle}${i.date?` (${i.date})`:''}, ${i.url}.`;}
function bibtex(i){const key=`cyberlaw${String(i.year||i.date||i.access).replace(/\D/g,'')}`;if(i.type==='article')return`@article{${key},\n  author={${i.author||''}},\n  title={${i.originalTitle||i.cnTitle}},\n  journal={${i.journal||''}},\n  year={${i.year||''}},\n  volume={${i.volume||''}},\n  number={${i.issue||''}},\n  pages={${i.pages||''}},\n  doi={${i.doi||''}},\n  url={${i.url||''}}\n}`;if(i.type==='book')return`@book{${key},\n  author={${i.author||''}},\n  title={${i.originalTitle||i.cnTitle}},\n  publisher={${i.publisher||''}},\n  year={${i.year||''}},\n  url={${i.url||''}}\n}`;return`@online{${key},\n  author={${i.sourceName||''}},\n  title={${i.originalTitle||i.cnTitle}},\n  date={${i.date||''}},\n  url={${i.url||''}},\n  urldate={${i.access}}\n}`;}
function ris(i){if(i.type==='article')return`TY  - JOUR\nTI  - ${i.originalTitle||i.cnTitle}\nAU  - ${i.author||''}\nJO  - ${i.journal||''}\nVL  - ${i.volume||''}\nIS  - ${i.issue||''}\nSP  - ${pagesStart(i.pages)}\nPY  - ${i.year||''}\nDO  - ${i.doi||''}\nUR  - ${i.url||''}\nER  -`;if(i.type==='book')return`TY  - BOOK\nTI  - ${i.originalTitle||i.cnTitle}\nAU  - ${i.author||''}\nPB  - ${i.publisher||''}\nPY  - ${i.year||''}\nUR  - ${i.url||''}\nER  -`;return`TY  - ELEC\nTI  - ${i.originalTitle||i.cnTitle}\nAU  - ${i.sourceName||''}\nPY  - ${(i.date||'').slice(0,4)}\nUR  - ${i.url||''}\nY2  - ${i.access}\nER  -`;}
const fmt=(i,f)=>f==='law'?law(i):f==='bluebook'?bluebook(i):f==='bibtex'?bibtex(i):f==='ris'?ris(i):gb(i);
async function copy(s){try{await navigator.clipboard.writeText(s);document.dispatchEvent(new CustomEvent('citation-copied'))}catch{}}
function render(panel,target){const i=infoFor(target);panel.innerHTML=`<div class="ctx-panel-title">引用与导出</div><div class="ctx-cite-tabs"><button data-fmt="gb">GB/T 7714—2025</button><button data-fmt="law">《法学引注手册》第二版</button><button data-fmt="bluebook">Bluebook</button><button data-fmt="bibtex">BibTeX</button><button data-fmt="ris">RIS</button></div><pre class="ctx-citation"></pre><button class="ctx-copy">复制当前格式</button>`;let f='gb';const out=panel.querySelector('.ctx-citation'),tabs=[...panel.querySelectorAll('[data-fmt]')],show=()=>{out.textContent=fmt(i,f);tabs.forEach(b=>b.classList.toggle('active',b.dataset.fmt===f))};tabs.forEach(b=>b.onclick=()=>{f=b.dataset.fmt;show()});panel.querySelector('.ctx-copy').onclick=()=>copy(fmt(i,f));show();}
document.addEventListener('click',e=>{const btn=e.target.closest('.ctx-actions [data-act="cite"]');if(!btn)return;e.preventDefault();e.stopImmediatePropagation();const panel=btn.closest('.ctx-actions')?.querySelector('.ctx-inline-panel'),target=targetFor(btn);if(!panel)return;if(panel.dataset.citeRefined==='1'&&panel.classList.contains('show')){panel.classList.remove('show');return}panel.dataset.citeRefined='1';render(panel,target);panel.classList.add('show')},true);
})();