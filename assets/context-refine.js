/* Item-level reading and factual topic timelines. No private reader data is read. */
(function (global) {
  'use strict';
  const VERSION = '4';
  const normal = s => String(s || '').toLowerCase().replace(/[\s\p{P}\p{S}]+/gu, '');
  const hit = (text, word) => {
    const value = String(text || '').toLowerCase(), term = word.toLowerCase();
    if (/^[a-z0-9 .-]+$/.test(term)) {
      const escaped = term.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
      return new RegExp('(^|[^a-z0-9])' + escaped + '($|[^a-z0-9])', 'i').test(value);
    }
    return value.includes(term);
  };
  const any = (text, words) => words.some(w => hit(text, w));
  // Every group must match. A single generic AI/data/company keyword is never enough.
  const TOPICS = [
    ['AI民事纠纷与司法救济', [['人工智能','AI','算法'], ['纠纷','民事','损害赔偿','侵权责任','禁令']]],
    ['智能体权限与越权行为', [['智能体','agentic','ai agent','AI代理'], ['越权','权限','接管','入侵','授权','网络风险','非预期行动','德国网站','Wiki']]],
    ['AI安全事件与披露义务', [['AI','人工智能','模型','OpenAI','智能体'], ['事故披露','事件报告','报告标准','失控','异常行为','网站事件']]],
    ['前沿AI能力评测与安全防护', [['AI','人工智能','模型','OpenAI','智能体'], ['前沿能力','红队','安全评测','网络能力','Preparedness Framework']]],
    ['生成式AI备案与服务管理', [['生成式','大模型'], ['备案','登记','服务管理','服务登记']]],
    ['公共部门AI与自动化行政', [['AI','人工智能','算法','自动化'], ['行政','政务','公共部门','监管执法','政府决策']]],
    ['诉讼与仲裁中的AI使用', [['AI','人工智能'], ['诉讼程序','证据使用','AI证据','材料真实性','使用披露','AI程序','仲裁','难民委员会','法院提交']]],
    ['算法招聘与劳动管理', [['算法','AI','人工智能','自动化'], ['招聘','求职','用工','劳动','从业人员','就业','强迫通行']]],
    ['机器遗忘与数据删除', [['机器遗忘','删除权','被遗忘权','去索引','machine unlearning','数据删除']]],
    ['匿名化与重新识别', [['匿名化','匿名数据','去标识化','重新识别','再识别','anonymization']]],
    ['数据跨境与出境合规', [['数据跨境','跨境数据','数据出境','cross-border data','数据传输协议']]],
    ['公共数据开放与授权运营', [['公共数据','数据开放','授权运营','开放数据'], ['数据','授权']]],
    ['政府数据库调用与目的限制', [['政府','行政','SAVE','国土安全','社保'], ['数据库','数据调用','数据共享','二次利用','数据复用','公民身份']]],
    ['数据要素赛事与成果转化', [['数据要素'], ['赛事','大赛','赛道','分赛','竞赛','总决赛']]],
    ['高质量数据集与数据标注', [['高质量数据集','数据标注','训练数据集','AI原生数据','合成数据']]],
    ['生物识别与身份信息保护', [['生物识别','人脸识别','面部认证','语音身份','车牌识别','biometric','facial recognition']]],
    ['未成年人上网与年龄核验', [['儿童','未成年','青少年','children','年龄'], ['上网','社交','平台','核验','隐私','数据','安全','最低年龄']]],
    ['平台内容治理与DSA实施', [['DSA','数字服务法','内容治理','非法内容','推荐算法','平台问责']]],
    ['AI训练版权与数据许可', [['AI','人工智能','模型','OpenAI','Anthropic','TDM'], ['版权','著作权','创作者作品','合理使用','fair use','侵权'], ['训练','training','挖掘','TDM','数据许可']]],
    ['AI生成内容与作者资格', [['AI','人工智能','生成式'], ['作者资格','法定作者','可版权性','作品登记','著作权登记']]],
    ['深度合成侵权与内容标识', [['深度伪造','deepfake','换脸','拟声','AI脱衣','“脱衣”','合成内容','数字水印'], ['内容','侵权','禁令','标识','披露','规则','性虐待','治理','安全','标准','禁止']]],
    ['平台反垄断与竞争执法', [['平台','Google','Apple','Microsoft','Amazon','Oracle','亚马逊','谷歌','苹果','DMA','应用商店'], ['反垄断','竞争','垄断','自我优待','守门人','antitrust','拆分','并购']]],
    ['行政性市场壁垒与公平竞争', [['统一市场','行政垄断','歧视性准入','地方保护','公平竞争审查','垄断协议个人责任']]],
    ['数据泄露与损害补救', [['数据泄露','信息泄露','被盗数据','数据暴露','泄露事件','客户数据','账户标识'], ['泄露','暴露','被盗','补偿','通知','赔偿','补救']]],
    ['勒索软件事件与处置', [['勒索软件','ransomware','勒索团伙','勒索攻击']]],
    ['漏洞利用与修补处置', [['漏洞','CVE','MikroTik'], ['利用','修复','修补','补丁','攻击','预警']]],
    ['关键基础设施与混合威胁防护', [['关键基础设施','关键信息基础设施','OT','基础设施'], ['安全','防护','威胁','破坏','攻击','韧性']]],
    ['后量子密码迁移', [['后量子','post-quantum','PQC']]],
    ['先进芯片与出口管制', [['芯片','半导体','GPU','先进计算'], ['出口管制','出口限制','禁运','许可限制','军事公司','实体清单']]],
    ['半导体材料与贸易救济', [['半导体','二氯二氢硅','晶圆'], ['反倾销','反补贴','贸易救济','保证金']]],
    ['科技商业秘密与跨境执法', [['商业秘密','技术泄密','半导体技术','泄密'], ['调查','诉讼','起诉','刑事','检方','窃取','盗窃']]],
    ['算力互联与资源调度', [['算力网','算力互联','算力调度','算力网络','词元工厂','一体化算力']]],
    ['算力与模型服务的财政支持', [['算力券','数据券','模型券','算力补贴','词元付费']]],
    ['智能体网络与互操作规范', [['智能体互联网','数据智能体','代理协议','Model Hardware Standard']]],
    ['数据中心能源与环境许可', [['数据中心','算力基地'], ['能源','电力','环境','空气许可','能耗','并网','水资源','资源披露','液冷','吉瓦']]],
    ['AI云服务与数字主权', [['云','cloud'], ['主权','依赖','供应链','准入','分发','迁移','采购','国防']]],
    ['选举AI与政治广告规则', [['选举','选民','投票','政治广告','election'], ['AI','人工智能','深度伪造','合成内容','机器人']]],
    ['自主武器与人类控制', [['自主武器','autonomous weapon','致命自主武器']]],
    ['军用AI与供应链限制', [['AI','人工智能','Anthropic'], ['军事','军用','五角大楼','国防','军方']]],
    ['前沿AI安全国际协调', [['AI','人工智能'], ['国际机构','国际规则','国际框架','安全对话','G20','红线','独立核验','治理机构'], ['安全','危险模型','高能力','前沿','红线']]],
    ['Cookie同意与应用追踪', [['Cookie','追踪','跟踪','tracking'], ['同意','隐私','数据','广告','GDPR']]],
    ['网络接入实名与日志规则', [['会话记录','浏览历史','网络接入日志','上网服务','实名核验'], ['日志','会话','浏览历史','实名','核验']]],
    ['自动驾驶准入与事故责任', [['自动驾驶','辅助驾驶','Cybercab','无人驾驶'], ['责任','上路','设计','合规','交通','准入','保险']]],
    ['数字化公司报告与信息披露', [['公司报告','企业报告','资本市场','证券','公司叙事','ESG'], ['报告','披露','AI','人工智能','数字化']]],
    ['医疗数据与网络安全', [['医疗','医院','患者','HIPAA'], ['数据','隐私','安全','泄露']]],
    ['AI诈骗与金融消费者保护', [['诈骗','网络金融','金融消费者'], ['AI','人工智能','网络','算法','数字','反诈']]]
  ];
  const groupsMatch = (text, groups) => groups.every(words => any(text, words));
  function detectTopics(item) {
    const title = item.title || '';
    const sentences = String(item.facts || '').split(/[。！？；\n]/).filter(s => s.trim() && !/不同于|无关|不能据以|^\s*(?:上述|此次收录|新的信息|并非|不是|不能|不应)/.test(s));
    return TOPICS.map(([name, groups]) => {
      // Only the headline and fact sentences can establish a timeline topic.
      const titleMatch = groupsMatch(title, groups);
      const factMatch = sentences.some(s => groupsMatch(s, groups));
      if (name === '数据泄露与损害补救' && /预算|年度计划/.test(title)) return null;
      if (name === '漏洞利用与修补处置' && /能力阈值|发布.{0,12}模型/.test(title)) return null;
      if (!titleMatch && !factMatch) return null;
      const titleGroups = groups.filter(ws => any(title, ws)).length;
      const mentions = groups.flat().filter(w => hit(title, w)).length;
      return { name, score: (titleMatch ? 100 : 40) + titleGroups * 8 + Math.min(mentions, 4) };
    }).filter(Boolean).sort((a, b) => b.score - a.score);
  }
  const grams = s => {
    const value = normal(s), out = new Set();
    for (let i = 0; i < value.length - 1; i++) out.add(value.slice(i, i + 2));
    return out;
  };
  function similarity(a, b) {
    const A = grams(a), B = grams(b);
    let shared = 0;
    for (const g of A) if (B.has(g)) shared++;
    return shared / Math.max(1, A.size + B.size - shared);
  }
  const key = x => x.path + (x.anchor ? '#' + x.anchor : '');
  const sameItem = (a, b) => key(a) === key(b);
  function duplicate(a, b) {
    if (sameItem(a, b) || normal(a.title) === normal(b.title)) return true;
    if (a.date === b.date && similarity(a.title, b.title) > .68) return true;
    return Boolean(a.sourceUrl && a.sourceUrl === b.sourceUrl && similarity(a.title, b.title) > .32);
  }
  function entityOverlap(a, b) {
    const entities = s => (String(s || '').match(/\b(?:OpenAI|Anthropic|Microsoft|Google|Meta|Tesla|TikTok|SAVE|Cybercab|Weverse|TVING|MikroTik)\b/gi) || []).map(normal);
    const A = new Set(entities(a.title + ' ' + a.facts));
    const B = new Set(entities(b.title + ' ' + b.facts));
    return [...A].filter(x => B.has(x)).length;
  }
  function buildTimelines(current, rows) {
    const news = rows.filter(x => x.kind === 'news' && x.path && x.anchor && /^\d{4}-\d{2}-\d{2}$/.test(x.date || '') && !sameItem(current, x));
    const own = detectTopics(current);
    const prepared = news.map(x => ({ x, topics: new Map(detectTopics(x).map(t => [t.name, t.score])) }));
    const used = [], result = [];
    for (const topic of own) {
      const candidates = prepared.filter(p => p.topics.has(topic.name)).map(p => ({
        x: p.x,
        score: entityOverlap(current, p.x) * 25 + similarity(current.title, p.x.title) * 20 + p.topics.get(topic.name) / 10
      })).sort((a, b) => b.score - a.score || String(b.x.date).localeCompare(String(a.x.date)) || key(a.x).localeCompare(key(b.x)));
      const selected = [];
      for (const { x } of candidates) {
        if ([...used, ...selected].some(y => duplicate(y, x))) continue;
        selected.push(x);
        if (selected.length === 4) break;
      }
      if (!selected.length) continue;
      used.push(...selected);
      result.push({ topic: topic.name, items: selected.sort((a, b) => String(a.date).localeCompare(String(b.date)) || key(a).localeCompare(key(b))) });
      if (result.length === 2) break;
    }
    return result;
  }
  function relatedRows(current, rows, kind) {
    const own = new Set(current.topics || []);
    const directTopics = detectTopics(current).map(t => t.name);
    const candidates = rows.filter(x => x.kind === kind && x.materialType !== 'book' && !sameItem(current, x));
    const ranked = candidates.map(x => {
      const shared = (x.topics || []).filter(t => own.has(t)).length;
      const narrow = detectTopics(x).filter(t => directTopics.includes(t.name)).length;
      return { x, score: shared * 8 + narrow * 10 + similarity(current.title, x.title) * 15 };
    }).filter(p => p.score >= 8).sort((a, b) => b.score - a.score || String(b.x.date).localeCompare(String(a.x.date)));
    const selected = [];
    for (const { x } of ranked) {
      if (selected.some(y => duplicate(y, x))) continue;
      selected.push(x);
      if (selected.length === 3) break;
    }
    return selected;
  }
  const api = { detectTopics, buildTimelines, relatedRows, similarity, duplicate, key };
  if (typeof module !== 'undefined' && module.exports) module.exports = api;
  if (!global.document) return;
  const document = global.document, script = document.currentScript;
  const assetBase = script ? new URL('.', script.src) : new URL('assets/', location.href);
  const siteRoot = new URL('../', assetBase);
  const esc = s => String(s == null ? '' : s).replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  const path = () => decodeURIComponent(location.pathname).slice(siteRoot.pathname.length);
  let pendingIndex;
  function getIndex() {
    if (!pendingIndex) pendingIndex = fetch(new URL('context-index.json?v=' + VERSION, assetBase))
      .then(r => { if (!r.ok) throw new Error('context-index'); return r.json(); })
      .then(rows => { if (!Array.isArray(rows)) throw new Error('context-index'); return rows; })
      .catch(error => { pendingIndex = null; throw error; });
    return pendingIndex;
  }
  function cleaned(target) {
    const copy = target.cloneNode(true);
    copy.querySelectorAll('.ctx-actions,.source,.reading-directory,.note-inline-panel,script,style,nav').forEach(n => n.remove());
    return copy;
  }
  function currentItem(target, rows) {
    const item = rows.find(x => x.path === path() && (x.anchor ? x.anchor === target.id : !target.matches('.brief-item')));
    if (item) return item;
    // Unknown/new pages use only their own text, never recommendation output.
    const copy = cleaned(target);
    const isCard = target.matches('.brief-item');
    const title = (isCard ? copy.querySelector('h3,h2') : document.querySelector('main h1'))?.textContent.trim() || document.title;
    const facts = [...copy.children].filter(n => n.tagName === 'P' && !/^(法治研判|智库选题|论文选题|意义|来源)/.test(n.textContent.trim())).map(n => n.textContent.trim()).slice(0, 2).join(' ');
    const topics = [...new Set(detectTopics({ title, facts }).map(t => t.name))];
    return { title, facts, text: copy.textContent, path: path(), anchor: isCard ? target.id : '', topics };
  }
  function href(row) {
    try {
      const url = new URL(row.path, siteRoot);
      if (url.origin !== siteRoot.origin || !url.pathname.startsWith(siteRoot.pathname)) return '';
      if (row.anchor) url.hash = row.anchor;
      return url.href;
    } catch { return ''; }
  }
  function relatedBlock(label, rows) {
    if (!rows.length) return '';
    return `<section class="ctx-theme-block"><h4>${label}</h4><div class="ctx-related">${rows.map(x => `<a href="${esc(href(x))}"><strong>${esc(x.title)}</strong><span>${esc(x.date || '')}</span></a>`).join('')}</div></section>`;
  }
  function renderRelated(panel, item, rows) {
    const html = [['相关新闻','news'],['研究新作','work'],['论文精读','paper']]
      .map(([name, kind]) => relatedBlock(name, relatedRows(item, rows, kind))).join('');
    panel.innerHTML = `<div class="ctx-panel-title">关联阅读</div>${html || '<p class="ctx-empty">暂无相关内容。</p>'}`;
  }
  let serial = 0;
  function renderTimeline(panel, item, rows) {
    const groups = buildTimelines(item, rows);
    panel.innerHTML = '<div class="ctx-panel-title">专题时间线</div>';
    if (!groups.length) { panel.insertAdjacentHTML('beforeend','<p class="ctx-empty">暂无相关专题新闻。</p>'); return; }
    const prefix = 'timeline-' + (++serial);
    const tablist = document.createElement('div');
    tablist.className = 'ctx-topic-tabs';
    tablist.setAttribute('role', 'tablist');
    tablist.setAttribute('aria-label', '新闻专题');
    panel.appendChild(tablist);
    const tabs = [], panes = [];
    groups.forEach((group, i) => {
      const tab = document.createElement('button');
      tab.type = 'button'; tab.id = `${prefix}-tab-${i}`; tab.textContent = group.topic;
      tab.setAttribute('role','tab'); tab.setAttribute('aria-controls',`${prefix}-pane-${i}`);
      tablist.appendChild(tab); tabs.push(tab);
      const pane = document.createElement('section');
      pane.className = 'ctx-topic-timeline'; pane.id = `${prefix}-pane-${i}`;
      pane.setAttribute('role','tabpanel'); pane.setAttribute('aria-labelledby',tab.id);
      pane.innerHTML = `<div class="ctx-timeline">${group.items.map(x => `<a href="${esc(href(x))}"><time datetime="${esc(x.date)}">${esc(x.date)}</time><span><strong>${esc(x.title)}</strong>${x.meta ? `<small>${esc(x.meta)}</small>` : ''}</span></a>`).join('')}</div>`;
      panel.appendChild(pane); panes.push(pane);
    });
    function activate(index, focus = false) {
      tabs.forEach((tab, i) => { tab.setAttribute('aria-selected', String(i === index)); tab.tabIndex = i === index ? 0 : -1; panes[i].hidden = i !== index; });
      if (focus) tabs[index].focus();
    }
    tabs.forEach((tab, i) => {
      tab.onclick = () => activate(i);
      tab.onkeydown = event => {
        if (!['ArrowRight','ArrowLeft','Home','End'].includes(event.key)) return;
        event.preventDefault();
        const next = event.key === 'Home' ? 0 : event.key === 'End' ? tabs.length - 1 : (i + (event.key === 'ArrowRight' ? 1 : -1) + tabs.length) % tabs.length;
        activate(next, true);
      };
    });
    activate(0);
  }
  const css = document.createElement('link'); css.rel = 'stylesheet';
  css.href = new URL('context-topics.css?v=' + VERSION, assetBase).href;
  document.head.appendChild(css);
  document.addEventListener('click', async event => {
    const btn = event.target.closest?.('.ctx-actions [data-act]');
    if (!btn) return;
    const actions = btn.closest('.ctx-actions'), panel = actions.querySelector('.ctx-inline-panel');
    if (!panel) return;
    if (!['related','timeline'].includes(btn.dataset.act)) { delete panel.dataset.contextMode; delete panel.dataset.contextToken; return; }
    event.preventDefault(); event.stopImmediatePropagation();
    const mode = btn.dataset.act;
    if (panel.dataset.contextMode === mode && panel.classList.contains('show')) {
      panel.classList.remove('show'); delete panel.dataset.contextToken; btn.setAttribute('aria-expanded','false'); return;
    }
    delete panel.dataset.citeRefined; delete panel.dataset.refineMode; delete panel.dataset.relatedV3;
    panel.dataset.contextMode = mode;
    const token = String(++serial); panel.dataset.contextToken = token;
    panel.innerHTML = '<p class="ctx-empty" role="status">正在加载…</p>'; panel.classList.add('show');
    btn.setAttribute('aria-expanded','true');
    try {
      const rows = await getIndex();
      if (panel.dataset.contextToken !== token) return;
      const item = currentItem(actions.parentElement, rows);
      if (mode === 'related') renderRelated(panel, item, rows); else renderTimeline(panel, item, rows);
    } catch {
      if (panel.dataset.contextToken === token) panel.innerHTML = '<p class="ctx-empty" role="alert">暂时无法加载，请稍后重试。</p>';
    }
  }, true);
})(typeof window !== 'undefined' ? window : globalThis);
