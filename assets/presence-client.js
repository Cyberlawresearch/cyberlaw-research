/* Online presence only. No page URL, visitor fingerprint or legacy password is transmitted. */
(()=>{
  'use strict';
  const endpoint='https://btgmuyuhmjzgxmpkglah.supabase.co/functions/v1/site-presence';
  const publishable='sb_publishable_7t_PVlGt7Kbv4HH7S__TZQ_otacb3-H';
  const storageKey='technologyLawPresenceSessionV1',pingKey='technologyLawPresenceLastAttemptV1';
  const validAccount=a=>/^researcher(0[1-9]|1[0-9]|20)$/.test(a||'');
  const validKey=k=>/^[0-9a-f]{64}$/.test(k||'');
  const $=id=>document.getElementById(id);
  const current=()=>{try{const s=JSON.parse(sessionStorage.getItem(storageKey)||'null');return s&&validAccount(s.account)&&validKey(s.key)?s:null}catch{return null}};
  function forget(){try{sessionStorage.removeItem(storageKey);sessionStorage.removeItem(pingKey)}catch{}}
  function setSession(account,key){sessionStorage.setItem(storageKey,JSON.stringify({account,key}));sessionStorage.setItem(pingKey,String(Date.now()))}
  async function call(action,key,account=''){
    const abort=new AbortController(),timer=setTimeout(()=>abort.abort(),8000);
    try{
      const r=await fetch(endpoint,{method:'POST',mode:'cors',credentials:'omit',cache:'no-store',signal:abort.signal,headers:{'Content-Type':'application/json','apikey':publishable},body:JSON.stringify({action,key,account})});
      const data=await r.json();
      if(!r.ok||!data?.ok)throw new Error(data?.error==='unauthorized'?'unauthorized':data?.error==='forbidden'?'forbidden':'unavailable');
      return data;
    }finally{clearTimeout(timer)}
  }
  async function verify(account,key){
    if(!validAccount(account)||!validKey(key))throw new Error('unauthorized');
    const data=await call('verify',key,account);
    if(data.account!==account||data.admin!==(account==='researcher02'))throw new Error('unauthorized');
    setSession(account,key);
    return data;
  }
  window.CyberlawPresence={verify,forget};
  document.addEventListener('click',e=>{if(e.target.closest('.account-logout,#account-signout'))forget()},true);
  let activeAt=Date.now(),heartbeatBusy=false;
  async function heartbeat(){
    const s=current(),u=window.CyberlawAuth?.user;
    if(!s||s.account!==u||document.visibilityState!=='visible'||Date.now()-activeAt>60000||heartbeatBusy)return;
    let last=0;try{last=Number(sessionStorage.getItem(pingKey)||0)}catch{}
    if(Date.now()-last<60000)return;
    heartbeatBusy=true;try{sessionStorage.setItem(pingKey,String(Date.now()));await call('heartbeat',s.key,s.account)}
    catch(e){if(e?.message==='unauthorized'){forget();document.dispatchEvent(new Event('presence-revoked'))}}
    finally{heartbeatBusy=false}
  }
  function markActive(){if(document.visibilityState==='visible'){activeAt=Date.now();void heartbeat()}}
  function adminPanel(){
    const panel=$('presence-admin'),auth=window.CyberlawAuth;
    if(!panel||auth?.user!=='researcher02')return;
    panel.hidden=false;
    const form=$('presence-verify-form'),status=$('presence-status'),dashboard=$('presence-dashboard'),list=$('presence-online-list'),count=$('presence-count'),refreshButton=$('presence-refresh'),issueForm=$('presence-issue-form'),select=$('presence-issue-account'),issued=$('presence-issued'),issueStatus=$('presence-issue-status'),issuedKey=$('presence-issued-key');
    let refreshing=false,verified=false,issuing=false;
    const clearList=()=>{list.replaceChildren();count.textContent='—'};
    function reset(msg='尚未验证后台身份。'){verified=false;dashboard.hidden=true;form.hidden=false;clearList();issued.hidden=true;issuedKey.value='';issueStatus.textContent='';status.textContent=msg}
    function render(rows){
      list.replaceChildren();
      const users=Array.isArray(rows)?rows.filter(r=>validAccount(r.account)&&Number.isFinite(Date.parse(r.last_seen))):[];
      count.textContent=String(users.length);
      if(!users.length){const p=document.createElement('p');p.className='presence-empty';p.textContent='当前没有已验证的在线账号。';list.append(p);return}
      users.forEach(r=>{
        const row=document.createElement('div');row.className='presence-row';
        const name=document.createElement('span');name.className='presence-account';name.textContent=r.account;
        const time=document.createElement('time');time.dateTime=r.last_seen;
        time.textContent=new Date(r.last_seen).toLocaleString('zh-CN',{timeZone:'Asia/Shanghai',hour:'2-digit',minute:'2-digit',second:'2-digit',hour12:false});
        time.title=new Date(r.last_seen).toLocaleString('zh-CN',{timeZone:'Asia/Shanghai',hour12:false})+'（北京时间）';row.append(name,time);list.append(row);
      });
    }
    async function refresh(){
      const s=current();if(!s||s.account!=='researcher02'||refreshing)return;
      refreshing=true;refreshButton.disabled=true;
      try{
        const data=await call('online',s.key);
        const live=current();if(!live||live.key!==s.key)return;
        verified=true;form.hidden=true;dashboard.hidden=false;render(data.online);
        status.textContent='已验证管理员身份 · 最近活跃时间（北京时间）';
      }catch(e){
        if(e?.message==='unauthorized'||e?.message==='forbidden'){forget();reset('后台身份已失效，请重新验证。')}
        else{clearList();status.textContent='在线名单暂时无法获取，请重试。';if(!verified)reset('在线服务暂时不可用，请重新验证。')}
      }finally{refreshing=false;refreshButton.disabled=false}
    }
    for(let i=1;i<=20;i++){if(i===2)continue;const option=document.createElement('option');option.value=option.textContent='researcher'+String(i).padStart(2,'0');select.append(option)}
    form.addEventListener('submit',async e=>{
      e.preventDefault();const key=$('presence-verify-key').value.trim(),button=form.querySelector('button');button.disabled=true;status.textContent='正在验证后台身份…';
      try{await verify('researcher02',key);$('presence-verify-key').value='';await refresh()}
      catch(e){forget();reset(e?.message==='unauthorized'?'管理员在线访问密钥不正确。':'后台验证暂时不可用，请重试。')}
      finally{button.disabled=false}
    });
    refreshButton.addEventListener('click',refresh);
    issueForm.addEventListener('submit',async e=>{
      e.preventDefault();const s=current(),account=select.value;
      if(!verified||!s||s.account!=='researcher02'||issuing||!validAccount(account)||account==='researcher02')return;
      if(!confirm('为 '+account+' 生成新的在线密钥？已有在线密钥将失效，原密码及资料不受影响。'))return;
      issuing=true;const button=issueForm.querySelector('button');button.disabled=true;issued.hidden=true;issuedKey.value='';issueStatus.textContent='正在生成密钥…';
      try{const result=await call('issue',s.key,account);if(!validKey(result.access_key)||result.account!==account)throw new Error('unavailable');if(current()?.key!==s.key)return;issuedKey.value=result.access_key;issued.hidden=false;issueStatus.textContent='已为 '+account+' 生成新密钥。';void refresh()}
      catch(e){issueStatus.textContent='未能生成密钥，请重试。';if(e?.message==='unauthorized'||e?.message==='forbidden'){forget();reset('后台身份已失效，请重新验证。')}}
      finally{issuing=false;button.disabled=false}
    });
    $('presence-copy').addEventListener('click',async()=>{try{await navigator.clipboard.writeText(issuedKey.value);issueStatus.textContent='密钥已复制，请私下发送。'}catch{issuedKey.select();issueStatus.textContent='请手动复制所选密钥。'}});
    $('presence-disconnect').addEventListener('click',()=>{forget();reset('已退出在线管理。')});
    document.addEventListener('presence-revoked',()=>reset('后台身份已失效，请重新验证。'));
    if(current()?.account==='researcher02')void refresh();
    setInterval(()=>{if(verified&&document.visibilityState==='visible')void refresh()},30000);
  }
  function init(){
    if(document.body.classList.contains('login-page')){forget();return}
    const u=window.CyberlawAuth?.user,s=current();
    if(s&&s.account!==u)forget();
    if(!validAccount(u))return;
    for(const event of ['pointerdown','keydown','scroll','touchstart'])window.addEventListener(event,markActive,{passive:true});
    document.addEventListener('visibilitychange',()=>{if(document.visibilityState==='visible')markActive()});
    window.addEventListener('focus',markActive);
    void heartbeat();setInterval(heartbeat,15000);adminPanel();
  }
  if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',init,{once:true});else init();
})();
