(()=>{
  const cfg=window.CYBERLAW_ANALYTICS||{};
  if(!cfg.enabled||!cfg.endpoint)return;
  const auth=window.CyberlawAuth;
  if(!auth||!/^researcher(?:0[1-9]|1\\d|20)$/.test(auth.user||''))return;
  const root=auth.siteRoot instanceof URL?auth.siteRoot:new URL('/cyberlaw-research/',location.origin);
  const pathname=decodeURIComponent(location.pathname);
  if(!pathname.startsWith(root.pathname))return;
  const path=pathname.slice(root.pathname.length)||'index.html';
  if(path==='login.html')return;
  const cooldown=Math.max(0,Number(cfg.cooldownMs)||300000);
  const key='cyberlawAnalyticsLast::'+auth.user+'::'+path;
  const now=Date.now();
  try{
    const last=Number(sessionStorage.getItem(key)||0);
    if(last&&now-last<cooldown)return;
    sessionStorage.setItem(key,String(now));
  }catch(_e){}
  const payload={version:Number(cfg.version)||1,user:auth.user,path,visited_at:new Date(now).toISOString()};
  try{
    fetch(String(cfg.endpoint),{
      method:'POST',
      mode:'cors',
      credentials:'omit',
      cache:'no-store',
      keepalive:true,
      headers:{'Content-Type':'application/json'},
      body:JSON.stringify(payload)
    }).catch(()=>{});
  }catch(_e){}
})();
