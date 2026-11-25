"""Apply the public site name and XinYu byline without rewriting article bodies.

The deployment normalizes historical site chrome before building its indexes,
then adds the shared masthead after the interior theme. Only exact site/column
names are replaced; factual uses of 网信法 and source metadata remain intact.
"""
from __future__ import annotations

import argparse
from html.parser import HTMLParser
from pathlib import Path
import re

SITE_NAME = "科技法研究每日推送"
TECH_LABEL = "科技法技术基础"
BYLINE = "by学科技法的XinYu"
VERSION = "20261125b"
ALIASES = {"网信法研究每日推送": SITE_NAME, "网信法技术基础": TECH_LABEL}
EXCLUDED = {"trade-watch", "node_modules", "dist", "build", "__pycache__"}
VOID = {"area", "base", "br", "col", "embed", "hr", "img", "input", "link", "meta", "param", "source", "track", "wbr"}
ASSETS = re.compile(r"\n?<!-- shared-site-brand:start -->.*?<!-- shared-site-brand:end -->\n?", re.S)


def canonical_name(text: str) -> str:
    for old, new in ALIASES.items():
        text = text.replace(old, new)
    return text


class BrandMarkup(HTMLParser):
    """Record exact source offsets so unrelated HTML is kept byte-for-byte."""
    def __init__(self, source: str):
        super().__init__(convert_charrefs=False)
        self.source = source
        self.lines = [0]
        for line in source.splitlines(keepends=True):
            self.lines.append(self.lines[-1] + len(line))
        self.stack = []
        self.edits = []
        self.brands = []
        self.bylines = []
        self.head_end = None

    def source_offset(self) -> int:
        line, column = self.getpos()
        return self.lines[line - 1] + column

    def handle_starttag(self, tag, attrs):
        start = self.source_offset()
        raw = self.get_starttag_text()
        values = dict(attrs)
        classes = set((values.get("class") or "").split())
        is_brand = ("brand" in classes and any(x["tag"] == "header" for x in self.stack)) or "login-brand" in classes
        element = {"tag": tag, "start": start, "classes": classes,
                   "brand": is_brand,
                   "wrapped": bool(self.stack and "site-identity" in self.stack[-1]["classes"])}
        if "site-byline" in classes:
            self.bylines.append(start)
        # Human-readable metadata only: never touch URLs, IDs, data-citation,
        # source authors, account keys or other machine-owned attributes.
        for match in re.finditer(r"(?<![\w:-])(title|aria-label|alt|content)\s*=\s*([\"'])(.*?)\2", raw, re.I | re.S):
            if match.group(1).lower() == "content" and tag != "meta":
                continue
            before = match.group(3)
            after = canonical_name(before)
            if before != after:
                self.edits.append((start + match.start(3), start + match.end(3), after))
        if tag not in VOID:
            self.stack.append(element)

    def handle_startendtag(self, tag, attrs):
        self.handle_starttag(tag, attrs)
        if tag not in VOID:
            self.stack.pop()

    def handle_endtag(self, tag):
        start = self.source_offset()
        end = self.source.index(">", start) + 1
        if tag == "head":
            self.head_end = start
        for index in range(len(self.stack) - 1, -1, -1):
            element = self.stack[index]
            if element["tag"] == tag:
                if element["brand"]:
                    self.brands.append({**element, "end": end})
                del self.stack[index:]
                break

    def handle_data(self, data):
        if any(x["tag"] in {"script", "style"} for x in self.stack):
            return
        replacement = canonical_name(data)
        if replacement != data:
            start = self.source_offset()
            self.edits.append((start, start + len(data), replacement))


def transform(source: str, relative: Path, *, names_only: bool = False) -> str:
    if not names_only:
        source = ASSETS.sub("", source)
    parser = BrandMarkup(source)
    parser.feed(source)
    parser.close()
    edits = parser.edits
    if not names_only:
        if parser.head_end is None or len(parser.brands) != 1:
            raise ValueError(f"Expected one site masthead and a complete head in {relative}")
        brand = parser.brands[0]
        if brand["wrapped"]:
            if len(parser.bylines) != 1 or BYLINE not in source:
                raise ValueError(f"Incomplete or duplicate site byline in {relative}")
        else:
            if parser.bylines:
                raise ValueError(f"Unexpected existing site byline in {relative}")
            edits.append((brand["start"], brand["start"], '<div class="site-identity">'))
            edits.append((brand["end"], brand["end"], f'<span class="site-byline">{BYLINE}</span></div>'))
        prefix = "../" * len(relative.parent.parts)
        resources = ("\n<!-- shared-site-brand:start -->\n"
                     f'<link rel="stylesheet" href="{prefix}assets/site-brand.css?v={VERSION}">\n'
                     "<!-- shared-site-brand:end -->\n")
        edits.append((parser.head_end, parser.head_end, resources))
    for start, end, replacement in sorted(edits, reverse=True):
        source = source[:start] + replacement + source[end:]
    return source


def pages(root: Path):
    for path in sorted(root.rglob("*.html")):
        relative = path.relative_to(root)
        if any(part.startswith(".") or part in EXCLUDED for part in relative.parts):
            continue
        yield path, relative


def apply(root: Path, *, names_only: bool = False) -> tuple[int, int]:
    total = changed = 0
    for path, relative in pages(root):
        original = path.read_text(encoding="utf-8")
        rendered = transform(original, relative, names_only=names_only)
        total += 1
        if rendered != original:
            path.write_text(rendered, encoding="utf-8")
            changed += 1
    return total, changed


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--names-only", action="store_true", help="Normalize public labels before index generation; add presentation after the interior theme")
    args = parser.parse_args()
    total, changed = apply(args.root.resolve(), names_only=args.names_only)
    mode = "names" if args.names_only else "name and byline"
    print(f"Shared site {mode}: {total} pages, {changed} updated.")
    if not args.names_only:
        from site_quality import inspect_site, sync_archive_media
        sync_archive_media(args.root.resolve())
        inspect_site(args.root.resolve())


if __name__ == "__main__":
    main()
