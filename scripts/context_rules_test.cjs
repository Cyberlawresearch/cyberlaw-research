'use strict';
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const model = require('../assets/context-refine.js');
const rows = JSON.parse(fs.readFileSync(path.join(__dirname, '../assets/context-index.json'), 'utf8'));
const current = (name, anchor) => rows.find(x => x.path === `articles/${name}` && x.anchor === anchor);
const run = (label, test) => { test(); console.log('PASS', label); };

run('books are excluded from recommendation index', () => {
  assert(rows.every(x => x.materialType !== 'book'));
  assert(!rows.some(x => /laws-empire|rawls|morality-of-law/.test(x.path)));
});

run('generic field overlap alone does not establish related reading', () => {
  const a = {title:'某AI产业园发布发展计划', facts:'地方提出支持人工智能产业集聚。', topics:['人工智能治理'], kind:'news', path:'a.html', anchor:'research-item-1', date:'2026-08-01'};
  const b = {title:'大学开设人工智能通识课程', facts:'学校公布面向本科生的课程计划。', topics:['人工智能治理'], kind:'news', path:'b.html', anchor:'research-item-1', date:'2026-08-02'};
  assert.equal(model.directlyRelated(a, b), false);
  assert.deepEqual(model.relatedRows(a, [a, b], 'news'), []);
});

run('same concrete actor and legal issue can establish related reading', () => {
  const a = {title:'OpenAI发布模型失配事件报告框架', facts:'框架用于披露模型异常行为和未经授权行动。', topics:['AI安全'], kind:'news', path:'a.html', anchor:'research-item-1', date:'2026-08-01'};
  const b = {title:'OpenAI披露新的模型失配案例', facts:'公司公开未经授权行动的事件调查。', topics:['AI安全'], kind:'news', path:'b.html', anchor:'research-item-1', date:'2026-08-02'};
  assert(model.directlyRelated(a, b));
  assert.equal(model.relatedRows(a, [a, b], 'news')[0].path, 'b.html');
});

run('related news is not artificially capped', () => {
  const base = {title:'OpenAI披露模型失配事件', facts:'OpenAI公开模型异常行为和未经授权行动的调查。', kind:'news', path:'base.html', anchor:'research-item-1', date:'2026-08-10'};
  const related = Array.from({length:8}, (_, i) => ({
    title:`OpenAI模型失配事件后续${i + 1}`,
    facts:`OpenAI继续披露模型异常行为调查和事件报告${i + 1}。`,
    kind:'news', path:`r${i + 1}.html`, anchor:'research-item-1', date:`2026-08-0${i + 1}`
  }));
  assert.equal(model.relatedRows(base, [base, ...related], 'news').length, 8);
});

run('agent permissions and interoperability are related but not automatically one timeline', () => {
  const permissions = {title:'智能体越权调用外部应用', facts:'测试发现智能体超出授权权限，调用外部工具。', kind:'news', path:'permissions.html', anchor:'research-item-1', date:'2026-08-01'};
  const interop = {title:'数据智能体互操作规范发布', facts:'数据智能体采用代理协议，规范跨应用互操作。', kind:'news', path:'interop.html', anchor:'research-item-1', date:'2026-08-02'};
  assert.deepEqual(model.detectTopics(permissions).map(t => t.name), ['智能体治理']);
  assert.deepEqual(model.detectTopics(interop).map(t => t.name), ['智能体治理']);
  assert.equal(model.buildTimelines(permissions, [permissions, interop]).length, 0);
  assert.equal(model.buildTimelines(interop, [permissions, interop]).length, 0);
});

run('same event progression forms a timeline', () => {
  const speech = {title:'冯德莱恩提出未满13岁社交媒体禁入', facts:'欧盟提出13岁以下不得使用社交媒体，正式法案尚待提出。', kind:'news', path:'speech.html', anchor:'research-item-1', date:'2026-09-16'};
  const proposal = {title:'欧盟委员会正式提出EU KIDS Act，未满13岁禁止接入社交媒体', facts:'委员会正式采纳EU KIDS Act立法提案，统一最低年龄规则进入立法程序。', kind:'news', path:'proposal.html', anchor:'research-item-1', date:'2026-09-17'};
  const groups = model.buildTimelines(proposal, [speech, proposal]);
  assert.equal(groups.length, 1);
  assert.equal(groups[0].topic, '未成年人上网与年龄核验');
  assert.deepEqual(groups[0].items.map(x => x.path), ['speech.html']);
});

run('same-type enforcement across jurisdictions can form a comparison timeline', () => {
  const cn = {title:'监管部门因违规处理个人信息处罚某平台', facts:'监管部门认定平台未经同意共享个人信息并作出行政处罚。', kind:'news', path:'cn.html', anchor:'research-item-1', date:'2026-09-18'};
  const eu = {title:'European DPA fines retailer for unlawful data sharing', facts:'The authority imposed a GDPR fine for unlawful sharing of personal data.', kind:'news', path:'eu.html', anchor:'research-item-1', date:'2026-09-10'};
  const groups = model.buildTimelines(cn, [eu, cn]);
  assert.equal(groups.length, 1);
  assert.equal(groups[0].topic, '个人信息保护处罚');
  assert.deepEqual(groups[0].items.map(x => x.path), ['eu.html']);
});

run('editorial extrapolation does not create factual topics', () => {
  const item = {title:'数据中心电力接入新规', facts:'当地明确数据中心并网和电力成本程序。', text:'智库选题：AI训练版权与数据出境。', topics:['AI训练与版权','数据跨境']};
  const topics = model.detectTopics(item).map(x => x.name);
  assert(topics.includes('数据中心电力与资源监管'));
  assert(!topics.some(x => /版权|出境/.test(x)));
});

run('English substrings cannot create unrelated topics', () => {
  assert.equal(model.detectTopics({title:'New privacy laws for email systems',facts:'A company explained its guidelines.'}).length, 0);
});

run('index facts exclude research commentary on every news item', () => {
  for (const row of rows.filter(x => x.kind === 'news')) {
    assert(row.facts);
    assert(!/智库选题|论文选题|法治研判/.test(row.facts), row.id);
  }
});

run('timeline groups are narrow, unique, chronological and directly supported', () => {
  for (const item of rows.filter(x => x.kind === 'news')) {
    const groups = model.buildTimelines(item, rows), seen = new Set();
    assert(groups.length <= 2);
    assert.equal(groups.length, new Set(groups.map(g => g.topic)).size);
    for (const group of groups) {
      assert(group.items.length >= 1 && group.items.length <= 4);
      assert(model.detectTopics(item).some(x => x.name === group.topic));
      let previous = '';
      for (const row of group.items) {
        assert.equal(row.kind, 'news');
        assert(!seen.has(model.key(row))); seen.add(model.key(row));
        assert.notEqual(model.key(item), model.key(row));
        assert(row.date >= previous); previous = row.date;
        const signals = model.relationSignals(item, row);
        const rowHasTopic = model.detectTopics(row).some(x => x.name === group.topic);
        // A named instrument/event marker can establish an event-chain relation even
        // when one historical headline uses wording outside the topic dictionary.
        assert(rowHasTopic || signals.markers > 0, `unsupported timeline topic: ${item.title} -> ${row.title}`);
        assert(model.isSeriesTopic(group.topic) || signals.markers > 0 || signals.entities > 0 || signals.title >= .10 || signals.facts >= .12,
          `weak timeline link: ${item.title} -> ${row.title}`);
      }
    }
  }
});

run('related reading never uses generic index topic alone', () => {
  for (const item of rows) {
    for (const kind of ['news','work','paper']) {
      for (const row of model.relatedRows(item, rows, kind)) {
        assert.notEqual(row.materialType, 'book');
        assert(model.directlyRelated(item, row), `weak related link: ${item.title} -> ${row.title}`);
      }
    }
  }
});

run('recommendation entry destinations exist and identify specific items', () => {
  for (const row of rows) {
    assert(fs.existsSync(path.join(__dirname,'..',row.path)), row.path);
    if (row.kind !== 'paper') assert(row.anchor && row.anchor.startsWith('research-item-'));
  }
});
console.log('context regression passed');