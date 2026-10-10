#!/usr/bin/env python3
"""Check completed daily news facts without requiring later research analysis."""
from __future__ import annotations

import json
from datetime import datetime, timedelta
from html.parser import HTMLParser
from pathlib import Path
from zoneinfo import ZoneInfo

ZONE = ZoneInfo("Asia/Shanghai")
FACT_CHECKS = (
    "sources",
    "legal_status",
    "original_titles",
    "timeliness",
    "previous_day_event_deduplication",
    "seven_day_history_deduplication",
    "natural_chinese_reviewed",
    "foreign_layout",
    "domestic_major_omission_review",
)


class BriefItemCounter(HTMLParser):
    def __init__(self):
        super().__init__()
        self.count = 0

    def handle_starttag(self, tag, attrs):
        if tag != "article":
            return
        attributes = dict(attrs)
        if "brief-item" in (attributes.get("class") or "").split():
            self.count += 1


def verify(root: Path, now: datetime) -> str:
    local = now.astimezone(ZONE)
    if not (local.hour >= 22 or local.hour < 1):
        return "News deadline check skipped before 22:00 Asia/Shanghai."

    # Between 00:00 and 00:59, verify the evening edition just ended.
    day = (local - timedelta(hours=12)).date().isoformat()
    manifest = json.loads((root / "data/current-edition.json").read_text(encoding="utf-8"))
    assert manifest["date"] == max(manifest["page_dates"].values()), "manifest top-level date is not max(page_dates)"
    assert manifest["page_dates"]["brief"] == day, (
        f'brief not published for {day}: {manifest["page_dates"]["brief"]}'
    )
    page_path = Path(manifest["pages"]["brief"])
    assert not page_path.is_absolute() and ".." not in page_path.parts, "unsafe news page path"
    page = root / page_path
    assert page.is_file() and day in page.name, f"brief page missing or wrong date: {page_path}"

    record_path = root / ".github/editions" / f"{day}.news.json"
    assert record_path.is_file(), f"missing news verification record: {record_path}"
    record = json.loads(record_path.read_text(encoding="utf-8"))
    assert record.get("state") == "verified", "news verification state is not verified"
    assert record.get("page") == str(page_path), "news verification page does not match current brief"
    assert record.get("news_count") == manifest["news_count"], "news count mismatch between record and manifest"
    assert record["news_count"] >= 10, "verified news count below the minimum of 10"

    counter = BriefItemCounter()
    counter.feed(page.read_text(encoding="utf-8"))
    assert counter.count == record["news_count"], (
        f"HTML item count {counter.count} differs from record count {record['news_count']}"
    )

    checks = record.get("checks", {})
    missing = [name for name in FACT_CHECKS if checks.get(name) is not True]
    assert not missing, "news fact verification checks incomplete: " + ", ".join(missing)
    coverage = record.get("domestic_source_coverage") or []
    assert len(coverage) >= 7, "domestic media group coverage missing or incomplete"
    for item in coverage:
        assert item.get("status") in ("checked", "no_new", "inaccessible"), (
            "invalid domestic source coverage status: " + str(item.get("source_group"))
        )
        if item["status"] == "inaccessible":
            assert item.get("notes"), "inaccessible source requires follow-up notes"

    # Background, legal analysis, paper topics and outlook are written by a
    # separate later task. Missing analysis is not a failed FACT publication.
    analysis = record.get("analysis") or {}
    pending = record.get("analysis_pending") is True or analysis.get("status") == "pending"
    status = "analysis pending" if pending else "analysis tracked separately"
    return (
        f'News factual edition verified for {day}: {page_path} '
        f'({record["news_count"]} items; {status}).'
    )


if __name__ == "__main__":
    print(verify(Path.cwd(), datetime.now(ZONE)))
