'use strict';
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const model = require('../assets/context-refine.js');
const rows = JSON.parse(fs.readFileSync(path.join(__dirname, '../assets/context-index.json'), 'utf8'));
const current = (name, anchor) => rows.find(x => x.path === `articles/${name}` && x.anchor === anchor);
const run = (label, test) => { test(); console.log('PASS', label); };
run('books are excluded regardless of former column', () => {
  assert(rows.every(x => x.materialType !== 'book'));
  assert(!rows.some(x => /laws-empire|rawls|morality-of-law/.test(x.path)));
  assert(!rows.some(x => x.path === 'papers/2026-08-07.html'));
  assert(!rows.some(x => x.path === 'new-works/2026-08-19.html' && x.anchor === 'research-item-5'));
});
run('separate factual topics for compute network and agent interoperability', () => {
  const item = current('2026-09-07-tech-law-brief.html', 'research-item-2');
  const groups = model.buildTimelines(item, rows);
  assert.equal(groups.length, 2);
  assert.deepEqual(groups.map(g => g.topic), ['算力互联与资源调度','智能体网络与互操作规范']);
  assert(!groups[0].items.some(x => /德国网站|版权|Anthropic/.test(x.title)));
  assert(!groups[1].items.some(x => /算力|隐私政策/.test(x.title)));
});
run('same event and narrow topical developments survive', () => {
  const item = current('2026-09-07-tech-law-brief.html', 'research-item-10');
  const groups = model.buildTimelines(item, rows);
  assert.equal(groups.length, 2);
  assert.deepEqual(groups.map(g => g.topic), ['AI安全事件与披露义务','智能体权限与越权行为']);
  assert(groups.flatMap(g => g.items).some(x => x.title.includes('OpenAI首次公开回应')));
  assert(groups.flatMap(g => g.items).some(x => x.title.includes('接管德国网站')));
  assert(!groups.flatMap(g => g.items).some(x => /版权|算力券|数据中心/.test(x.title)));
});
run('editorial extrapolation does not create factual topics', () => {
  const item = {title:'数据中心电力接入新规', facts:'当地明确数据中心并网和环境许可程序。', text:'智库选题：AI训练版权与数据出境。', topics:['AI训练与版权','数据跨境']};
  const topics = model.detectTopics(item).map(x => x.name);
  assert(topics.includes('数据中心能源与环境许可'));
  assert(!topics.some(x => /版权|出境/.test(x)));
});
run('contrasting another case does not join the cases', () => {
  const item = current('2026-09-07-tech-law-brief.html', 'research-item-18');
  assert(!model.detectTopics(item).some(x => /数据库/.test(x.name)));
});
run('English substrings cannot create AI/ADM/LAWS topics', () => {
  assert.equal(model.detectTopics({title:'New privacy laws for email systems',facts:'A company explained its guidelines.'}).length, 0);
});
run('index facts exclude research commentary on every news item', () => {
  for(const row of rows.filter(x => x.kind === 'news')) {
    assert(row.facts);
    assert(!/智库选题|论文选题|法治研判/.test(row.facts), row.id);
  }
});
run('all groups capped, unique, chronological, and supported by facts', () => {
  for(const item of rows.filter(x => x.kind === 'news')) {
    const groups = model.buildTimelines(item, rows), seen = new Set();
    assert(groups.length <= 2);
    for(const group of groups) {
      assert(group.items.length >= 1 && group.items.length <= 4);
      assert(model.detectTopics(item).some(x => x.name === group.topic));
      let previous = '';
      for(const row of group.items) {
        assert.equal(row.kind, 'news');
        assert(!seen.has(model.key(row))); seen.add(model.key(row));
        assert.notEqual(model.key(item), model.key(row));
        assert(row.date >= previous); previous = row.date;
        assert(model.detectTopics(row).some(x => x.name === group.topic));
      }
    }
  }
});
run('recommendation entry destinations exist and identify specific items', () => {
  for(const row of rows) {
    assert(fs.existsSync(path.join(__dirname,'..',row.path)), row.path);
    if(row.kind !== 'paper') assert(row.anchor && row.anchor.startsWith('research-item-'));
  }
});
console.log('context regression passed');
