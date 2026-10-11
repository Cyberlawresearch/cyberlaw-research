#!/usr/bin/env python3
"""Offline smoke tests for JSON-to-HTML news publication.

All news examples are synthetic fixtures, never marked as real research.
"""
from __future__ import annotations

import copy
import json
import shutil
from datetime import datetime, timedelta
from pathlib import Path
from tempfile import TemporaryDirectory
from zoneinfo import ZoneInfo

from bs4 import BeautifulSoup
from publish_news_from_draft import publish, FACT_CHECKS, load, verify

ROOT = Path(__file__).resolve().parents[1]
TZ = ZoneInfo("Asia/Shanghai")
RUN_TIME = datetime(2026, 10, 11, 20, 30, tzinfo=TZ)
DAY = RUN_TIME.date().isoformat()


def synthetic_draft():
    items = []
    for i in range(1, 12):
        items.append({
            "id": f"research-item-{i}",
            "domestic": i <= 4,
            "date": DAY,
            "jurisdiction": "中国" if i <= 4 else "测试法域",
            "agency": "虚拟测试机构",
            "title": f"示例科技法新闻标题{i}",
            "original_title": f"Fictional News Item {i}",
            "source_name": "Synthetic source",
            "url": f"https://example.org/test-news/item-{i}",
            "fact": "这是一段专门用于验证页面排版、元数据保存和新闻条数检查的模拟报道文字，不代表任何真实新闻、政策发布、行政调查或司法裁判。该段文字不会进入正式新闻简报。",
            "status": "verified",
        })
    return {
        "date": DAY,
        "column": "brief",
        "state": "draft",
        "publication_ready": True,
        "last_news_scan_at": RUN_TIME.isoformat(),
        "checked_at": RUN_TIME.isoformat(),
        "news_count": len(items),
        "distribution": {"domestic": 4, "foreign": 7},
        "checks": {name: True for name in FACT_CHECKS},
        "coverage": [{
            "source_group": f"test group {i}",
            "source_name": "Synthetic fixture",
            "checked_at": RUN_TIME.isoformat(),
            "status": "checked",
            "found": 0,
            "notes": "Tests only",
        } for i in range(7)],
        "items": items,
    }


def expect_failure(root, draft, excerpt):
    try:
        verify(root, draft, RUN_TIME)
    except ValueError as e:
        assert excerpt in str(e), f"unexpected validation error: {e}"
    else:
        raise AssertionError("expected failure for: " + excerpt)


def main():
    with TemporaryDirectory() as directory:
        root = Path(directory)
        old_manifest = load(ROOT / "data/current-edition.json")
        assert old_manifest["page_dates"]["brief"] < DAY, "Test requires previous published news"
        paths = ["index.html", "briefs.html", "archive.html",
                 "data/current-edition.json", old_manifest["pages"]["brief"]]
        for path in paths:
            target = root / path
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(ROOT / path, target)
        old_home = (root / "index.html").read_text(encoding="utf-8")
        old_manifest_copy = copy.deepcopy(old_manifest)
        data = synthetic_draft()

        incomplete = copy.deepcopy(data)
        incomplete["publication_ready"] = False
        expect_failure(root, incomplete, "publication_ready")
        incomplete = copy.deepcopy(data)
        incomplete["checks"]["sources"] = False
        expect_failure(root, incomplete, "Factual verification")
        incomplete = copy.deepcopy(data)
        incomplete["last_news_scan_at"] = (RUN_TIME - timedelta(hours=4)).isoformat()
        expect_failure(root, incomplete, "older than two hours")
        incomplete = copy.deepcopy(data)
        incomplete["coverage"] = incomplete["coverage"][:6]
        expect_failure(root, incomplete, "Seven domestic source")
        incomplete = copy.deepcopy(data)
        incomplete["items"][0]["url"] = "http://example.org/unsafe"
        expect_failure(root, incomplete, "HTTPS")
        incomplete = copy.deepcopy(data)
        incomplete["items"][0]["date"] = "2026-10-08"
        expect_failure(root, incomplete, "72-hour window")

        result = publish(root, data, RUN_TIME)
        assert result["status"] == "prepared", result
        assert result["count"] == 11 and result["domestic"] == 4, result
        latest = load(root / "data/current-edition.json")
        assert latest["pages"]["brief"] == f"articles/{DAY}-tech-law-brief.html"
        assert latest["news_count"] == 11
        for name in ("paper", "classic", "newworks"):
            assert latest["pages"][name] == old_manifest_copy["pages"][name]
            assert latest["page_dates"][name] == old_manifest_copy["page_dates"][name]

        html = BeautifulSoup((root / latest["pages"]["brief"]).read_text(encoding="utf-8"),
                             "html.parser")
        articles = html.select(".brief-item")
        assert len(articles) == 11
        assert len([a for a in articles if a.find("p", class_="brief-original")]) == 7
        for i, article in enumerate(articles, 1):
            assert article["id"] == f"research-item-{i}"
            assert len(article.select("p.analysis-pending")) == 3
            assert json.loads(article.select_one("script.brief-insight").string) == {
                "background": "", "outlook": "",
            }
            assert article.select_one(".source a")["href"] == data["items"][i-1]["url"]
        record = load(root / ".github/editions" / f"{DAY}.news.json")
        assert record["state"] == "verified"
        assert record["analysis_pending"] and record["publication"]["pages_status"] == "awaiting_deployment"
        assert len(record["domestic_source_coverage"]) == 7

        home = BeautifulSoup((root / "index.html").read_text(encoding="utf-8"), "html.parser")
        before = BeautifulSoup(old_home, "html.parser")
        for name in ("paper", "classic", "newworks"):
            assert str(home.select_one(f'[data-daily-column="{name}"]')) == str(
                before.select_one(f'[data-daily-column="{name}"]')
            ), f"Other column changed: {name}"
        assert home.select_one('[data-daily-column="brief"]')["href"] == latest["pages"]["brief"]
        history = BeautifulSoup((root / "briefs.html").read_text(encoding="utf-8"), "html.parser")
        assert history.select_one(".issue-row .issue-action")["href"] == latest["pages"]["brief"]

        # A second identical run never rewrites the same published edition.
        assert publish(root, data, RUN_TIME)["status"] == "already_published"
    print("Structured news release: 8 negative/positive checks and idempotence passed.")


if __name__ == "__main__":
    main()
