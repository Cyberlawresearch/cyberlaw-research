"""Apply the shared interior-page presentation to the deploy artifact.

Historical HTML stays byte-for-byte intact apart from the body presentation
attributes and the two shared asset references. This also covers future editions
without requiring each independent publishing task to duplicate the site chrome.
"""

from __future__ import annotations

import argparse
from collections import Counter
from html import unescape
from html.parser import HTMLParser
import json
from pathlib import Path
import re


VERSION = "20261125b"
BODY = re.compile(r"<body\b(?:[^\"'>]|\"[^\"]*\"|'[^']*')*>", re.I)
HEAD_END = re.compile(r"</head\s*>", re.I)
BLOCK = re.compile(
    r"\n?<!-- shared-interior:start -->.*?<!-- shared-interior:end -->\n?",
    re.S,
)
EXCLUDED_DIRS = {"trade-watch", "node_modules", "dist", "build", "__pycache__"}
LEGACY_PAGE = Path("papers/2026-08-08.html")
LEGACY_PARTS = (
    "data/papers/2026-08-08/001.part",
    "data/papers/2026-08-08/002.part",
    "data/papers/2026-08-08/003.part",
)


def materialize_legacy_page(root: Path) -> bool:
    """Resolve the one known split page in the build artifact, never execute JS.

    Run before normal content preparation so authentication, navigation, indexes
    and reading tools receive the same full document as all other articles.
    The checked-in loader and its three part files remain the source of truth.
    """
    path = root / LEGACY_PAGE
    source = path.read_text(encoding="utf-8")
    if not re.search(r"\bdocument\s*\.\s*write\s*\(", source):
        return False
    files = re.search(r"\bconst\s+files\s*=\s*(\[[^\]]*\])", source)
    if not files or json.loads(files.group(1)) != list(LEGACY_PARTS):
        raise ValueError(f"Unexpected split-page loader in {LEGACY_PAGE}; refusing to replace it")
    chunks = []
    for relative in LEGACY_PARTS:
        part = root / relative
        if not part.is_file() or part.is_symlink():
            raise FileNotFoundError(f"Missing regular split-page source: {relative}")
        chunks.append(part.read_bytes())
    document = b"".join(chunks).decode("utf-8")

    class Structure(HTMLParser):
        def __init__(self) -> None:
            super().__init__(convert_charrefs=True)
            self.events = []

        def handle_starttag(self, tag, attrs):
            if tag in {"html", "head", "body", "main", "footer"}:
                self.events.append(("start", tag))

        def handle_endtag(self, tag):
            if tag in {"html", "head", "body", "main", "footer"}:
                self.events.append(("end", tag))

    structure = Structure()
    structure.feed(document)
    structure.close()
    expected = [
        ("start", "html"), ("start", "head"), ("end", "head"),
        ("start", "body"), ("start", "main"), ("end", "main"),
        ("start", "footer"), ("end", "footer"), ("end", "body"),
        ("end", "html"),
    ]
    if structure.events != expected or not re.search(r"</html\s*>\s*$", document, re.I):
        raise ValueError(f"Incomplete document in split-page sources for {LEGACY_PAGE}")
    path.write_text(document, encoding="utf-8")
    return True


def attribute(tag: str, name: str) -> str:
    match = re.search(r"(?<![\w-])" + re.escape(name) + r"\s*=\s*([\"'])(.*?)\1", tag, re.I | re.S)
    return unescape(match.group(2)) if match else ""


def section_for(path: Path, text: str, body: str) -> str:
    name = path.name.lower()
    material = attribute(body, "data-material-type").lower()
    classes = set(attribute(body, "class").split())
    eyebrow = re.search(
        r"<[^>]+class=[\"'][^\"']*\beyebrow\b[^\"']*[\"'][^>]*>(.*?)</[^>]+>",
        text,
        re.I | re.S,
    )
    label = re.sub(r"<[^>]+>", "", eyebrow.group(1)).upper() if eyebrow else ""
    if "tech-basics" in path.parts or name == "tech-basics.html":
        return "tech"
    if name == "media-ai.html" or "ai-media-digest" in name or "media-ai-reading" in classes:
        return "media"
    if name.startswith("briefs") or "tech-law-brief" in name or material == "news":
        return "brief"
    if "new-works" in path.parts or "new-works" in name or material == "newwork":
        return "newworks"
    if name.startswith("classics") or material == "book" or "classic-page" in classes:
        return "classic"
    # Older paper editions use "CLASSIC PAPER"; explicit paper identity must
    # precede the historical book labels.
    if name.startswith("papers") or "papers" in path.parts or material == "paper" or "PAPER" in label or "论文精读" in label:
        return "paper"
    if "CLASSIC BOOK" in label or "LEGAL CLASSIC" in label or "经典著作" in label:
        return "classic"
    if name == "archive.html":
        return "archive"
    if "articles" in path.parts:
        return "paper"
    return "tools"


def presentation_body(tag: str, section: str) -> str:
    classes = attribute(tag, "class").split()
    if "interior-page" not in classes:
        classes.append("interior-page")
    class_attr = re.compile(r"(?<![\w-])class\s*=\s*([\"'])(.*?)\1", re.I | re.S)
    if class_attr.search(tag):
        tag = class_attr.sub(lambda m: f'class={m.group(1)}{" ".join(classes)}{m.group(1)}', tag, count=1)
    else:
        tag = tag[:-1] + ' class="' + " ".join(classes) + '">'
    section_attr = re.compile(r"\s+data-interior-section\s*=\s*([\"'])(.*?)\1", re.I | re.S)
    tag = section_attr.sub("", tag)
    return tag[:-1] + f' data-interior-section="{section}">'


def transform(text: str, path: Path) -> tuple[str, str | None]:
    body = BODY.search(text)
    if not body or not HEAD_END.search(text):
        return text, None
    section = section_for(path, text, body.group())
    text = BODY.sub(lambda m: presentation_body(m.group(), section), text, count=1)
    text = BLOCK.sub("", text)
    prefix = "../" * len(path.parent.parts)
    assets = (
        "\n<!-- shared-interior:start -->\n"
        f'<link rel="stylesheet" href="{prefix}assets/interior.css?v={VERSION}">\n'
        f'<script defer src="{prefix}assets/interior.js?v={VERSION}"></script>\n'
        "<!-- shared-interior:end -->\n"
    )
    text = HEAD_END.sub(lambda m: assets + m.group(), text, count=1)
    return text, section


def apply(root: Path) -> Counter:
    counts: Counter = Counter()
    for path in sorted(root.rglob("*.html")):
        relative = path.relative_to(root)
        if relative == Path("index.html") or any(part.startswith(".") or part in EXCLUDED_DIRS for part in relative.parts):
            continue
        original = path.read_text(encoding="utf-8")
        rendered, section = transform(original, relative)
        if section:
            counts[section] += 1
            if rendered != original:
                path.write_text(rendered, encoding="utf-8")
    return counts


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--materialize-only", action="store_true", help="Resolve the known split article before normal build processing")
    args = parser.parse_args()
    if args.materialize_only:
        changed = materialize_legacy_page(args.root.resolve())
        print(f"Split article: {'materialized' if changed else 'already static'} ({LEGACY_PAGE}).")
        return
    counts = apply(args.root.resolve())
    print(f"Shared interior design: {sum(counts.values())} pages ({', '.join(f'{key}={count}' for key, count in sorted(counts.items()))}).")


if __name__ == "__main__":
    main()
