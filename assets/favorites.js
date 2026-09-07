(() => {
  const auth = window.CyberlawAuth;
  if (!auth) return;
  const KEY = auth.key('cyberlawInspirationFavoritesV2');
  const script = document.currentScript;
  const assetBase = script ? new URL('.', script.src) : new URL('assets/', location.href);
  const cssHref = new URL('favorites.css', assetBase).href;
  if (!document.querySelector(`link[href="${cssHref}"]`)) {
    const link = document.createElement('link'); link.rel = 'stylesheet'; link.href = cssHref;
    document.head.appendChild(link);
  }
  const load = () => {
    const raw = localStorage.getItem(KEY);
    if (raw === null) return [];
    const value = JSON.parse(raw);
    if (!Array.isArray(value) || value.some(x => !x || typeof x !== 'object')) throw new Error('Invalid saved excerpts');
    return value;
  };
  const save = value => localStorage.setItem(KEY, JSON.stringify(value));
  const normalize = value => String(value || '').replace(/\s+/g, ' ').trim();
  const cleanUrl = value => {
    try { const url = new URL(value, location.href); url.search = ''; url.hash = ''; return url.href; }
    catch { return value; }
  };
  const pageTitle = () => document.querySelector('main h1')?.textContent.trim() || document.title.replace(/｜.*$/, '').trim();
  const category = () => document.querySelector('.eyebrow')?.textContent.trim() || document.querySelector('footer')?.textContent.trim() || '';
  const articleRoot = () => document.querySelector('.article-body .article-wrap,.article-body,.article .reading,.article,main');
  const childPath = (node, root) => {
    const path = [];
    for (let current = node; current; current = current.parentNode) {
      if (current === root) return path;
      if (!current.parentNode) return null;
      path.unshift([...current.parentNode.childNodes].indexOf(current));
    }
    return null;
  };
  const resolvePath = (path, root) => {
    if (!Array.isArray(path)) return null;
    let node = root;
    for (const index of path) { node = node?.childNodes?.[index]; if (!node) return null; }
    return node;
  };
  const excluded = '.ctx-actions,.ctx-inline-panel,.note-inline-panel,.fav-popover,.fav-toast,script,style';
  function textMap(root) {
    const walker = document.createTreeWalker(root, NodeFilter.SHOW_TEXT, {
      acceptNode: node => node.parentElement?.closest(excluded) ? NodeFilter.FILTER_REJECT : NodeFilter.FILTER_ACCEPT
    });
    const chars = [], starts = [], ends = [];
    // Keep an offset map while collapsing whitespace, including whitespace-only nodes.
    // Stored excerpts are normalized; searching unnormalized text cannot reliably restore them.
    while (walker.nextNode()) {
      const node = walker.currentNode;
      for (let offset = 0; offset < node.nodeValue.length; offset++) {
        const char = /\s/.test(node.nodeValue[offset]) ? ' ' : node.nodeValue[offset];
        if (char === ' ' && !chars.length) continue;
        if (char === ' ' && chars[chars.length - 1] === ' ') {
          ends[ends.length - 1] = [node, offset + 1];
          continue;
        }
        chars.push(char); starts.push([node, offset]); ends.push([node, offset + 1]);
      }
    }
    if (chars[chars.length - 1] === ' ') { chars.pop(); starts.pop(); ends.pop(); }
    return {text: chars.join(''), starts, ends};
  }
  function fallbackRange(favorite, root) {
    const anchored = favorite.sourceAnchor ? document.getElementById(favorite.sourceAnchor) : null;
    const scope = anchored && root.contains(anchored) ? anchored : root;
    const map = textMap(scope), needle = normalize(favorite.text);
    if (!needle) return null;
    const index = map.text.indexOf(needle);
    // Do not silently jump to the wrong occurrence of an ambiguous legacy excerpt.
    if (index < 0 || map.text.indexOf(needle, index + 1) >= 0) return null;
    const start = map.starts[index], end = map.ends[index + needle.length - 1];
    if (!start || !end) return null;
    const range = document.createRange();
    try { range.setStart(...start); range.setEnd(...end); return range; } catch { return null; }
  }
  function rangeFor(favorite, root) {
    const start = resolvePath(favorite.startPath, root), end = resolvePath(favorite.endPath, root);
    const anchored = favorite.sourceAnchor ? document.getElementById(favorite.sourceAnchor) : null;
    if (start && end && (!anchored || (anchored.contains(start) && anchored.contains(end)))) {
      try {
        const range = document.createRange();
        range.setStart(start, Math.min(favorite.startOffset || 0, start.nodeType === 3 ? start.nodeValue.length : start.childNodes.length));
        range.setEnd(end, Math.min(favorite.endOffset || 0, end.nodeType === 3 ? end.nodeValue.length : end.childNodes.length));
        if (normalize(range.toString()) === normalize(favorite.text)) return range;
      } catch { /* A changed DOM can invalidate the old path; try text anchoring. */ }
    }
    return fallbackRange(favorite, root);
  }
  let timer;
  function toast(message) {
    let element = document.querySelector('.fav-toast');
    if (!element) { element = document.createElement('div'); element.className = 'fav-toast'; document.body.appendChild(element); }
    element.textContent = message;
    requestAnimationFrame(() => element.classList.add('show'));
    clearTimeout(timer); timer = setTimeout(() => element.classList.remove('show'), 1800);
  }
  let popover, pending;
  const hide = () => { popover?.classList.remove('show'); pending = null; };
  function ensurePopover() {
    if (popover) return popover;
    popover = document.createElement('button'); popover.type = 'button';
    popover.className = 'fav-popover'; popover.textContent = '收藏为灵感';
    document.body.appendChild(popover);
    popover.addEventListener('pointerdown', event => event.preventDefault());
    popover.onclick = () => {
      if (!pending) return;
      const root = articleRoot(), text = normalize(pending.toString());
      if (!root || text.length < 2) return;
      if (text.length > 2000) { toast('一次最多收藏2000字'); return; }
      const startPath = childPath(pending.startContainer, root), endPath = childPath(pending.endContainer, root);
      if (!startPath || !endPath) return;
      try {
        const pageUrl = cleanUrl(location.href), items = load();
        if (items.some(x => cleanUrl(x.pageUrl) === pageUrl && x.text === text)) {
          toast('这段已经收藏过了'); hide(); getSelection()?.removeAllRanges(); return;
        }
        const element = pending.startContainer.nodeType === 1 ? pending.startContainer : pending.startContainer.parentElement;
        const anchor = element?.closest('[id]');
        // Optional metadata; existing V2 records and saved paths remain valid.
        const sourceAnchor = anchor && root.contains(anchor) && anchor.contains(pending.endContainer) ? anchor.id : '';
        items.unshift({id: 'i_' + (globalThis.crypto?.randomUUID?.() || Date.now().toString(36) + Math.random().toString(36).slice(2)),
          pageUrl, title: pageTitle(), category: category(), text, startPath, endPath,
          startOffset: pending.startOffset, endOffset: pending.endOffset, sourceAnchor,
          createdAt: new Date().toISOString(), project: '', tags: [], note: ''});
        save(items);
      } catch {
        toast('摘录未保存。请检查浏览器存储；不要清空原有数据。');
        return;
      }
      toast('已存入灵感摘录'); hide(); getSelection()?.removeAllRanges();
    };
    return popover;
  }
  function show() {
    if (document.body.classList.contains('research-tool-page')) return;
    const selection = getSelection();
    if (!selection || !selection.rangeCount || selection.isCollapsed) { hide(); return; }
    const range = selection.getRangeAt(0), root = articleRoot();
    if (!root || !root.contains(range.commonAncestorContainer) || range.toString().trim().length < 2) { hide(); return; }
    const element = range.commonAncestorContainer.nodeType === 1 ? range.commonAncestorContainer : range.commonAncestorContainer.parentElement;
    if (element?.closest(excluded)) { hide(); return; }
    pending = range.cloneRange();
    const rect = range.getBoundingClientRect(), button = ensurePopover(); button.classList.add('show');
    button.style.left = `${Math.max(10, Math.min(innerWidth - 130, rect.left + rect.width / 2 - 58))}px`;
    button.style.top = `${Math.max(10, Math.min(innerHeight - 45, rect.bottom + 8))}px`;
  }
  let selectionTimer;
  document.addEventListener('selectionchange', () => { clearTimeout(selectionTimer); selectionTimer = setTimeout(show, 90); });
  document.addEventListener('scroll', hide, {passive: true});
  function jump() {
    const id = new URL(location.href).searchParams.get('fav');
    if (!id) return;
    let favorite;
    try { favorite = load().find(x => x.id === id); }
    catch { toast('暂时无法读取摘录，请勿清空原有数据。'); return; }
    const root = articleRoot();
    if (!favorite || !root || cleanUrl(favorite.pageUrl) !== cleanUrl(location.href)) return;
    const range = rangeFor(favorite, root);
    if (!range) { toast('未能准确定位这段摘录，请按摘录文字查找原文。'); return; }
    const element = range.startContainer.nodeType === 1 ? range.startContainer : range.startContainer.parentElement;
    setTimeout(() => element?.scrollIntoView({behavior: 'smooth', block: 'center'}), 150);
  }
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', jump);
  else jump();
})();
