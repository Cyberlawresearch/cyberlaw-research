# 当期核验记录与自动收尾

本目录只存维护资料，不进入读者页面。四个研究栏目独立研究、独立核验、独立发布；任一栏目完成后，不等待其他栏目，也不得借机改写其他栏目。 `daily-release.yml` 只负责发布保障和逾期检查，不代替内容研究、来源核验或法律判断。

## current-edition 的独立栏目规则

`data/current-edition.json` 保存四栏各自最新已发布页面：

- `pages.<column>`：该栏最新正文路径；
- `page_dates.<column>`：该栏最新正文日期；
- `news_count`、`newworks_count`：对应栏目的当前数量；
- 顶层 `date`：始终等于四个 `page_dates` 中的最大日期。

因此，某一栏目单独推进时，只修改该栏自己的 `pages/page_dates` 和对应计数字段；顶层 `date` 作为派生字段同步更新为四栏最新日期。其他栏目的正文、入口、日期和计数保持原样。不得因为其他栏目尚未更新而阻塞已经核验完成的栏目。

## 新闻栏核验记录

新闻栏完成真实来源核验后，提交 `.github/editions/YYYY-MM-DD.news.json`。记录必须反映本次实际检查结果，不得复制旧记录或把未检查项目写成 true。基本格式如下：

```json
{
  "date": "YYYY-MM-DD",
  "column": "brief",
  "state": "verified",
  "page": "articles/YYYY-MM-DD-tech-law-brief.html",
  "news_count": 18,
  "distribution": {
    "domestic": 6,
    "foreign": 12
  },
  "checked_at": "YYYY-MM-DDTHH:MM:SS+08:00",
  "last_news_scan_at": "YYYY-MM-DDTHH:MM:SS+08:00",
  "checks": {
    "sources": true,
    "legal_status": true,
    "original_titles": true,
    "timeliness": true,
    "previous_day_event_deduplication": true,
    "seven_day_history_deduplication": true,
    "local_language_scan_korea_japan_vietnam": true,
    "prior_background_checked": true,
    "natural_chinese_reviewed": true,
    "background_outlook": true,
    "foreign_layout": true
  }
}
```

可继续保存去重说明、来源巡视记录、最终窗口复扫、背景与语言检查等字段。程序只验证记录和页面结构是否满足门槛，不会替代对事实真伪、法律状态和外文原题的人工研究核验。

新闻正文继续保留标准 `.brief-item`、`.brief-fact`、`.brief-meta`、`.source`、`data-citation`、`data-event-date` 以及结构化 `brief-insight`。72小时时效、18—20条门槛、外文原题、事件级去重和其他内容要求以 `AGENTS.md`、`BRIEF_STRUCTURE.md` 及现行脚本为准，不通过删除或弱化验收测试来发布。

## 发布保障

北京时间20:17起，仓库发布保障按计划检查独立栏目结构；22:00以后额外检查当天新闻栏是否已经存在、是否有 verified 的 `.news.json` 记录，并在失败时通过 GitHub Issue 报告。00点的兜底检查仍归属前一天。

Pages 部署成功后还要核对 current-columns、当期入口和阅读功能。只有对应 main 提交已经部署成功，而且线上验收通过，才能称为“已发布”。提交成功、pending 或仅有草稿都不等于上线成功。

推送冲突时从最新 main 重新读取并合并，不强推。任何单次来源访问、写入、校验或部署失败都不得自行关闭长期内容任务。
