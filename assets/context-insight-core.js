/* Optional background and outlook panel for news items. */
(function(){
  'use strict';
  const script=document.currentScript;
  const assetBase=script?new URL('.',script.src):new URL('assets/',location.href);
  const siteRoot=new URL('../',assetBase);
  const esc=s=>String(s==null?'':s).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  const pagePath=()=>decodeURIComponent(location.pathname).slice(siteRoot.pathname.length);
  let pendingIndex;
  function getIndex(){
    if(!pendingIndex) pendingIndex=fetch(new URL('context-index.json?v=insight-1',assetBase))
      .then(r=>{if(!r.ok)throw new Error('context-index');return r.json()})
      .then(rows=>Array.isArray(rows)?rows:[])
      .catch(e=>{pendingIndex=null;throw e});
    return pendingIndex;
  }
  function href(row){
    try{
      const url=new URL(row.path,siteRoot);
      if(url.origin!==siteRoot.origin||!url.pathname.startsWith(siteRoot.pathname))return'';
      if(row.anchor)url.hash=row.anchor;
      return url.href;
    }catch{return''}
  }
  function structured(item){
    const node=item.querySelector(':scope > script.brief-insight[type="application/json"]');
    if(!node)return null;
    try{
      const data=JSON.parse(node.textContent||'{}');
      return {background:String(data.background||'').trim(),outlook:String(data.outlook||'').trim()};
    }catch{return null}
  }
  function lawAnalysis(item){
    const node=[...item.children].find(n=>n.tagName==='P'&&/^\s*法治研判[：:]/.test(n.textContent||''));
    return node?node.textContent.replace(/^\s*法治研判[：:]\s*/,'').trim():'';
  }
  function currentRow(item,rows){
    return rows.find(x=>x.path===pagePath()&&x.anchor===item.id)||null;
  }
  function priorRows(current,rows){
    if(!current)return[];
    const own=new Set(current.topics||[]);
    return rows.filter(x=>x.kind==='news'&&x.path&&x.anchor&&x.id!==current.id&&String(x.date||'')<=String(current.date||'')&&(x.topics||[]).some(t=>own.has(t)))
      .map(x=>({x,shared:(x.topics||[]).filter(t=>own.has(t)).length}))
      .sort((a,b)=>b.shared-a.shared||String(b.x.date).localeCompare(String(a.x.date)))
      .slice(0,3).map(x=>x.x);
  }
  function panelHtml(item,rows){
    const data=structured(item)||{background:'',outlook:''};
    const current=currentRow(item,rows);
    const prior=priorRows(current,rows);
    const topics=(current?.topics||[]).slice(0,2);
    let background=data.background;
    let links='';
    if(!background){
      if(topics.length) background=`这条新闻处在“${topics.join('、')}”相关制度与治理议题的持续演进中。以下站内前序材料可用于理解其直接背景。`;
      else if(prior.length) background='以下站内前序材料可用于理解这条新闻出现的制度或事实背景。';
      else background='当前站内没有足够直接的前序材料，背景判断应以本条已核验的原始来源和事实摘要为起点。';
      if(prior.length) links=`<ul class="ctx-insight-links">${prior.map(x=>`<li><a href="${esc(href(x))}">${esc(x.title)}</a>${x.date?` <small>${esc(x.date)}</small>`:''}</li>`).join('')}</ul>`;
    }
    let outlook=data.outlook||lawAnalysis(item);
    if(!outlook) outlook='现有信息不足以形成可靠的影响判断。后续应观察是否出现新的正式规则、裁判、执法措施、企业合规调整或关键事实变化。';
    return `<div class="ctx-panel-title">背景信息与未来前瞻</div><div class="ctx-insight-grid"><section class="ctx-insight-block"><h4>背景信息</h4><p>${esc(background)}</p>${links}</section><section class="ctx-insight-block"><h4>未来前瞻</h4><p>${esc(outlook)}</p></section></div>`;
  }
  function install(){
    if(!(document.body?.dataset.materialType==='news'||document.title.includes('全球科技法简报')))return;
    document.querySelectorAll('.brief-item').forEach(item=>{
      const actions=item.querySelector(':scope > .ctx-actions');
      if(!actions||actions.querySelector('[data-act="background"]'))return;
      const button=document.createElement('button');
      button.type='button';button.dataset.act='background';button.textContent='背景与前瞻';button.setAttribute('aria-expanded','false');
      const timeline=actions.querySelector('[data-act="timeline"]');
      timeline?.after(button)||actions.appendChild(button);
    });
  }
  const css=document.createElement('link');css.rel='stylesheet';css.href=new URL('context-insight.css?v=1',assetBase).href;document.head.appendChild(css);
  install();
  document.addEventListener('DOMContentLoaded',install,{once:true});
  const observer=new MutationObserver(()=>install());
  if(document.documentElement)observer.observe(document.documentElement,{childList:true,subtree:true});
  document.addEventListener('click',async event=>{
    const btn=event.target.closest?.('.ctx-actions [data-act="background"]');
    if(!btn)return;
    event.preventDefault();event.stopImmediatePropagation();
    const actions=btn.closest('.ctx-actions'),item=actions?.closest('.brief-item'),panel=actions?.querySelector('.ctx-inline-panel');
    if(!item||!panel)return;
    if(panel.dataset.contextMode==='background'&&panel.classList.contains('show')){
      panel.classList.remove('show');btn.setAttribute('aria-expanded','false');delete panel.dataset.contextMode;return;
    }
    actions.querySelectorAll('[data-act]').forEach(b=>b.setAttribute('aria-expanded',String(b===btn)));
    panel.dataset.contextMode='background';panel.innerHTML='<p class="ctx-empty" role="status">正在加载…</p>';panel.classList.add('show');
    try{panel.innerHTML=panelHtml(item,await getIndex())}
    catch{panel.innerHTML=panelHtml(item,[])}
  },true);
})();
