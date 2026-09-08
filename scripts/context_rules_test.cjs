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
  assert.deepEqual(groups.map(g => g.topic), ['算力互联与资源调度','智能体治理']);
  assert(!groups[0].items.some(x => /德国网站|版权|Anthropic/.test(x.title)));
  assert(!groups[1].items.some(x => /算力|隐私政策/.test(x.title)));
});
run('same event and narrow topical developments survive', () => {
  const item = current('2026-09-07-tech-law-brief.html', 'research-item-10');
  const groups = model.buildTimelines(item, rows);
  assert.equal(groups.length, 2);
  assert.deepEqual(groups.map(g => g.topic), ['AI安全事件与披露义务','智能体治理']);
  assert(groups.flatMap(g => g.items).some(x => x.title.includes('OpenAI首次公开回应')));
  assert(groups.flatMap(g => g.items).some(x => x.title.includes('接管德国网站')));
  assert(!groups.flatMap(g => g.items).some(x => /版权|算力券|数据中心/.test(x.title)));
});
run('agent permissions and interoperability form one topic and candidate pool', () => {
  const permissions = {title:'智能体越权调用外部应用', facts:'测试发现智能体超出授权权限，调用外部工具。', kind:'news', path:'permissions.html', anchor:'research-item-1', date:'2026-08-01'};
  const interop = {title:'数据智能体互操作规范发布', facts:'数据智能体采用代理协议，规范跨应用互操作。', kind:'news', path:'interop.html', anchor:'research-item-1', date:'2026-08-02'};
  const both = {title:'智能体权限与代理协议规范', facts:'数据智能体跨应用运行需要授权管理和互操作规范。', kind:'news', path:'both.html', anchor:'research-item-1', date:'2026-08-03'};
  for (const item of [permissions, interop, both]) {
    assert.deepEqual(model.detectTopics(item).map(t => t.name), ['智能体治理']);
  }
  const groups = model.buildTimelines(both, [permissions, interop, both]);
  assert.equal(groups.length, 1);
  assert.equal(groups[0].topic, '智能体治理');
  assert.deepEqual(groups[0].items.map(x => x.path), ['permissions.html', 'interop.html']);
  assert(model.buildTimelines(permissions, [permissions, interop]).some(g => g.items.some(x => x.path === 'interop.html')));
  assert(model.buildTimelines(interop, [permissions, interop]).some(g => g.items.some(x => x.path === 'permissions.html')));
});
run('agent governance does not absorb general AI or editorial mentions', () => {
  for (const item of [
    {title:'OpenAI发布大模型', facts:'公司介绍模型参数和价格。'},
    {title:'数据中心扩建', facts:'企业增加电力供应和服务器容量。', text:'论文选题：智能体权限与互操作', topics:['智能体AI']},
    {title:'开放网络互操作协议', facts:'系统新增通用网络访问权限。'},
    {title:'AI训练版权诉讼', facts:'法院审查训练语料的合理使用问题。'}
  ]) assert(!model.detectTopics(item).some(t => t.name === '智能体治理'));
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
    const detected = model.detectTopics(item).map(t => t.name);
    assert.equal(detected.length, new Set(detected).size);
    assert(!detected.some(t => /智能体权限与越权行为|智能体网络与互操作规范/.test(t)));
    const groups = model.buildTimelines(item, rows), seen = new Set();
    assert.equal(groups.length, new Set(groups.map(g => g.topic)).size);
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
