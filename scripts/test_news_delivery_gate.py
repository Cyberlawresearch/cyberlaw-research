#!/usr/bin/env python3
"""Regression tests: fact-only editions must not fail analysis-only checks."""
import json
import os
from datetime import datetime
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch
from zoneinfo import ZoneInfo

from news_delivery_gate import FACT_CHECKS, check, main as run_check, verify
from close_daily_release_issue import close_verified_issues


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
            "date": "2026-10-10",
            "column": "brief",
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
        # Explicit results drive issue closure, including delayed scheduled jobs.
        assert check(root, datetime(2026, 10, 10, 22, 0, tzinfo=tz))["status"] == "verified"
        assert check(root, datetime(2026, 10, 11, 0, 59, tzinfo=tz))["edition_date"] == "2026-10-10"
        for stamp in ("2026-10-10T21:59:00", "2026-10-11T01:00:00", "2026-10-11T03:29:00"):
            skipped = check(root, datetime.fromisoformat(stamp).replace(tzinfo=tz))
            assert skipped["status"] == "skipped" and skipped["edition_date"] is None
        daytime = datetime(2026, 10, 11, 10, 0, tzinfo=tz)
        assert check(root, daytime, "2026-10-10")["status"] == "verified"
        try:
            check(root, daytime, "2026-10-09")
        except AssertionError as exc:
            assert "brief not published for 2026-10-09" in str(exc)
        else:
            raise AssertionError("An unrelated edition was accepted by explicit recheck")
        report = root / "result.json"
        outputs = root / "outputs.txt"
        with patch.dict(os.environ, {"GITHUB_OUTPUT": str(outputs)}):
            run_check(["--result", str(report)], root=root, now=after_midnight)
            assert "status=verified\nedition_date=2026-10-10\n" in outputs.read_text()
            outputs.write_text("")
            run_check(["--result", str(report)], root=root, now=daytime)
            assert json.loads(report.read_text())["status"] == "skipped"
            assert outputs.read_text() == "status=skipped\nedition_date=\n"
        record["date"] = "2026-10-09"
        record_path.write_text(json.dumps(record), encoding="utf-8")
        expect_failure(root, evening, "date does not match")
        record["date"] = "2026-10-10"
        record["checks"]["sources"] = False
        record_path.write_text(json.dumps(record), encoding="utf-8")
        expect_failure(root, evening, "sources")
        # A previous successful JSON report must be replaced on failure.
        report.write_text('{"status":"verified","edition_date":"2026-10-10"}')
        outputs.write_text("")
        with patch.dict(os.environ, {"GITHUB_OUTPUT": str(outputs)}):
            try:
                run_check(["--edition-date", "2026-10-10", "--result", str(report)], root=root, now=daytime)
            except AssertionError:
                pass
            else:
                raise AssertionError("invalid recheck unexpectedly passed")
        assert json.loads(report.read_text())["status"] == "failed"
        assert outputs.read_text() == "status=failed\nedition_date=\n"
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
        record["domestic_source_coverage"] = [{"source_group": "same", "status": "checked"}] * 7
        record_path.write_text(json.dumps(record), encoding="utf-8")
        expect_failure(root, evening, "duplicate domestic")
        record["domestic_source_coverage"] = [
            {"source_group": f"group {i}", "status": "checked"} for i in range(7)
        ]
        record["domestic_source_coverage"][0]["status"] = "searched"
        record_path.write_text(json.dumps(record), encoding="utf-8")
        expect_failure(root, evening, "invalid domestic source")
        record["domestic_source_coverage"][0]["status"] = "inaccessible"
        record_path.write_text(json.dumps(record), encoding="utf-8")
        expect_failure(root, evening, "follow-up notes")
        record["domestic_source_coverage"][0]["notes"] = "Retry this source through an available official entry point."
        record_path.write_text(json.dumps(record), encoding="utf-8")
        assert check(root, evening)["status"] == "verified"

    # No API call, let alone a PATCH, may follow skipped/failed/missing evidence.
    with patch("close_daily_release_issue.subprocess.check_output") as read, patch("close_daily_release_issue.subprocess.run") as write:
        for result in ({}, {"status": "skipped"}, {"status": "failed"}, {"status": "success"}):
            assert close_verified_issues(result) == []
        read.assert_not_called()
        write.assert_not_called()
        for day in (None, "20261010", "2026-10-10\n"):
            try:
                close_verified_issues({"status": "verified", "edition_date": day})
            except ValueError:
                pass
            else:
                raise AssertionError("invalid issue date accepted")
        read.assert_not_called()
        write.assert_not_called()
        read.return_value = json.dumps([
            [{"number": 1, "body": "<!-- daily-release:2026-10-11 -->"}],
            [{"number": 2, "body": "<!-- daily-release:2026-10-10 -->"},
             {"number": 3, "body": "<!-- daily-release:2026-10-10 -->", "pull_request": {}}],
        ])
        assert close_verified_issues({"status": "verified", "edition_date": "2026-10-10"}) == [2]
        assert write.call_count == 1 and write.call_args.args[0][-3:] == ["repos/Cyberlawresearch/cyberlaw-research/issues/2", "-f", "state=closed"]

    workflow = (Path(__file__).resolve().parents[1] / ".github/workflows/daily-release.yml").read_text()
    closure_step = workflow.split("- name: Close resolved safeguard issue", 1)[1].split("- name:", 1)[0]
    assert "if: success() && steps.news_delivery.outputs.status == 'verified'" in closure_step
    assert 'close_daily_release_issue.py "$RUNNER_TEMP/release-check/news-delivery.json"' in closure_step
    assert "datetime.now" not in closure_step
    print("news_delivery_gate: fact checks, time boundaries, explicit rechecks, failure outputs and issue-closure regressions passed")


if __name__ == "__main__":
    main()
