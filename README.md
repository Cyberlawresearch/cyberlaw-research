# 网信法研究每日推送

每日四栏包括全球科技法简报、域外法学论文精读、法学经典著作和科技法研究新作。

执行内容更新前，先阅读 [AGENTS.md](AGENTS.md)、[BRIEF_STRUCTURE.md](BRIEF_STRUCTURE.md) 与 [.github/editions/README.md](.github/editions/README.md)。核验完成后统一交付四栏正文和摘要绑定的核验记录，不能停留在部分文件已提交。

## 发布与中断恢复

- `data/current-edition.json`：最后完整一期的声明；首页及历史入口必须与其一致。
- `.github/editions/YYYY-MM-DD.json`：内容生成者真实核验后的候选记录。
- `.github/workflows/daily-release.yml`：定时收尾、部署重试及逾期告警。
- `scripts/edition_gate.py`：整期正文、首页、归档与实际部署验收。
- `.github/workflows/reader-regression.yml`：独立的21:30阅读功能测评，保持原任务。

“每日推送发布保障”只承担技术发布，不能代替网页研究、法律状态核验、书目核验，也不能代表外部 ChatGPT 定时内容任务已经修改。原有内容生成任务需按照 AGENTS.md 交付真实核验记录。

## 经典解读规范

[PROMPT.md](PROMPT.md) 保留经典著作解读的详细要求：核对原著与版本，展开全书结构、主要观点、影响、代表性争议与误读。不要混用初版、修订版或译本，不编造引文页码，不将二手概括冒充作者原话，不将后来概念倒写给早期作者。

所有既有正文、有效来源与用户收藏笔记继续保留。维护报告不进入读者页面。
