"""Reviewed editorial corrections and non-destructive language audit.

This step runs on the Pages build copy before generating search indexes. The
verified historical source files, source URLs, anchors and direct quotations
are not rewritten. Only exact, reviewed Chinese phrases are replaced. Audit
candidates are reports for human review, not automatic substitutions.
"""
from __future__ import annotations

import html
from html.parser import HTMLParser
import json
from collections import Counter
from pathlib import Path
import os
import re

ROOT = Path(__file__).resolve().parents[1]
RULES = json.loads((ROOT / "scripts/editorial_language_edits.json").read_text(encoding="utf-8"))
TITLES = RULES["titles"]
EDITS = RULES["edits"]
VOID = {"area", "base", "br", "col", "embed", "hr", "img", "input", "link", "meta", "param", "source", "track", "wbr"}
SKIP_TAGS = {"script", "style", "blockquote", "q", "code", "pre"}
SKIP_CLASSES = {"source", "brief-original", "media-original", "media-sentence", "sentence-text", "original-title", "original-label", "media-source", "original-source", "source-list"}
EXCLUDED = {".git", ".github", "trade-watch", "node_modules", "dist", "build", "__pycache__"}

def replacements(path, value, heading=False):
    pairs = EDITS.get(path, []) + TITLES
    for old, new in pairs:
        value = value.replace(old, new)
    if heading:
        if "全书阅读地图" in value:
            value = value.replace("全书阅读地图", "全书结构与论证脉络")
        if path.startswith("tech-basics/"):
            if value.strip() == "法治连接":
                value = value.replace("法治连接", "法律制度与合规要求")
            if value.strip() == "两个可发展的研究问题":
                value = value.replace("两个可发展的研究问题", "研究延伸")
    if path == "media-ai.html" or "ai-media-digest" in path:
        value = re.sub(r"(\d+)篇正文命中", r"\1篇在正文中涉及相关主题", value)
        value = re.sub(r"正文命中(\d+)篇", r"其中\1篇正文涉及相关主题", value)
        value = value.replace("无新增命中", "无新增相关文章").replace("正文命中", "正文涉及相关主题")
        value = value.replace("标题+正文", "标题与正文均相关").replace("检索异常：", "来源核验说明：")
    return value

class Polish(HTMLParser):
    def __init__(self, source, path):
        super().__init__(convert_charrefs=False)
        self.source, self.path = source, path
        self.offsets = [0]
        for line in source.splitlines(keepends=True):
            self.offsets.append(self.offsets[-1] + len(line))
        self.stack = []
        self.edits = []

    def offset(self):
        line, col = self.getpos()
        return self.offsets[line-1] + col

    def protected(self):
        return any(p for _, p in self.stack)

    def start(self, tag, attrs, push=True):
        values = dict(attrs)
        classes = set((values.get("class") or "").split())
        blocked = self.protected() or tag in SKIP_TAGS or bool(classes & SKIP_CLASSES)
        # Update Chinese title metadata only, never an original title, URL or source.
        if not blocked:
            raw = self.get_starttag_text()
            pos = self.offset()
            for m in re.finditer(r"(?<![\w:-])(title|aria-label)\s*=\s*(['\"])(.*?)\2", raw, re.S | re.I):
                before = html.unescape(m.group(3))
                after = replacements(self.path, before)
                if before != after:
                    self.edits.append((pos + m.start(3), pos + m.end(3), html.escape(after, quote=True)))
            for m in re.finditer(r"(?<![\w:-])data-citation\s*=\s*(['\"])(.*?)\1", raw, re.S | re.I):
                try:
                    obj = json.loads(html.unescape(m.group(2)))
                except (TypeError, ValueError):
                    continue
                if isinstance(obj, dict) and isinstance(obj.get("cnTitle"), str):
                    new = obj["cnTitle"]
                    for old, new_title in TITLES:
                        new = new.replace(old, new_title)
                    if new != obj["cnTitle"]:
                        obj["cnTitle"] = new
                        self.edits.append((pos + m.start(2), pos + m.end(2), html.escape(json.dumps(obj, ensure_ascii=False, separators=(",", ":")), quote=True)))
        if push and tag not in VOID:
            self.stack.append((tag, blocked))

    def handle_starttag(self, tag, attrs):
        self.start(tag, attrs)

    def handle_startendtag(self, tag, attrs):
        self.start(tag, attrs, False)

    def handle_endtag(self, tag):
        for i in range(len(self.stack)-1, -1, -1):
            if self.stack[i][0] == tag:
                del self.stack[i:]
                break

    def handle_data(self, text):
        if self.protected():
            return
        heading = any(tag in {"h1","h2","h3","h4","summary"} for tag, _ in self.stack)
        updated = replacements(self.path, text, heading)
        if updated != text:
            pos = self.offset()
            self.edits.append((pos, pos+len(text), updated))

def transform(source, path):
    p = Polish(source, path)
    p.feed(source)
    p.close()
    result = source
    for start, end, value in sorted(p.edits, reverse=True):
        result = result[:start] + value + result[end:]
    return result, len(p.edits)

def inspect(root):
    findings = Counter()
    samples = []
    paths = 0
    changes = {}
    # Candidates are intentionally broad enough for review, not a blacklist.
    markers = re.compile(r"正文命中|全量覆盖|恢复真正的公职|自由表达是三角形|隐私破裂的承诺|隐私的失信|策展正当程序|法律想象|制度断崖|制度增量|治理抓手|主体性上的|结构性耦合|获建议|遭凭证入侵|相关防御方")
    for file in sorted(root.rglob("*.html")):
        rel = file.relative_to(root)
        if any(x.startswith(".") or x in EXCLUDED for x in rel.parts):
            continue
        paths += 1
        source = file.read_text(encoding="utf-8")
        path = rel.as_posix()
        updated, count = transform(source, path)
        if count:
            # Existing resource URLs, element ids and external links remain intact.
            for pattern in (r'\bid=(["\'])(.*?)\1', r'\b(?:href|src)=(["\'])(.*?)\1'):
                if re.findall(pattern, source, re.S) != re.findall(pattern, updated, re.S):
                    raise ValueError("Editorial patch would alter links or IDs: " + path)
            if transform(updated, path)[0] != updated:
                raise ValueError("Non-idempotent editorial patch: " + path)
            file.write_text(updated, encoding="utf-8")
            changes[path] = count
        # Scan rendered reader text for candidates. Do not treat direct quotations,
        # English sources, or matches in historical writing as automatically wrong.
        plain = re.sub(r"<(?:script|style|blockquote)\b[^>]*>.*?</(?:script|style|blockquote)>", " ", updated, flags=re.S|re.I)
        plain = html.unescape(re.sub(r"<[^>]+>", " ", plain))
        for m in markers.finditer(plain):
            findings[m.group(0)] += 1
            if len(samples) < 200:
                samples.append({"path":path,"term":m.group(0),"context":re.sub(r"\s+"," ",plain[max(0,m.start()-45):m.end()+45]).strip()})
    report = {"pages_scanned":paths,"pages_changed":len(changes),"text_nodes_changed":sum(changes.values()),"changes":changes,"review_candidates":dict(findings),"samples":samples}
    print("Editorial language:", json.dumps({k:v for k,v in report.items() if k not in {"samples","changes"}},ensure_ascii=False))
    if os.environ.get("RUNNER_TEMP"):
        dest = Path(os.environ["RUNNER_TEMP"]) / "context-tests" / "editorial-language.json"
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding="utf-8")
    return report

def self_test():
    raw = '<html><head><title>自由表达是三角形</title></head><body><h2>全书阅读地图</h2><blockquote>自由表达是三角形</blockquote><a href="keep.html#abc" id="abc">自由表达是三角形</a><p class="brief-original">自由表达是三角形</p><script>const x="自由表达是三角形";</script></body></html>'
    out,n = transform(raw,"articles/2026-10-02-balkin-free-speech-triangle.html")
    assert n == 3
    assert '<title>言论自由的三角结构</title>' in out
    assert '<blockquote>自由表达是三角形</blockquote>' in out
    assert '<p class="brief-original">自由表达是三角形</p>' in out
    assert '<script>const x="自由表达是三角形";</script>' in out
    assert 'href="keep.html#abc" id="abc"' in out
    assert transform(out,"articles/2026-10-02-balkin-free-speech-triangle.html")[0] == out
    media,_ = transform('<p class="hit-mode">正文命中</p><blockquote>正文命中</blockquote><p>7篇正文命中</p>',"media-ai.html")
    assert "7篇在正文中涉及相关主题" in media and "<blockquote>正文命中</blockquote>" in media

if __name__ == "__main__":
    self_test()
    inspect(ROOT)
