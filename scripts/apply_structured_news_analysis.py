"""Render structured per-item news analysis into deployed brief pages.

The analysis task writes small JSON records under
``.github/editions/analysis/YYYY-MM-DD/`` instead of replacing a long HTML page.
This keeps GitHub writes small and isolates a failure to one item. During the
Pages build, completed analysis packages are validated and merged into the
corresponding news page.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from bs4 import BeautifulSoup
from bs4.element import Tag

ROOT = Path(__file__).resolve().parents[1]
ANALYSIS_ROOT = ROOT / ".github" / "editions" / "analysis"

FIELD_LABELS = {
    "legal_analysis": "法治研判：",
    "think_tank": "智库选题参考：",
    "paper_topic": "论文选题：",
}


def load_json(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"analysis JSON must be an object: {path}")
    return data


def direct_child(item: Tag, selector: str) -> Tag | None:
    found = item.select_one(f":scope > {selector}")
    return found if isinstance(found, Tag) else None


def find_analysis_paragraph(item: Tag, label: str) -> Tag:
    for paragraph in item.find_all("p", recursive=False):
        if not isinstance(paragraph, Tag):
            continue
        strong = paragraph.find("strong", recursive=False)
        if isinstance(strong, Tag) and strong.get_text(strip=True) == label:
            return paragraph
    raise ValueError(f"missing analysis slot {label} in {item.get('id')}")


def fill_paragraph(paragraph: Tag, label: str, text: str, soup: BeautifulSoup) -> None:
    text = text.strip()
    if not text:
        raise ValueError(f"empty analysis text for {label}")
    paragraph.attrs.pop("style", None)
    classes = [name for name in paragraph.get("class", []) if name != "analysis-pending"]
    if classes:
        paragraph["class"] = classes
    else:
        paragraph.attrs.pop("class", None)
    paragraph.clear()
    strong = soup.new_tag("strong")
    strong.string = label
    paragraph.append(strong)
    paragraph.append(text)


def fill_item(item: Tag, record: dict[str, Any], soup: BeautifulSoup) -> None:
    for field, label in FIELD_LABELS.items():
        value = record.get(field)
        if not isinstance(value, str):
            raise ValueError(f"missing {field} for {record.get('id')}")
        fill_paragraph(find_analysis_paragraph(item, label), label, value, soup)

    background = record.get("background")
    outlook = record.get("outlook")
    if not isinstance(background, str) or not background.strip():
        raise ValueError(f"missing background for {record.get('id')}")
    if not isinstance(outlook, str) or not outlook.strip():
        raise ValueError(f"missing outlook for {record.get('id')}")

    insight = direct_child(item, "script.brief-insight")
    if insight is None:
        insight = soup.new_tag("script", type="application/json")
        insight["class"] = "brief-insight"
        source = direct_child(item, "p.source")
        if source is None:
            raise ValueError(f"missing source paragraph in {record.get('id')}")
        source.insert_before(insight)
    insight.string = json.dumps(
        {"background": background.strip(), "outlook": outlook.strip()},
        ensure_ascii=False,
        separators=(",", ":"),
    )


def apply_package(package_dir: Path) -> dict[str, Any] | None:
    meta_path = package_dir / "_meta.json"
    if not meta_path.is_file():
        return None
    meta = load_json(meta_path)
    if meta.get("state") != "completed":
        return None

    page_value = meta.get("page")
    if not isinstance(page_value, str) or not page_value.strip():
        raise ValueError(f"missing page in {meta_path}")
    page = ROOT / page_value
    if not page.is_file():
        raise ValueError(f"analysis target page not found: {page_value}")

    record_paths = sorted(
        path for path in package_dir.glob("*.json") if path.name != "_meta.json"
    )
    records = [load_json(path) for path in record_paths]
    expected_count = meta.get("expected_count")
    if not isinstance(expected_count, int) or expected_count < 1:
        raise ValueError(f"invalid expected_count in {meta_path}")
    if len(records) != expected_count:
        raise ValueError(
            f"analysis record count mismatch for {package_dir.name}: "
            f"expected {expected_count}, found {len(records)}"
        )

    source = page.read_text(encoding="utf-8")
    soup = BeautifulSoup(source, "html.parser")
    page_items = {
        item.get("id"): item
        for item in soup.select("article.brief-item")
        if isinstance(item, Tag) and item.get("id")
    }
    if len(page_items) != expected_count:
        raise ValueError(
            f"page item count mismatch for {page_value}: "
            f"expected {expected_count}, found {len(page_items)}"
        )

    seen: set[str] = set()
    for record in records:
        item_id = record.get("id")
        if not isinstance(item_id, str) or not item_id:
            raise ValueError(f"missing item id in {package_dir}")
        if item_id in seen:
            raise ValueError(f"duplicate analysis item id: {item_id}")
        seen.add(item_id)
        item = page_items.get(item_id)
        if item is None:
            raise ValueError(f"analysis item not found in page: {item_id}")
        fill_item(item, record, soup)

    missing = sorted(set(page_items) - seen)
    if missing:
        raise ValueError(f"analysis missing page items: {', '.join(missing)}")

    if soup.body:
        soup.body["data-analysis-status"] = "completed"
    page.write_text(str(soup), encoding="utf-8")
    return {
        "date": meta.get("date", package_dir.name),
        "page": page_value,
        "items": len(records),
    }


def main() -> None:
    if not ANALYSIS_ROOT.is_dir():
        print(json.dumps({"structured_analysis": []}, ensure_ascii=False))
        return
    applied: list[dict[str, Any]] = []
    for package_dir in sorted(path for path in ANALYSIS_ROOT.iterdir() if path.is_dir()):
        result = apply_package(package_dir)
        if result is not None:
            applied.append(result)
    print(json.dumps({"structured_analysis": applied}, ensure_ascii=False))


if __name__ == "__main__":
    main()
