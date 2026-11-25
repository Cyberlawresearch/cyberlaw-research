(()=>{const auth=window.CyberlawAuth;if(!auth)return;const version='3';const fnv=s=>{let h=0x811c9dc5;for(let i=0;i<s.length;i++){h^=s.charCodeAt(i);h=Math.imul(h,0x01000193)>>>0}return h>>>0};const initialPassword=u=>'law2026'+u.slice(-2);const form=document.getElementById('password-form'),msg=document.getElementById('password-message'),userEl=document.getElementById('account-name');if(userEl)userEl.textContent=auth.user;form?.addEventListener('submit',e=>{e.preventDefault();const old=document.getElementById('password-current').value,neo=document.getElementById('password-new').value,again=document.getElementById('password-confirm').value;const overrideVersion=localStorage.getItem(auth.passwordVersionKey),override=overrideVersion===version?Number(localStorage.getItem(auth.passwordKey)||0):0;const oldOk=override?fnv(`${auth.user}|${old}`)===override:old===initialPassword(auth.user);if(!oldOk){msg.textContent='当前密码不正确。';msg.className='account-message error';return}if(neo.length<6){msg.textContent='新密码至少需要6位。';msg.className='account-message error';return}if(neo!==again){msg.textContent='两次输入的新密码不一致。';msg.className='account-message error';return}if(neo===old){msg.textContent='新密码不能与当前密码相同。';msg.className='account-message error';return}localStorage.setItem(auth.passwordKey,String(fnv(`${auth.user}|${neo}`)));localStorage.setItem(auth.passwordVersionKey,version);msg.textContent='已保存本机密码。';msg.className='account-message success';form.reset()})})();
/* Export only the current account's research data. No credentials or uploads. */
(()=>{
  const auth=window.CyberlawAuth;if(!auth)return;
  const summary=document.getElementById('account-storage-summary'),button=document.getElementById('account-export'),status=document.getElementById('account-export-status');
  if(!button)return;
  const fields={collections:'cyberlawFullFavoritesV2',excerpts:'cyberlawInspirationFavoritesV2',notes:'cyberlawNotesV1',ideaStates:'cyberlawIdeaStateV2'};
  function readData(){
    const data={};for(const [name,key] of Object.entries(fields)){
      const raw=localStorage.getItem(auth.key(key));
      data[name]=raw===null?(name==='ideaStates'?{}:[]):JSON.parse(raw);
      if(name==='ideaStates'?!data[name]||typeof data[name]!=='object'||Array.isArray(data[name]):!Array.isArray(data[name]))throw new Error('Invalid saved data');
    }return data;
  }
  try{const d=readData();summary.textContent='完整收藏 '+d.collections.length+' 项 · 摘录 '+d.excerpts.length+' 项 · 笔记 '+d.notes.length+' 条 · 已标记选题 '+Object.values(d.ideaStates).filter(Boolean).length+' 项。'}
  catch(_){summary.textContent='暂时无法读取本机资料，请勿清除浏览器数据。'}
  button.addEventListener('click',()=>{try{
    const data=readData(),now=new Date().toISOString(),blob=new Blob([JSON.stringify({schema:'technology-law-personal-data',version:1,account:auth.user,exportedAt:now,...data},null,2)],{type:'application/json'}),url=URL.createObjectURL(blob),a=document.createElement('a');
    a.href=url;a.download='科技法研究资料-'+auth.user+'-'+now.slice(0,10)+'.json';document.body.append(a);a.click();a.remove();setTimeout(()=>URL.revokeObjectURL(url),1000);status.textContent='已生成本机导出文件。请妥善保存。';
  }catch(_){status.textContent='导出失败，原有资料未改动。请检查浏览器存储设置。'}})
})();

(()=>{const auth=window.CyberlawAuth;document.getElementById('account-signout')?.addEventListener('click',()=>auth?.logout())})();
