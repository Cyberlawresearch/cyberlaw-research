"""Regression tests use synthetic HTML; no repository or network writes."""
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch
import requests
from trade_watch_presence import check, local_check

DAY = '2026-01-02'
REL = f'issues/{DAY}.html'
ISSUE = '''<html><title>第001期｜2026年1月2日</title><nav class="navlinks"><a href="../index.html">首页</a></nav><section class="issue-head">第001期 2026年1月2日 1条重点</section><article class="news-list"><section class="news-card" id="one"><h2>测试标题</h2><div class="news-copy"><p>测试正文</p><div class="source"><a href="https://example.com/source">来源</a></div></div></section></article><aside class="toc"><a href="#one">目录</a></aside></html>'''
HOME = f'''<html><title>首页</title><nav class="navlinks">导航</nav><a class="latest-feature" href="{REL}">第001期</a><div class="focus-grid">重点</div></html>'''
ARCHIVE = f'''<html><title>归档</title><nav class="navlinks">导航</nav><div class="archive-list"><a class="archive-item" href="{REL}">第001期</a></div></html>'''

class PresenceTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        (self.root / 'issues').mkdir()
        self.contents = {REL: ISSUE, 'index.html': HOME, 'archive.html': ARCHIVE}
        for name, content in self.contents.items():
            (self.root / name).write_text(content, encoding='utf-8')
    def test_complete_local_issue(self):
        _, errors, count = local_check(self.root, DAY)
        self.assertEqual(errors, [])
        self.assertEqual(count, 1)
    def test_missing_issue(self):
        (self.root / REL).unlink()
        self.assertTrue(local_check(self.root, DAY)[1])
    def test_previous_day_is_not_success(self):
        self.assertTrue(local_check(self.root, '2026-01-03')[1])
    def test_stale_home(self):
        (self.root / 'index.html').write_text(HOME.replace(REL, 'issues/2026-01-01.html'), encoding='utf-8')
        self.assertTrue(local_check(self.root, DAY)[1])
    def test_missing_archive_entry(self):
        (self.root / 'archive.html').write_text('<title>归档</title>', encoding='utf-8')
        self.assertTrue(local_check(self.root, DAY)[1])
    def test_placeholder(self):
        (self.root / REL).write_text('<title>第001期｜2026年1月2日</title>', encoding='utf-8')
        self.assertTrue(local_check(self.root, DAY)[1])
    def test_count_mismatch(self):
        (self.root / REL).write_text(ISSUE.replace('1条', '11条'), encoding='utf-8')
        self.assertTrue(local_check(self.root, DAY)[1])
    def test_public_content_matches(self):
        def get(url, **kwargs):
            relative = url.split('/trade-watch/')[1]
            return Mock(content=self.contents[relative].encode(), status_code=200, raise_for_status=Mock())
        with patch('trade_watch_presence.requests.get', side_effect=get):
            report = check(self.root, DAY, False)
        self.assertTrue(report['public_ok'])
    def test_public_error_is_not_success(self):
        with patch('trade_watch_presence.requests.get', side_effect=requests.ConnectionError('offline')), patch('trade_watch_presence.time.sleep'):
            report = check(self.root, DAY, False)
        self.assertTrue(report['repository_ok'])
        self.assertFalse(report['public_ok'])
        self.assertEqual(len(report['errors']), 3)
    def test_public_old_version_is_not_success(self):
        response = Mock(content=ISSUE.replace('2026年1月2日', '2026年1月1日').encode(), status_code=200, raise_for_status=Mock())
        with patch('trade_watch_presence.requests.get', return_value=response), patch('trade_watch_presence.time.sleep'):
            self.assertFalse(check(self.root, DAY, False)['public_ok'])

if __name__ == '__main__':
    unittest.main()
