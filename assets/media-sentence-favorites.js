(() => {
  const auth = window.CyberlawAuth;
  if (!auth) return;
  const KEY = auth.key('cyberlawInspirationFavoritesV2');
  const normalize = value => String(value || '').replace(/\s+/g, ' ').trim();
  const cleanUrl = value => {
    try { const url = new URL(value, location.href); url.search = ''; url.hash = ''; return url.href; }
    catch { return value; }
  };
  const load = () => {
    const raw = localStorage.getItem(KEY);
    if (raw === null) return [];
    const value = JSON.parse(raw);
    if (!Array.isArray(value) || value.some(x => !x || typeof x !== 'object')) throw new Error('Invalid saved excerpts');
    return value;
  };
  const save = value => localStorage.setItem(KEY, JSON.stringify(value));
  let timer;
  function toast(message) {
    let element = document.querySelector('.fav-toast');
    if (!element) { element = document.createElement('div'); element.className = 'fav-toast'; document.body.appendChild(element); }
    element.textContent = message;
    requestAnimationFrame(() => element.classList.add('show'));
    clearTimeout(timer); timer = setTimeout(() => element.classList.remove('show'), 1600);
  }
  function info(button) {
    const sentence = button.closest('.media-sentence');
    const item = button.closest('.media-item');
    const text = normalize(sentence?.querySelector('.sentence-text')?.textContent);
    const title = normalize(item?.querySelector('h3')?.textContent) || document.title.replace(/｜.*$/, '');
    const source = item?.querySelector('.media-source a');
    const id = sentence?.id || '';
    return {sentence, item, text, title, source, id};
  }
  function matching(items, data) {
    const page = cleanUrl(location.href);
    return items.findIndex(x => cleanUrl(x.pageUrl) === page && normalize(x.text) === data.text);
  }
  function refresh(button) {
    try {
      const data = info(button), active = matching(load(), data) >= 0;
      button.classList.toggle('active', active);
      button.textContent = active ? '★ 已收藏' : '☆ 收藏';
      button.setAttribute('aria-pressed', active ? 'true' : 'false');
    } catch {
      button.textContent = '☆ 收藏';
    }
  }
  document.addEventListener('click', event => {
    const button = event.target.closest('[data-sentence-fav]');
    if (!button) return;
    const data = info(button);
    if (!data.text || !data.sentence) return;
    try {
      const items = load(), index = matching(items, data);
      if (index >= 0) {
        items.splice(index, 1);
        save(items);
        toast('已取消收藏');
      } else {
        items.unshift({
          id:'i_' + (globalThis.crypto?.randomUUID?.() || Date.now().toString(36) + Math.random().toString(36).slice(2)),
          pageUrl:cleanUrl(location.href),
          title:data.title,
          category:'权威媒体AI摘编',
          text:data.text,
          sourceAnchor:data.id,
          sourceUrl:data.source?.href || '',
          createdAt:new Date().toISOString(),
          project:'',
          tags:[],
          note:''
        });
        save(items);
        toast('已收藏这句原文');
      }
      refresh(button);
    } catch {
      toast('收藏未保存，请检查浏览器存储。');
    }
  });
  function init() {
    document.querySelectorAll('[data-sentence-fav]').forEach(refresh);
    const favId = new URL(location.href).searchParams.get('fav');
    if (!favId) return;
    try {
      const favorite = load().find(x => x.id === favId);
      if (!favorite || cleanUrl(favorite.pageUrl) !== cleanUrl(location.href) || !favorite.sourceAnchor) return;
      const target = document.getElementById(favorite.sourceAnchor);
      if (!target) return;
      target.scrollIntoView({behavior:'smooth', block:'center'});
      target.classList.add('fav-flash');
      setTimeout(() => target.classList.remove('fav-flash'), 2400);
    } catch {}
  }
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', init);
  else init();
})();