#!/usr/bin/env python3
"""Close only the issue for an explicitly verified news edition."""
import json
import subprocess
import sys
from datetime import date
from pathlib import Path

ENDPOINT = "repos/Cyberlawresearch/cyberlaw-research/issues"


def close_verified_issues(result):
    # Defense in depth: a successful job (or a skipped check) is not verification.
    if result.get("status") != "verified":
        return []
    day = result.get("edition_date")
    if not isinstance(day, str) or date.fromisoformat(day).isoformat() != day:
        raise ValueError("A verified edition date is required before closing issues")
    marker = "<!-- daily-release:" + day + " -->"
    pages = json.loads(subprocess.check_output(
        ["gh", "api", "--paginate", "--slurp", ENDPOINT + "?state=open&per_page=100"],
        text=True,
    ))
    closed = []
    for rows in pages:
        for row in rows:
            if "pull_request" not in row and marker in (row.get("body") or ""):
                subprocess.run(
                    ["gh", "api", "--method", "PATCH", ENDPOINT + "/" + str(row["number"]),
                     "-f", "state=closed"], check=True,
                )
                closed.append(row["number"])
                print("Closed verified safeguard issue #" + str(row["number"]) + " for " + day)
    return closed


if __name__ == "__main__":
    close_verified_issues(json.loads(Path(sys.argv[1]).read_text(encoding="utf-8")))
