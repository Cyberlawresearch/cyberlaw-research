#!/usr/bin/env python3
"""Publish one fact-only brief from an explicitly verified draft JSON.

This script is deliberately deterministic and performs no news discovery.
It never touches paper/classic/newworks, trade-watch or tech-basics content.
GitHub Actions runs this on a disposable checkout before a single main push.
"""
from __future__ import annotations

import argparse
import copy
import json
import re
from datetime import date, datetime, timedelta
from pathlib import Path
from urllib.parse import urlparse
from zoneinfo import ZoneInfo

from bs4 import BeautifulSoup

TZ = ZoneInfo("Asia/Shanghai")
ROOT = Path(__file__).resolve().parents[1]
FACT_CHECKS = (
    "sources", "legal_status", "original_titles", "timeliness",
    "previous_day_event_deduplication", "seven_day_history_deduplication",
    "domestic_major_omission_review", "natural_chinese_reviewed",
    "foreign_layout",
)
ANALYSIS_LABELS = ("法治研判：", "智库选题参考：", "论文选题：")
ANALYSIS_HIDE = "visibility:hidden;height:1px;min-height:0;margin:0;padding:0;border:0;overflow:hidden"
OUTPUT_FILES = ("index.html", "briefs.html", "archive.html", "data/current-edition.json")


def demand(condition, explanation):
    if not condition:
        raise ValueError(explanation)


def load(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def save(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(value, encoding="utf-8")


def text(node, name):
    demand(node is not None, "Missing HTML element: " + name)
    return node


def soup(path):
    return BeautifulSoup(path.read_text(encoding="utf-8"), "html.parser")


def new_child(doc, parent, tag, label=None, css_class=None, **attrs):
    node = doc.new_tag(tag, **attrs)
    if css_class:
        node["class"] = css_class
    if label is not None:
        node.string = str(label)
    parent.append(node)
    return node


def verify(root, draft, now, *, backfill=False):
    now = now.astimezone(TZ)
    day = str(draft.get("date") or "")
    demand(re.fullmatch(r"\d{4}-\d{2}-\d{2}", day), "Invalid issue date")
    issue_date = date.fromisoformat(day)
    if backfill:
        demand(draft.get("backfill_authorized") is True, "Historical backfill not authorized")
        demand(draft.get("backfill_issue_date") == day and draft.get("backfill_reviewed_at"),
               "Missing historical backfill review")
        demand(0 < (now.date() - issue_date).days <= 2,
               "Backfill limited to the preceding two dates")
    else:
        demand(day == now.date().isoformat(), "Draft must match today's Shanghai date")
    demand(draft.get("column") == "brief", "Only the news column is eligible")
    demand(draft.get("publication_ready") is True, "Draft not publication_ready")
    demand(draft.get("state") in ("draft", "verified"), "Invalid draft state")
    checks = draft.get("checks") or {}
    demand(all(checks.get(field) is True for field in FACT_CHECKS),
           "Factual verification incomplete: " + ", ".join(k for k in FACT_CHECKS if checks.get(k) is not True))
    scan = draft.get("last_news_scan_at")
    demand(isinstance(scan, str) and scan, "Missing final news scan timestamp")
    try:
        scan_time = datetime.fromisoformat(scan)
    except ValueError as err:
        raise ValueError("Invalid final scan timestamp") from err
    demand(scan_time.tzinfo is not None, "Final scan timestamp needs timezone")
    demand(timedelta(0) <= now - scan_time.astimezone(TZ) <= timedelta(hours=2),
           "Final news scan older than two hours; recheck sources before release")
    coverage = draft.get("coverage") or draft.get("domestic_source_coverage") or []
    demand(isinstance(coverage, list) and len(coverage) >= 7,
           "Seven domestic source groups required")
    for entry in coverage:
        demand(entry.get("source_group") and entry.get("source_name") and entry.get("checked_at"),
               "Incomplete domestic source coverage entry")
        demand(entry.get("status") in ("checked", "no_new", "inaccessible"),
               "Invalid coverage status")
        if entry["status"] == "inaccessible":
            demand(entry.get("notes"), "Inaccessible sources require follow-up notes")
    items = draft.get("items")
    demand(isinstance(items, list) and len(items) >= 10, "At least 10 verified news items required")
    demand(len(items) == draft.get("news_count"), "Draft count does not match items")
    seen_urls = set()
    domestic = 0
    for i, item in enumerate(items, 1):
        for key in ("date", "jurisdiction", "agency", "title", "original_title",
                    "source_name", "url", "fact"):
            demand(isinstance(item.get(key), str) and item[key].strip(),
                   f"Missing {key} in news item {i}")
        demand(item.get("status") not in ("excluded", "rejected", "blocked"),
               f"Excluded item in ready edition: {i}")
        demand(item.get("id") == f"research-item-{i}",
               f"News ids must be sequential and stable: item {i}")
        url = item["url"].strip()
        parts = urlparse(url)
        demand(parts.scheme == "https" and parts.netloc and not parts.username,
               f"Source is not a valid HTTPS URL: item {i}")
        demand(url not in seen_urls, f"Repeated source URL in issue: {i}")
        seen_urls.add(url)
        demand(len(item["fact"].strip()) >= 65, f"Fact paragraph too short: item {i}")
        try:
            event_day = date.fromisoformat(item["date"])
        except ValueError as err:
            raise ValueError(f"Invalid event date: {i}") from err
        # Dates with no verified hour/minute are checked conservatively.
        demand(0 <= (issue_date - event_day).days <= 2,
               f"Event outside conservative 72-hour window: {i}")
        domestic += item.get("domestic") is True
    demand(domestic == (draft.get("distribution") or {}).get("domestic"),
           "Draft domestic count disagrees with items")
    demand(len(items) - domestic == (draft.get("distribution") or {}).get("foreign"),
           "Draft foreign count disagrees with items")

    current = load(root / "data/current-edition.json")
    demand(current["date"] == max(current["page_dates"].values()),
           "Existing manifest date mismatch")
    published = current["page_dates"]["brief"]
    demand(published <= day, "Cannot overwrite a newer edition")
    if published == day:
        record = root / ".github" / "editions" / f"{day}.news.json"
        demand(record.exists() and load(record).get("state") == "verified",
               "Today's current brief is not verified; manual recovery required")
        return day, items, coverage, current, True
    demand(published < day, "News must advance dates")

    # URL-level duplicate check; editorial event-level dedup remains mandatory
    # in the draft before publication_ready may be set.
    for offset in range(1, 8):
        former = (issue_date - timedelta(days=offset)).isoformat()
        older = root / "articles" / f"{former}-tech-law-brief.html"
        if not older.exists():
            continue
        old_urls = set()
        for card in soup(older).select("article.brief-item"):
            value = card.get("data-citation")
            if not value:
                continue
            try:
                old_urls.add(json.loads(value).get("url"))
            except (ValueError, TypeError):
                continue
        for i, item in enumerate(items, 1):
            demand(item["url"] not in old_urls or
                   (item.get("material_new_event") is True and item.get("new_action_details")),
                   f"Potential duplicate source from {former}: item {i}")
    return day, items, coverage, current, False


def make_article(doc, item, ordinal):
    citation = json.dumps({
        "originalTitle": item["original_title"].strip(),
        "url": item["url"].strip(),
    }, ensure_ascii=False, separators=(",", ":"))
    article = doc.new_tag("article", id=item["id"])
    article["class"] = "brief-item"
    article["data-citation"] = citation
    article["data-event-date"] = item["date"]
    article["data-material-type"] = "news"
    new_child(doc, article, "h3", f'{ordinal}. {item["title"].strip()}')
    new_child(doc, article, "div",
              f'{item["date"]} · {item["jurisdiction"]} · {item["agency"]}',
              css_class="brief-meta")
    if item.get("domestic") is not True:
        origin = new_child(doc, article, "p", css_class="brief-original")
        new_child(doc, origin, "strong", "原始题名：")
        origin.append(item["original_title"].strip())
    new_child(doc, article, "p", item["fact"].strip(), css_class="brief-fact")
    for label in ANALYSIS_LABELS:
        para = new_child(doc, article, "p", css_class="analysis-pending")
        para["style"] = ANALYSIS_HIDE
        new_child(doc, para, "strong", label)
    insight = new_child(doc, article, "script", css_class="brief-insight", type="application/json")
    insight.string = json.dumps({"background": "", "outlook": ""}, separators=(",", ":"))
    source = new_child(doc, article, "p", css_class="source")
    source.append("原始来源：")
    link = new_child(doc, source, "a", item["source_name"], href=item["url"])
    return article


def set_brief_nav(doc, href):
    links = [a for a in doc.select(".navlinks a") if a.get_text(strip=True) == "全球科技法简报"]
    demand(len(links) == 1, "Cannot identify news navigation entry")
    links[0]["href"] = href


def generate_page(root, day, items, current, *, backfilled_at=None):
    old = root / current["pages"]["brief"]
    demand(old.is_file(), "Previous news HTML is missing")
    doc = soup(old)
    doc.title.string = f'{int(day[:4])}年{int(day[5:7])}月{int(day[8:])}日全球科技法简报｜网信法研究每日推送'
    text(doc.select_one(".article-hero .eyebrow"), "issue eyebrow").string = "每日全球科技法简报 · " + day.replace("-", ".")
    lead = text(doc.select_one(".article-hero .lead"), "issue lead")
    lead.string = f'{int(day[:4])}年{int(day[5:7])}月{int(day[8:])}日 · {len(items)}条'
    if backfilled_at is not None:
        released = backfilled_at.astimezone(TZ)
        lead.string += f" · {released.year}年{released.month}月{released.day}日补发"
    text(doc.body, "page body")["data-analysis-status"] = "pending"
    set_brief_nav(doc, day + "-tech-law-brief.html")
    by_labels = {
        "域外法学论文精读": current["pages"]["paper"].removeprefix("articles/"),
        "法学经典著作": current["pages"]["classic"].removeprefix("articles/"),
        "科技法研究新作": current["pages"]["newworks"].removeprefix("articles/"),
    }
    for label, path in by_labels.items():
        for a in doc.select(".navlinks a"):
            if a.get_text(strip=True) == label:
                a["href"] = path
    body = text(doc.select_one(".article-body .article-wrap"), "brief item container")
    body.clear()
    domestic = [item for item in items if item.get("domestic") is True]
    foreign = [item for item in items if item.get("domestic") is not True]
    for label, group in (("国内", domestic), ("国际", foreign)):
        if group:
            new_child(doc, body, "h2", label)
            for item in group:
                body.append(make_article(doc, item, items.index(item) + 1))
    new_path = root / "articles" / f"{day}-tech-law-brief.html"
    demand(not new_path.exists(), "New issue already exists outside manifest; manual review required")
    save(new_path, str(doc))
    return str(new_path.relative_to(root))


def update_entrances(root, day, items, page, current):
    display = day.replace("-", ".")
    count = len(items)
    index = soup(root / "index.html")
    brief = text(index.select_one('.portal-card[data-daily-column="brief"]'),
                 "home news card")
    brief["href"] = page
    text(brief.select_one(".portal-latest small"), "home news date").string = display + " · 最新一期"
    titles = [item["title"].strip()[:22] for item in items[:4]]
    text(brief.select_one(".portal-latest strong"), "home news summary").string = f'{count}条｜' + "；".join(titles)
    set_brief_nav(index, page)
    save(root / "index.html", str(index))

    listing = soup(root / "briefs.html")
    block = text(listing.select_one(".issue-list"), "news issue listing")
    for old in block.select(".issue-row .issue-action"):
        demand(old.get("href") != page, "Duplicate day already in news history")
    card = listing.new_tag("article")
    card["class"] = "issue-row"
    date_div = new_child(listing, card, "div", css_class="issue-date")
    new_child(listing, date_div, "strong", display)
    main_div = new_child(listing, card, "div", css_class="issue-main")
    new_child(listing, main_div, "h3", f"全球科技法简报 · {count}条")
    new_child(listing, card, "a", "阅读全文 →", css_class="issue-action", href=page)
    block.insert(0, card)
    set_brief_nav(listing, page)
    save(root / "briefs.html", str(listing))

    archive = soup(root / "archive.html")
    arch = text(archive.select_one('.portal-card[href="briefs.html"]'), "archive news card")
    text(arch.select_one("p"), "archive news summary").string = f"最新：{display} · {count}条"
    set_brief_nav(archive, page)
    save(root / "archive.html", str(archive))


def issue_record(draft, day, items, coverage, now, page, *, backfill=False):
    entries = []
    for entry in items:
        entries.append({key: entry[key] for key in (
            "id", "domestic", "date", "jurisdiction", "agency", "title",
            "original_title", "source_name", "url", "fact"
        )})
    return {
        "date": day, "column": "brief", "state": "verified", "phase": "publishing",
        "page": page, "news_count": len(items),
        "distribution": {"domestic": sum(e["domestic"] is True for e in items),
                         "foreign": sum(e["domestic"] is not True for e in items)},
        "mode": "fact_only", "analysis_pending": True,
        "published_as_backfill": bool(backfill),
        "actual_release_at": now.astimezone(TZ).isoformat(),
        "checked_at": draft.get("checked_at") or draft["last_news_scan_at"],
        "last_news_scan_at": draft["last_news_scan_at"],
        "checks": copy.deepcopy(draft["checks"]),
        "domestic_source_coverage": coverage,
        "items": entries,
        "analysis": {"status": "pending", "task": "网信法新闻分析补充"},
        "publication": {
            "article_written": True, "index_updated": True,
            "briefs_updated": True, "archive_updated": True,
            "current_edition_updated": True,
            "pages_status": "awaiting_deployment",
        }
    }


def publish(root, draft, now, *, backfill=False):
    day, items, coverage, current, already = verify(root, draft, now, backfill=backfill)
    if already:
        return {"status": "already_published", "date": day}
    page = generate_page(root, day, items, current, backfilled_at=now if backfill else None)
    update_entrances(root, day, items, page, current)
    next_manifest = copy.deepcopy(current)
    next_manifest["pages"]["brief"] = page
    next_manifest["page_dates"]["brief"] = day
    next_manifest["news_count"] = len(items)
    next_manifest["date"] = max(next_manifest["page_dates"].values())
    save(root / "data/current-edition.json",
         json.dumps(next_manifest, ensure_ascii=False, indent=2) + "\n")
    output_record = root / ".github/editions" / f"{day}.news.json"
    demand(not output_record.exists(), "Verified news record already exists; manual review required")
    save(output_record,
         json.dumps(issue_record(draft, day, items, coverage, now, page, backfill=backfill),
                    ensure_ascii=False, indent=2) + "\n")
    generated = [page, *OUTPUT_FILES, str(output_record.relative_to(root))]
    return {"status": "prepared", "date": day, "count": len(items),
            "domestic": sum(e.get("domestic") is True for e in items),
            "files": generated}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--draft", required=True, type=Path)
    parser.add_argument("--now", help="ISO 8601 timestamp, for deterministic offline tests")
    parser.add_argument("--backfill", action="store_true", help="Publish an explicitly authorized historical edition within two days")
    args = parser.parse_args()
    now = datetime.fromisoformat(args.now) if args.now else datetime.now(TZ)
    demand(now.tzinfo is not None, "Timestamp must include timezone")
    result = publish(args.root, load(args.draft), now, backfill=args.backfill)
    print(json.dumps(result, ensure_ascii=False))


if __name__ == "__main__":
    main()
