# 新闻后置分析结构化数据

后置分析不再直接替换整份新闻 HTML。每期分析保存在：

```text
.github/editions/analysis/YYYY-MM-DD/
```

目录内包含：

- `_meta.json`：整期状态与目标页面；
- `01.json`、`02.json`……：每条新闻的分析数据。

只有 `_meta.json` 的 `state` 为 `completed` 时，Pages 构建脚本才会把该目录的数据注入对应新闻页面。条目不完整、数量不一致、ID 不匹配或字段为空时，构建必须失败，不得静默发布半成品。

## `_meta.json`

```json
{
  "date": "2026-10-09",
  "page": "articles/2026-10-09-tech-law-brief.html",
  "expected_count": 11,
  "state": "completed"
}
```

研究过程中先使用 `state: draft`。全部条目写入并逐条回读后，最后才改为 `completed`。

## 单条分析文件

```json
{
  "id": "research-item-1",
  "legal_analysis": "法治研判正文",
  "think_tank": "智库选题题目及说明",
  "paper_topic": "论文选题题目及说明",
  "background": "经核验的前序背景",
  "outlook": "使用条件表达的未来前瞻"
}
```

文件名按页面顺序使用两位数字。每个文件只对应一条新闻，便于单独定位写入失败，不得在一个条目中夹带其他条目的内容。

## 发布流程

1. 从最新 `main` 建立唯一分析发布分支；
2. 先创建 `_meta.json`，状态为 `draft`；
3. 逐条写入分析文件，每次写入后立即回读；
4. 更新当日 `.news.json` 中的分析进度，但不提前标记完成；
5. 全部条目通过后，将 `_meta.json` 改为 `completed`，并将 `.news.json` 的分析状态改为 `completed`；
6. 重新核对最新 `main`，无并发变化时非强制 fast-forward；有变化时从最新 `main` 重建分支并叠加分析数据；
7. Pages 构建时由 `scripts/apply_structured_news_analysis.py` 注入正文并执行页面验收。

任何单条失败不得关闭长期任务。应记录真实工具、分支、路径和错误文本；合法、必要的分析内容不得因猜测触发原因而批量删除。网络安全条目只分析责任、监管、程序和风险分配，不写可执行攻击方法。
