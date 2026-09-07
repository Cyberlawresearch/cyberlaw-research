(() => {
  const auth = window.CyberlawAuth;
  if (!auth) return;
  const NOTES = auth.key('cyberlawNotesV1');
  const FULL = auth.key('cyberlawFullFavoritesV2');
  // A failed read is not an empty collection. Never overwrite unreadable data.
  const load = key => {
    const raw = localStorage.getItem(key);
    if (raw === null) return [];
    const value = JSON.parse(raw);
    if (!Array.isArray(value) || value.some(x => !x || typeof x !== 'object')) {
      throw new Error('Invalid saved collection');
    }
    return value;
  };
  const save = (key, value) => localStorage.setItem(key, JSON.stringify(value));
  const clean = value => {
    try { const url = new URL(value, location.href); url.search = ''; url.hash = ''; return url.href; }
    catch { return value; }
  };
  const newId = prefix => prefix + (globalThis.crypto?.randomUUID?.() ||
    Date.now().toString(36) + Math.random().toString(36).slice(2));
  let timer;
  function toast(message) {
    let element = document.querySelector('.fav-toast');
    if (!element) {
      element = document.createElement('div');
      element.className = 'fav-toast';
      document.body.appendChild(element);
    }
    element.textContent = message;
    requestAnimationFrame(() => element.classList.add('show'));
    clearTimeout(timer);
    timer = setTimeout(() => element.classList.remove('show'), 1800);
  }
  const category = () => document.title.includes('科技法研究新作') ? '科技法研究新作' :
    document.title.includes('全球科技法简报') ? '科技新闻' :
    document.body.classList.contains('classic-page') || document.title.includes('经典') ? '法学经典著作' :
    document.title.includes('论文') ? '域外法学论文精读' : '研究内容';
  function infoFor(actions) {
    // The action bar belongs to its parent, not the first article on the page.
    const target = actions.parentElement;
    if (!target) throw new Error('Missing note target');
    const isItem = target.matches('.brief-item');
    const heading = isItem ? target.querySelector('h3,h2') : document.querySelector('main h1');
    const title = (heading?.textContent || document.title.replace(/｜.*$/, '')).replace(/^\s*\d+[.、]\s*/, '').trim();
    if (!target.id) {
      const index = [...document.querySelectorAll('.ctx-actions')].indexOf(actions) + 1;
      let id = `research-item-${index}`, suffix = 1;
      while (document.getElementById(id)) id = `research-item-${index}-${suffix++}`;
      target.id = id;
    }
    const copy = target.cloneNode(true);
    copy.querySelectorAll('.ctx-actions,.ctx-inline-panel,.note-inline-panel,.fav-popover,.fav-toast,script,style').forEach(x => x.remove());
    copy.querySelectorAll('p,h1,h2,h3,h4,li,br,div,section').forEach(x => x.appendChild(document.createTextNode(' ')));
    const text = (copy.textContent || '').replace(/\s+/g, ' ').trim();
    const id = target.id;
    return {
      target, actions, title, id, isItem,
      pageUrl: clean(location.href) + '#' + encodeURIComponent(id),
      text, meta: target.querySelector('.brief-meta')?.textContent.trim() || '',
      sourceType: category()
    };
  }
  function ensureFavorite(info, favorites) {
    const itemKey = `${clean(location.href)}#${info.id}`;
    const existing = favorites.find(x => x.itemKey === itemKey ||
      (!info.isItem && x.itemKey === `${clean(location.href)}#article`));
    if (existing) return existing.id;
    const id = newId('c_');
    favorites.unshift({id, itemKey, pageUrl: info.pageUrl, title: info.title,
      category: info.sourceType, date: '', meta: info.meta, summary: info.text.slice(0, 360),
      topics: [], tags: [], createdAt: new Date().toISOString(), project: '', note: ''});
    save(FULL, favorites);
    // A local lookup also works when the original document had no ID.
    const button = info.actions.querySelector('[data-act="fav"]');
    if (button) button.textContent = '✓ 已收藏';
    return id;
  }
  function enhance(actions) {
    if (actions.querySelector('[data-note-inline]')) return;
    const button = document.createElement('button');
    button.type = 'button';
    button.dataset.noteInline = '1';
    button.textContent = '写笔记';
    actions.insertBefore(button, actions.querySelector('[data-act="related"]') || actions.firstChild);
    const panel = document.createElement('div');
    panel.className = 'note-inline-panel';
    panel.hidden = true;
    panel.innerHTML = '<input class="note-inline-title" aria-label="笔记标题" placeholder="笔记标题（可选）"><textarea class="note-inline-text" aria-label="笔记内容" placeholder="记下你的判断、联想或问题"></textarea><div class="note-inline-actions"><button type="button" data-note-save>保存</button><button type="button" data-note-cancel>取消</button></div>';
    actions.appendChild(panel);
    button.onclick = () => {
      panel.hidden = !panel.hidden;
      if (!panel.hidden) panel.querySelector('.note-inline-text').focus();
    };
    panel.querySelector('[data-note-cancel]').onclick = () => { panel.hidden = true; };
    panel.querySelector('[data-note-save]').onclick = () => {
      const content = panel.querySelector('.note-inline-text').value.trim();
      if (!content) { toast('先写一点内容'); return; }
      try {
        // Validate both stores before making any persistent change.
        const notes = load(NOTES), favorites = load(FULL), info = infoFor(actions);
        const favoriteId = ensureFavorite(info, favorites), now = new Date().toISOString();
        notes.unshift({id: newId('n_'), title: panel.querySelector('.note-inline-title').value.trim() || content.slice(0, 28),
          content, project: '', tags: [], sourceTitle: info.title, sourceUrl: info.pageUrl,
          sourceType: info.sourceType, sourceExcerpt: info.text.slice(0, 260), favoriteId,
          createdAt: now, updatedAt: now});
        save(NOTES, notes);
      } catch {
        toast('笔记未保存，输入已保留。请检查浏览器存储；不要清空原有数据。');
        return;
      }
      panel.querySelector('.note-inline-title').value = '';
      panel.querySelector('.note-inline-text').value = '';
      panel.hidden = true;
      toast('笔记已保存');
    };
  }
  const scan = () => document.querySelectorAll('.ctx-actions').forEach(enhance);
  new MutationObserver(scan).observe(document.documentElement, {childList: true, subtree: true});
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', scan);
  else scan();
})();
