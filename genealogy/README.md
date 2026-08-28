# 法律概念谱系｜Legal Concept Genealogy

这是 `cyberlaw-research` 下的个人研究辅助项目。第一期主题为：

> **平台权力 / Platform Power**

目标不是建立普通文献列表，而是逐步重建法律概念的形成、传播、翻译、继承、分化、批判与制度化过程。

## 当前目录

- `data/works.seed.jsonl`：网上公开检索并核实的第一批中外文献元数据。
- `data/concept-relations.seed.jsonl`：从标题、摘要或公开正文中提取的“候选概念关系”。
- `reports/seed-corpus-2026-08-28.md`：第一轮抓取说明和初步研究观察。

## 数据原则

1. **不把检索结果等同于概念史事实。**
2. `abstract_verified` 仅表示关系可由摘要明确支持；并不自动证明跨文献的思想继承。
3. `unverified` 表示机器/研究者发现的候选关系，后续必须结合全文、参考文献和页码核验。
4. 对“首次提出”“源自”“继承”“翻译自”等强谱系命题，必须有直接引文或明确引证证据。
5. GitHub 当前只存元数据、来源链接和研究性归纳，不批量转载受版权保护的论文全文。
6. 可合法公开获取的全文只记录来源/许可状态；个人合法取得的 PDF 由本地语料库处理，不直接提交到公开仓库。

## 后续与本地语料合并

本地 Codex 处理 PDF 后，可将以下数据并入本项目：

- `works.jsonl`
- `references.jsonl`
- `concepts.jsonl`
- 页码级证据

合并时以 DOI、标题、作者、年份和文件哈希去重，并优先保留能够回溯至原文页码的证据。

## 第一阶段概念簇

中文候选：
`平台权力`、`数字平台权力`、`平台私权力`、`超级平台私权力`、`数字权力`、`算法权力`、`基础设施平台权力`。

英文候选：
`platform power`、`digital gatekeeper`、`private power`、`private governance`、`platform governance`、`digital constitutionalism`、`infrastructural power`。

后续将继续扩展检索、补齐 DOI/开放全文状态、抓取参考文献网络，并生成可人工核验的概念谱系图。
