# 网信法研究每日推送

每日四个研究栏目包括全球科技法简报、域外法学论文精读、法学经典著作和科技法研究新作；另有独立的“网信法技术基础”教学序列。

执行内容更新前，先阅读 [AGENTS.md](AGENTS.md)、[BRIEF_STRUCTURE.md](BRIEF_STRUCTURE.md) 与 [.github/editions/README.md](.github/editions/README.md)，并读取最新 main、`data/current-edition.json` 和对应栏目历史。四栏独立研究、独立核验、独立发布，不以同日四栏全部完成作为单栏发布前提。

## 发布与中断恢复

- `data/current-edition.json`：保存四栏各自最新页面和日期；顶层 `date` 始终等于四个 `page_dates` 中的最大日期。
- `.github/editions/YYYY-MM-DD.news.json`：新闻栏真实核验记录；其他栏目按现行仓库规范保存各自核验信息。
- `.github/workflows/daily-release.yml`：独立栏目结构检查、新闻逾期检查和异常报告。
- `scripts/current_columns_gate.py`：独立栏目当前指针、首页入口、历史列表和新闻基本门槛验收。
- `.github/workflows/pages.yml`：Pages部署及部署前后阅读功能、current-columns验收。
- `.github/workflows/reader-regression.yml`：独立的阅读功能测评。

某一栏目完成后，只推进该栏自己的正文、首页入口、历史列表、`pages/page_dates` 和对应计数字段；同步把顶层 `date` 更新为四栏日期最大值。其他栏保持原样。中断后从最新 main 续作，不把旧草稿、旧成功报告或仅有GitHub工作流绿灯当作内容已经完成的证据。

“每日推送发布保障”和 Pages 工作流只能证明技术结构与部署状态，不能代替网页研究、法律状态核验、书目核验、事件级去重和内容判断。

## 经典解读规范

[PROMPT.md](PROMPT.md) 保留经典著作解读的详细要求：核对原著与版本，展开全书结构、主要观点、影响、代表性争议与误读。不要混用初版、修订版或译本，不编造引文页码，不将二手概括冒充作者原话，不将后来概念倒写给早期作者。

所有既有正文、有效来源与用户收藏笔记继续保留。维护报告不进入读者页面。
