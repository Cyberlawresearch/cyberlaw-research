(()=>{
  const version='3';
  const fnv=s=>{let h=0x811c9dc5;for(let i=0;i<s.length;i++){h^=s.charCodeAt(i);h=Math.imul(h,0x01000193)>>>0}return h>>>0};
  const form=document.getElementById('login-form'),err=document.getElementById('login-error');
  const validUser=u=>/^researcher(?:0[1-9]|1\d|20)$/.test(u);
  const initialPassword=u=>'law2026'+u.slice(-2);
  let busy=false;
  form?.addEventListener('submit',async e=>{
    e.preventDefault();if(busy)return;
    const u=document.getElementById('login-user').value.trim(),p=document.getElementById('login-password').value;
    if(!validUser(u)){err.textContent='账号或密码不正确。';return}
    let ok=false;
    try{const v=localStorage.getItem('cyberlawPasswordVersion::'+u),override=v===version?Number(localStorage.getItem('cyberlawPasswordOverride::'+u)||0):0;ok=override?fnv(u+'|'+p)===override:p===initialPassword(u)}catch{}
    if(ok){window.CyberlawPresence?.forget()}
    else if(/^[0-9a-f]{64}$/.test(p)){
      const button=form.querySelector('button[type="submit"]');busy=true;if(button)button.disabled=true;err.textContent='正在验证在线访问密钥…';
      try{
        if(!window.CyberlawPresence)throw new Error('unavailable');
        await window.CyberlawPresence.verify(u,p);ok=true;
      }catch(error){err.textContent=error?.message==='unauthorized'?'账号或在线访问密钥不正确。':'在线验证暂时不可用，可使用原有密码登录。';return}
      finally{busy=false;if(button)button.disabled=false}
    }
    if(!ok){err.textContent='账号或密码不正确。';return}
    document.cookie='cyberlaw_user='+encodeURIComponent(u)+'; Max-Age=7776000; Path=/cyberlaw-research/; SameSite=Lax; Secure';
    const next=new URL(location.href).searchParams.get('next');
    if(next&&next.startsWith('/cyberlaw-research/'))location.replace(next);else location.replace('index.html');
  });
})();
