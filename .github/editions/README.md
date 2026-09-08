# 当期核验记录与自动收尾

本目录只存维护资料，不进入读者页面。`daily-release.yml` 是发布保障，不是具有网页研究能力的内容生成任务；不会尝试读取模型账户或调用付费接口。

## 固定执行

北京时间每天20:17起，每半小时检查一次，至次日00:47；提交正文/核验记录后以及 Pages 每次结束后也检查。00点的兜底检查归属前一天。22点后仍未完成则创建当日唯一的 GitHub Issue 并提及仓库所有者；重复检查更新同一记录。GitHub 通知是否进一步发送邮件取决于账号通知设置，不能承诺 ChatGPT 内消息或邮件一定送达。GitHub cron 也不是严格准点保证。

当前 main 的部署最多三次尝试（原运行加最多两次重试）。禁止重新部署已被 main 超越的旧提交；不强推；部署完成之后还核对线上清单与首页。自动提交后显式 workflow_dispatch Pages，不依赖 GITHUB_TOKEN 的 push 触发另一工作流。未完成或失败时保留最后完整一期。

## 内容任务如何交付

生成任务完成真实来源核验后，将以下记录与四栏最终正文一起提交。日期、路径和时间为当期实值。下面只是格式，不能复制示例即视为完成核验。

```json
{
  "date": "YYYY-MM-DD",
  "pages": {
    "brief": "articles/YYYY-MM-DD-tech-law-brief.html",
    "paper": "articles/YYYY-MM-DD-selected-paper.html",
    "classic": "articles/YYYY-MM-DD-selected-classic.html",
    "newworks": "articles/YYYY-MM-DD-new-works.html"
  },
  "news_count": 18,
  "newworks_count": 5,
  "review": {
    "status": "verified",
    "checked_at": "YYYY-MM-DDTHH:MM:SS+08:00",
    "last_news_scan_at": "YYYY-MM-DDTHH:MM:SS+08:00",
    "checks": {
      "sources": true,
      "legal_status": true,
      "bibliography": true,
      "deduplication": true,
      "original_titles": true
    },
    "sha256": {
      "每一个正文的完整相对路径": "该文件UTF-8字节的SHA-256；四项缺一不可"
    },
    "news_event_times": {
      "research-item-1": "来源明确的新进展时间，ISO 8601含时区；覆盖每条新闻"
    }
  }
}
```

记录命名为 `.github/editions/YYYY-MM-DD.json`；`pages` 按示例顺序。来源核验、法律状态、书目、全部历史去重、外文原题必须全部实际检查，未检查不能填 true。程序仅验证记录完整性、正文未被更换、新闻时窗和网页结构，不会判定论述事实真伪。

保留标准 `.brief-item`、`.brief-fact`、`.brief-meta`、`.source`、`.work-reading` 及 `data-citation`、`data-event-date`。具体门槛由 `scripts/edition_gate.py` 执行，不要通过删除或弱化验收测试来发布。

## 状态与安全

- `delivered=true`：当前 main 对应 Pages 已成功，并已核对线上清单、首页四卡片及导航；正文/归档的严格验收由 Pages 的 edition gate 执行。
- `pending`：等内容核验、推送部署出现或部署正在进行，不是上线成功。
- `failed`：内容不齐/未核验超过截止时间、部署超过重试上限或运行本身失败。维护信息仅写入 Actions/Issue，不能添加到网页。

改动仅限当期四篇正文的导航、首页、总归档、四类历史入口和本期清单。不会更改账户、收藏和笔记。通过临时目录先验证再复制，推送冲突时停止，下一次从最新 main 重新运行；不使用 force。

当前已发布基线为9月8日，不补造该期核验记录。今后的候选记录只能由真正执行了来源核验的内容任务提交。
