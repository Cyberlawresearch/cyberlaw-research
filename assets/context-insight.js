/* Loader for contextual insight panels and the verified 2026-10-08 news correction. */
(function(){
  'use strict';
  const here=document.currentScript;
  const base=here?new URL('.',here.src):new URL('assets/',location.href);
  const load=(name,done)=>{const s=document.createElement('script');s.src=new URL(name,base).href;s.onload=done||null;s.onerror=()=>console.error('Failed to load '+name);document.head.appendChild(s)};
  if(location.pathname.endsWith('/articles/2026-10-08-tech-law-brief.html')){
    load('oct8-live-correction.js?v=3',()=>load('context-insight-core.js?v=2'));
  }else{
    load('context-insight-core.js?v=2');
  }
})();
