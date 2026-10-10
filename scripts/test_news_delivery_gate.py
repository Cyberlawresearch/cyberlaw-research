#!/usr/bin/env python3
"""Regression tests: fact-only editions must not fail analysis-only checks."""
import json
from datetime import datetime
from pathlib import Path
from tempfile import TemporaryDirectory
from zoneinfo import ZoneInfo

from news_delivery_gate import FACT_CHECKS, verify


def expect_failure(root, now, substring):
    try:
        verify(root, now)
    except AssertionError as exc:
        assert substring in str(exc), str(exc)
    else:
        raise AssertionError("expected a validation failure: " + substring)


def main():
    tz = ZoneInfo("Asia/Shanghai")
    evening = datetime(2026, 10, 10, 23, 15, tzinfo=tz)
    after_midnight = datetime(2026, 10, 11, 0, 30, tzinfo=tz)
    with TemporaryDirectory() as directory:
        root = Path(directory)
        (root / "data").mkdir()
        (root / ".github/editions").mkdir(parents=True)
        (root / "articles").mkdir()
        manifest = {
            "date": "2026-10-10",
            "page_dates": {
                "brief": "2026-10-10", "paper": "2026-10-10",
                "classic": "2026-10-09", "newworks": "2026-10-10",
            },
            "pages": {"brief": "articles/2026-10-10-tech-law-brief.html"},
            "news_count": 13,
        }
        manifest_path = root / "data/current-edition.json"
        manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
        page = root / manifest["pages"]["brief"]
        page.write_text(
            "<html>" + "<article class='brief-item'></article>" * 13 + "</html>",
            encoding="utf-8",
        )
        record = {
            "state": "verified",
            "mode": "fact_only",
            "analysis_pending": True,
            "analysis": {"status": "pending"},
            "page": manifest["pages"]["brief"],
            "news_count": 13,
            "checks": {field: True for field in FACT_CHECKS},
            "domestic_source_coverage": [
                {"source_group": f"group {i}", "status": "checked"} for i in range(7)
            ],
        }
        record_path = root / ".github/editions/2026-10-10.news.json"
        record_path.write_text(json.dumps(record), encoding="utf-8")

        # Current published fact-only edition passes despite missing research fields.
        assert "verified" in verify(root, evening)
        assert "verified" in verify(root, after_midnight)
        assert "skipped" in verify(root, datetime(2026, 10, 10, 21, 0, tzinfo=tz))
        record["checks"]["sources"] = False
        record_path.write_text(json.dumps(record), encoding="utf-8")
        expect_failure(root, evening, "sources")
        record["checks"]["sources"] = True
        record_path.write_text(json.dumps(record), encoding="utf-8")
        page.write_text("<html><article class='brief-item'></article></html>", encoding="utf-8")
        expect_failure(root, evening, "HTML item count")
        page.write_text(
            "<html>" + "<article class='brief-item'></article>" * 13 + "</html>",
            encoding="utf-8",
        )
        record["domestic_source_coverage"] = record["domestic_source_coverage"][:5]
        record_path.write_text(json.dumps(record), encoding="utf-8")
        expect_failure(root, evening, "domestic media group")
    print("news_delivery_gate: all 7 positive/negative cases passed")


if __name__ == "__main__":
    main()
