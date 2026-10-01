#!/usr/bin/env python3
"""Read-only Trade Watch freshness and publication checks. Never generates news."""
from __future__ import annotations
import argparse
import json
import os
import re
import sys
import time
from datetime import date, datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import requests
from bs4 import BeautifulSoup

BASE = 'https://cyberlawresearch.github.io/cyberlaw-research/trade-watch/'


def text(node):
    return node.get_text(' ', strip=True) if node else ''


def signature(node):
    return (text(node), [(a.get('href'), text(a)) for a in node.select('a[href]')]) if node else None


def local_check(root: Path, expected: str):
    date.fromisoformat(expected)
    relative = f'issues/{expected}.html'
    errors, documents = [], {}
    for path in [relative, 'index.html', 'archive.html']:
        try:
            documents[path] = BeautifulSoup((root / path).read_text(encoding='utf-8'), 'html.parser')
        except (OSError, UnicodeError) as exc:
            errors.append({'stage': 'repository', 'path': path, 'detail': str(exc)})
    def require(condition, path, detail):
        if not condition:
            errors.append({'stage': 'repository', 'path': path, 'detail': detail})
    home = documents.get('index.html')
    archive = documents.get('archive.html')
    issue = documents.get(relative)
    feature = home.select_one('a.latest-feature') if home else None
    entries = archive.select('a.archive-item') if archive else []
    require(feature and feature.get('href') == relative, 'index.html', 'Latest issue does not point to expected date')
    require(entries and entries[0].get('href') == relative, 'archive.html', 'Expected issue is not first in archive')
    require(sum(a.get('href') == relative for a in entries) == 1, 'archive.html', 'Expected issue must appear exactly once')
    count = 0
    if issue:
        cards = issue.select('.news-card')
        count = len(cards)
        head = issue.select_one('.issue-head')
        require(count > 0, relative, 'No news cards; placeholder pages cannot pass')
        d = date.fromisoformat(expected)
        display_date = f'{d.year}年{d.month}月{d.day}日'
        require(display_date in text(head) and display_date in text(issue.title), relative, 'Issue date mismatch')
        declared = re.search(r'(\d+)条', text(head))
        require(declared and int(declared.group(1)) == count, relative, 'Declared news count differs from actual cards')
        numbers = [re.search(r'第(\d+)期', text(node)) for node in [issue.title, head, feature, entries[0] if entries else None]]
        require(all(numbers) and len({m.group(1) for m in numbers if m}) == 1, relative, 'Issue numbers are missing or inconsistent')
        ids = [card.get('id') for card in cards]
        require(all(ids) and len(set(ids)) == count, relative, 'News IDs are missing or duplicated')
        for card in cards:
            label = card.get('id', '(missing id)')
            require(text(card.select_one('h2')) and text(card.select_one('.news-copy > p')), relative, 'Missing headline or facts: ' + label)
            require(card.select_one('.source a[href]'), relative, 'Missing original source: ' + label)
        for link in issue.select('.toc a[href^="#"]'):
            require(link['href'][1:] in ids, relative, 'Broken contents link: ' + link['href'])
    return documents, errors, count


def check(root: Path, expected: str, offline: bool, commit: str = ''):
    documents, errors, count = local_check(root, expected)
    report = {'expected_date': expected, 'commit': commit, 'news_count': count,
              'checked_at': datetime.now(ZoneInfo('Asia/Shanghai')).isoformat(),
              'repository_ok': not errors, 'public_ok': False, 'pages': [], 'errors': errors}
    if errors or offline:
        return report
    for path, document in documents.items():
        selectors = ['.navlinks', '.issue-head', '.news-list', '.toc'] if path.startswith('issues/') else ['.navlinks', '.latest-feature', '.focus-grid'] if path == 'index.html' else ['.navlinks', '.archive-list']
        item = {'path': path, 'ok': False, 'attempts': []}
        for attempt in range(3):
            try:
                response = requests.get(BASE + path, params={'verify': commit or expected}, timeout=(8, 20))
                response.raise_for_status()
                actual = BeautifulSoup(response.content, 'html.parser')
                if text(actual.title) != text(document.title):
                    raise ValueError('Public page title differs from repository')
                for selector in selectors:
                    a, b = actual.select_one(selector), document.select_one(selector)
                    if not a or not b or signature(a) != signature(b):
                        raise ValueError('Public content or links mismatch: ' + selector)
                item.update(ok=True, status=response.status_code)
                break
            except (requests.RequestException, ValueError) as exc:
                item['attempts'].append(str(exc))
                if attempt < 2:
                    time.sleep(10)
        report['pages'].append(item)
        if not item['ok']:
            errors.append({'stage': 'public', 'path': path, 'detail': item['attempts'][-1]})
    report['public_ok'] = not errors
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=Path('trade-watch'))
    parser.add_argument('--date', default='')
    parser.add_argument('--latest', action='store_true', help='Check newest issue file instead of today; for preflight only')
    parser.add_argument('--offline', action='store_true')
    parser.add_argument('--commit', default=os.environ.get('GITHUB_SHA', ''))
    parser.add_argument('--report', type=Path, default=Path(os.environ.get('RUNNER_TEMP', '/tmp')) / 'trade-watch-presence.json')
    args = parser.parse_args()
    expected = args.date or datetime.now(ZoneInfo('Asia/Shanghai')).date().isoformat()
    try:
        if args.latest:
            names = sorted(p.stem for p in (args.root / 'issues').glob('????-??-??.html') if re.fullmatch(r'\d{4}-\d{2}-\d{2}', p.stem))
            if not names:
                raise ValueError('No issue files in repository')
            expected = names[-1]
        report = check(args.root, expected, args.offline, args.commit)
    except Exception as exc:
        report = {'expected_date': expected, 'repository_ok': False, 'public_ok': False,
                  'errors': [{'stage': 'checker', 'detail': str(exc)}]}
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 1 if report['errors'] else 0


if __name__ == '__main__':
    sys.exit(main())
