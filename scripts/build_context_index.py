"""Build reader recommendations from item facts, without indexing reader UI.

The existing search indexes remain unchanged. Books keep their public pages and
search records, but are not candidates for contextual related reading.
"""
from __future__ import annotations
import json
import re
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / 'assets'

class Node:
    def __init__(self, tag='', attrs=(), parent=None):
        self.tag, self.attrs, self.parent, self.children = tag, dict(attrs), parent, []
    def has(self, name):
        return name in self.attrs.get('class', '').split()
    def walk(self):
        yield self
        for child in self.children:
            if isinstance(child, Node):
                yield from child.walk()
    def text(self):
        if self.tag in {'script', 'style', 'nav', 'header', 'footer'} or any(
            self.has(c) for c in ('ctx-actions', 'source', 'reading-directory', 'account-nav')
        ):
            return ''
        return re.sub(r'\s+', ' ', ' '.join(
            c.text() if isinstance(c, Node) else c for c in self.children
        )).strip()
    def first(self, predicate):
        return next((n for n in self.walk() if predicate(n)), None)

class Document(HTMLParser):
    VOID = set('area base br col embed hr img input link meta param source track wbr'.split())
    def __init__(self, text):
        super().__init__(convert_charrefs=True)
        self.root = self.current = Node('root')
        self.feed(text)
    def handle_starttag(self, tag, attrs):
        node = Node(tag, attrs, self.current)
        self.current.children.append(node)
        if tag not in self.VOID:
            self.current = node
    def handle_startendtag(self, tag, attrs):
        self.handle_starttag(tag, attrs)
        if tag not in self.VOID:
            self.handle_endtag(tag)
    def handle_endtag(self, tag):
        node = self.current
        while node.parent is not None:
            if node.tag == tag:
                self.current = node.parent
                return
            node = node.parent
    def handle_data(self, data):
        self.current.children.append(data)

DOCUMENTS = {}
def document(path):
    if path not in DOCUMENTS:
        resolved = (ROOT / path).resolve()
        if not resolved.is_relative_to(ROOT) or resolved.suffix != '.html':
            raise ValueError(f'Invalid content path: {path}')
        DOCUMENTS[path] = Document(resolved.read_text(encoding='utf-8')).root
    return DOCUMENTS[path]

def content_block(doc, row):
    anchor = row.get('anchor', '')
    explicit = doc.first(lambda n: bool(anchor) and n.attrs.get('id') == anchor)
    if explicit:
        return explicit
    number = re.search(r'research-item-(\d+)$', anchor)
    idx = int(number.group(1)) - 1 if number else -1
    cards = [n for n in doc.walk() if n.tag == 'article' and n.has('brief-item')]
    if 0 <= idx < len(cards):
        return cards[idx]
    headings = [n for n in doc.walk() if n.tag == 'h3' and re.match(r'^\s*\d+[.、]', n.text())]
    if 0 <= idx < len(headings):
        heading = headings[idx]
        siblings = heading.parent.children
        block = Node('section')
        for child in siblings[siblings.index(heading):]:
            if child is not heading and isinstance(child, Node) and child.tag in {'h2', 'h3'}:
                break
            block.children.append(child)
        return block
    return None

ANALYSIS = re.compile(r'^(?:法治研判|智库选题|论文选题|原始来源|公开来源|来源|意义|研究延伸)')
def facts_only(block):
    explicit = [n.text() for n in block.walk() if n.has('brief-fact')]
    if explicit:
        return ' '.join(explicit)
    facts = []
    for n in block.children:
        if not isinstance(n, Node):
            continue
        text = n.text()
        if any(n.has(c) for c in ('brief-analysis-grid', 'brief-meaning', 'meaning')) or ANALYSIS.match(text):
            break
        if n.tag == 'p' and text and not n.has('source'):
            facts.append(text)
    return ' '.join(facts)

def book_like(block, category=''):
    if category == '法学经典著作':
        return True
    explicit = block.first(lambda n: n.attrs.get('data-material-type') in {'book', 'article'})
    if explicit:
        return explicit.attrs['data-material-type'] == 'book'
    text = block.text()[:1800]
    # Publication labels/ISBN, not a publisher platform name inside journal metadata.
    if re.search(r'ISBN|出版社\s*[:：]|英文法学专著|本书|这部书|这部著作|学术专著', text, re.I):
        return True
    meta = block.first(lambda n: n.has('brief-meta'))
    if meta and re.search(r'University Press|Publishing|出版社', meta.text(), re.I):
        return not re.search(r'\bVol\.?|\bJournal\b|\bReview\b|\bIssue\b|期刊|\bArticle\b', meta.text(), re.I)
    return False

def read(name):
    return json.loads((ASSETS / name).read_text(encoding='utf-8'))

def build():
    output = []
    for row in read('news-index.json'):
        doc = document(row['path'])
        block = content_block(doc, row)
        if block is None or not row.get('title'):
            continue
        meta = block.first(lambda n: n.has('brief-meta') or n.has('brief-date'))
        output.append({**row, 'kind': 'news', 'materialType': 'news',
                       'meta': meta.text() if meta else row.get('meta', ''),
                       'facts': facts_only(block), 'text': block.text()})
    for row in read('newworks-index.json'):
        block = content_block(document(row['path']), row)
        if block is not None and not book_like(block):
            output.append({**row, 'kind': 'work', 'materialType': 'article', 'text': block.text()})
    for row in read('research-index.json'):
        if row['category'] != '域外法学论文精读':
            continue
        main = document(row['path']).first(lambda n: n.tag == 'main')
        if main is None or book_like(main, row['category']) or '正在载入' in row['title']:
            continue
        output.append({**row, 'kind': 'paper', 'materialType': 'article'})
    for row in output:
        if row['kind'] == 'news' and not row['facts']:
            raise ValueError(f'No factual paragraph: {row["id"]}')
    (ASSETS / 'context-index.json').write_text(
        json.dumps(output, ensure_ascii=False, separators=(',', ':')), encoding='utf-8')
    print('Context index:', {kind: sum(x['kind'] == kind for x in output) for kind in ('news','work','paper')})
    return output

if __name__ == '__main__':
    build()
