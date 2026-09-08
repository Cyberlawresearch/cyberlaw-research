"""Finish reviewed daily editions and monitor delivery; never generate or certify research.

Only a fresh, hash-bound review record may promote a candidate. All mutations are
limited to four current reading-page navs, reader entry points, and the manifest.
GitHub retries use the latest main SHA only, have a bounded budget, and do not
force-push. Diagnostics live in Actions and a deduplicated repository issue.
"""
from __future__ import annotations
import argparse
from datetime import datetime, timedelta, timezone
import hashlib
import json
import os
from pathlib import Path
import posixpath
import re
import shutil
import subprocess
import tempfile
import time
from urllib.error import HTTPError, URLError
from urllib.parse import urljoin, urlsplit
from urllib.request import Request, urlopen
from zoneinfo import ZoneInfo
from bs4 import BeautifulSoup
import edition_gate as gate

ROOT = Path(__file__).resolve().parents[1]
REPO = 'Cyberlawresearch/cyberlaw-research'
SITE = 'https://cyberlawresearch.github.io/cyberlaw-research/'
ZONE = ZoneInfo('Asia/Shanghai')
KEYS = ('brief', 'paper', 'classic', 'newworks')
ENTRY = ('index.html', 'archive.html', *gate.HISTORIES, 'data/current-edition.json')
CHECKS = ('sources', 'legal_status', 'bibliography', 'deduplication', 'original_titles')
MAX_ATTEMPTS = 3

class ReleaseError(Exception):
    pass

def require(condition, message):
    if not condition:
        raise ReleaseError(message)

def timestamp(value):
    result = datetime.fromisoformat(str(value).replace('Z', '+00:00'))
    require(result.tzinfo is not None, '核验时间必须带时区')
    return result

def load(path):
    return json.loads(path.read_text(encoding='utf-8'))

def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def expected_day(now):
    # Early-morning retries belong to the previous evening, not a new issue.
    return (now.astimezone(ZONE) - timedelta(hours=12)).date()

def overdue(now, day):
    return now.astimezone(ZONE) >= datetime.combine(day, datetime.min.time(), ZONE).replace(hour=22)

def document(root, path):
    return BeautifulSoup((root / path).read_text(encoding='utf-8'), 'html.parser')

def verify_candidate(root, record, now):
    day = datetime.fromisoformat(record['date']).date()
    require(day <= now.astimezone(ZONE).date(), '不能提前发布未来日期')
    pages = record.get('pages', {})
    require(list(pages) == list(KEYS) and len(set(pages.values())) == 4, '四栏正文必须唯一且齐全')
    review = record.get('review', {})
    require(review.get('status') == 'verified', '内容尚未完成核验')
    require(all(review.get('checks', {}).get(k) is True for k in CHECKS), '核验项目不完整')
    checked = timestamp(review['checked_at'])
    scanned = timestamp(review['last_news_scan_at'])
    require(scanned <= checked <= now, '核验时间不正确')
    require(now - scanned <= timedelta(hours=2), '新闻终检已超过两小时，需要更新检索')
    for path in pages.values():
        require(re.fullmatch(r'(articles|papers|new-works)/[A-Za-z0-9_.-]+\.html', path) is not None, '正文路径不受支持')
        require(record['date'] in Path(path).name, '正文日期与本期不一致')
        file = root / path
        require(file.resolve().is_relative_to(root.resolve()) and file.is_file(), '缺少正文：' + path)
        require(review.get('sha256', {}).get(path) == digest(file), '正文在核验后发生变化：' + path)
    news = document(root, pages['brief']).select('.brief-item')
    events = review.get('news_event_times', {})
    require(len(news) == record.get('news_count') and 18 <= len(news) <= 20, '新闻数量不完整')
    require({n.get('id') for n in news} == set(events), '缺少逐条新闻的来源时间记录')
    for identity, value in events.items():
        elapsed = now - timestamp(value)
        require(timedelta(0) <= elapsed <= timedelta(hours=72), '新闻不在发布时的72小时内：' + identity)
    require(record.get('newworks_count') == 5, '研究新作必须为5项')
    return {k: record[k] for k in ('date', 'pages', 'news_count', 'newworks_count')}

def update_entries(root, manifest):
    paths = list(manifest['pages'].values())
    titles = [document(root, p).select_one('main h1').get_text(' ', strip=True) for p in paths]
    doc = document(root, 'index.html')
    cards = doc.select('.portal-card')
    require(len(cards) == 4, '首页结构无法识别；不自动改版')
    for i, (card, path) in enumerate(zip(cards, paths)):
        card['href'] = path
        require(card.select_one('.portal-latest small') is not None and card.select_one('.portal-latest strong') is not None, '首页卡片缺少本期信息')
        card.select_one('.portal-latest small').string = manifest['date'].replace('-', '.') + ' · 最新一期'
        text = titles[i]
        if i in (0, 3):
            heads = document(root, path).select('.brief-item h3')[:3]
            text = ('18条' if i == 0 and manifest['news_count'] == 18 else str(manifest['news_count'])+'条') if i == 0 else '5项'
            text += '｜' + '；'.join(re.sub(r'^\s*\d+[.、]\s*', '', h.get_text(' ', strip=True)) for h in heads)
        card.select_one('.portal-latest strong').string = text
    # Keep a single existing secondary archive entry, never create another menu.
    for a in doc.select('.navlinks a[href="archive.html"]'):
        a.decompose()
    (root / 'index.html').write_text(str(doc), encoding='utf-8')
    for path, listing, title in zip(paths, gate.HISTORIES, titles):
        d = document(root, listing)
        collection = d.select_one('.issue-list')
        require(collection is not None, '历史列表结构无法识别：' + listing)
        old = next((r for r in collection.select('.issue-row') if r.select_one(f'a[href="{path}"]')), None)
        if old is not None:
            row = old.extract()
        else:
            row = d.new_tag('article', attrs={'class': 'issue-row'})
            date_node = d.new_tag('div', attrs={'class': 'issue-date'})
            strong = d.new_tag('strong'); strong.string = manifest['date'].replace('-', '.')
            date_node.append(strong); row.append(date_node)
            main = d.new_tag('div', attrs={'class': 'issue-main'})
            h = d.new_tag('h3'); h.string = title; main.append(h); row.append(main)
            link = d.new_tag('a', href=path, attrs={'class': 'issue-action'})
            link.string = '阅读全文 →'; row.append(link)
        # Remove only the old "latest" badge text; retain dates and every prior row.
        for n in collection.select('.issue-date'):
            for text in list(n.find_all(string=True, recursive=False)):
                if '最新一期' in text:
                    text.replace_with(str(text).replace('最新一期', ''))
        collection.insert(0, row)
        (root / listing).write_text(str(d), encoding='utf-8')
    for path in [*paths, *ENTRY[:-1]]:
        d = document(root, path)
        for a in d.select('.navlinks a'):
            label = a.get_text(strip=True)
            if label in gate.LABELS:
                a['href'] = posixpath.relpath(paths[gate.LABELS.index(label)], posixpath.dirname(path) or '.')
        (root / path).write_text(str(d), encoding='utf-8')
    (root / 'data/current-edition.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')

def promote(root, record, now):
    manifest = verify_candidate(root, record, now)
    previous = load(root / 'data/current-edition.json')
    require(manifest['date'] > previous['date'], '不回退或重复发布既有日期')
    allowed = [*ENTRY, *manifest['pages'].values()]
    # Trial on a disposable copy. A failed gate must not modify live source files.
    with tempfile.TemporaryDirectory(prefix='edition-trial-') as temp:
        trial = Path(temp) / 'site'
        shutil.copytree(root, trial, ignore=shutil.ignore_patterns('.git', '__pycache__', 'reader-test-results'))
        update_entries(trial, manifest)
        original = gate.ROOT
        try:
            gate.ROOT = trial
            gate.validate(manifest)
        finally:
            gate.ROOT = original
        changed = [p for p in allowed if (root / p).read_bytes() != (trial / p).read_bytes()]
        for p in changed:
            shutil.copyfile(trial / p, root / p)
    return changed

def git(*args):
    return subprocess.check_output(['git', *args], cwd=ROOT, text=True).strip()

class GitHubAPI:
    def __init__(self):
        self.token = os.environ['GH_TOKEN']
    def request(self, method, suffix, data=None):
        url = 'https://api.github.com/repos/' + REPO + suffix
        raw = None if data is None else json.dumps(data).encode()
        req = Request(url, data=raw, method=method, headers={
            'Authorization': 'Bearer ' + self.token, 'Accept': 'application/vnd.github+json',
            'Content-Type': 'application/json', 'User-Agent': 'cyberlaw-daily-release'})
        # Reads are retryable. Do not blindly retry a non-idempotent POST.
        for attempt in range(3 if method == 'GET' else 1):
            try:
                with urlopen(req, timeout=30) as response:
                    body = response.read()
                    return json.loads(body) if body else {}
            except HTTPError as e:
                if method == 'GET' and e.code >= 500 and attempt < 2:
                    time.sleep(2 ** attempt); continue
                raise ReleaseError(f'GitHub {method} {suffix.split("?")[0]} 返回 {e.code}') from None
            except URLError:
                if method == 'GET' and attempt < 2:
                    time.sleep(2 ** attempt); continue
                raise ReleaseError('GitHub 网络请求失败') from None

def delivery_action(runs, live_ok):
    ordered = sorted(runs, key=lambda r: int(r['id']), reverse=True)
    if any(r['status'] != 'completed' for r in ordered):
        return 'running'
    if ordered and ordered[0].get('conclusion') == 'success' and live_ok:
        return 'delivered'
    spent = sum(int(r.get('run_attempt', 1)) for r in ordered)
    if spent >= MAX_ATTEMPTS:
        return 'exhausted'
    if ordered and ordered[0].get('conclusion') in ('failure', 'timed_out', 'cancelled'):
        return 'rerun'
    return 'dispatch'

def live_matches(manifest):
    try:
        def read(path):
            request = Request(urljoin(SITE, path)+'?release-check='+str(time.time_ns()), headers={'User-Agent':'cyberlaw-release-check'})
            with urlopen(request, timeout=20) as response:
                return response.read()
        if json.loads(read('data/current-edition.json')) != manifest:
            return False
        d = BeautifulSoup(read('index.html'), 'html.parser')
        paths = list(manifest['pages'].values())
        if [a.get('href') for a in d.select('.portal-card')] != paths:
            return False
        return all(d.select_one(f'.navlinks a[href="{p}"]') for p in paths)
    except (ValueError, URLError, TimeoutError):
        return False

def notify(api, day, problem=None):
    marker = '<!-- daily-release:' + day.isoformat() + ' -->'
    issues = api.request('GET', '/issues?state=open&per_page=100')
    issue = next((x for x in issues if marker in (x.get('body') or '') and 'pull_request' not in x), None)
    if problem is None:
        if issue:
            api.request('POST', f'/issues/{issue["number"]}/comments', {'body': '本期已完成发布。已核对当前提交的 Pages completed/success、线上本期清单与首页入口。'})
            api.request('PATCH', f'/issues/{issue["number"]}', {'state':'closed'})
        return
    title = '每日推送未完成｜' + day.isoformat()
    body = marker + '\n@Cyberlawresearch\n\n' + problem + '\n\n自动流程不会用占位正文、未核验内容或旧闻补齐数量。原有完整一期保持可读。\n详细执行记录见仓库 Actions 的“每日推送发布保障”。'
    if issue is None:
        api.request('POST', '/issues', {'title':title, 'body':body})
    elif issue.get('body') != body:
        api.request('PATCH', f'/issues/{issue["number"]}', {'body':body})

def run(now, api):
    require(os.environ.get('GITHUB_REPOSITORY') == REPO, '仓库不匹配')
    current = load(ROOT / 'data/current-edition.json')
    day = expected_day(now)
    problem = None
    changed = False
    candidates = sorted((ROOT / '.github/editions').glob('????-??-??.json'), reverse=True)
    for file in candidates:
        if current['date'] < file.stem <= now.astimezone(ZONE).date().isoformat():
            try:
                record = load(file)
                require(record.get('date') == file.stem, '核验文件名与日期不一致')
                paths = promote(ROOT, record, now)
                require(paths, '候选内容没有产生入口更新')
                git('diff', '--check')
                git('config', 'user.name', 'github-actions[bot]')
                git('config', 'user.email', '41898282+github-actions[bot]@users.noreply.github.com')
                git('add', '--', *paths)
                git('commit', '-m', '同步发布已核验四栏：' + record['date'])
                git('push', 'origin', 'HEAD:main')  # fast-forward only; concurrency conflicts fail closed
                current = load(ROOT / 'data/current-edition.json'); changed = True
            except subprocess.CalledProcessError:
                raise ReleaseError('提交或推送发生冲突；已停止，不覆盖远端；下一轮重新读取 main') from None
            except (ReleaseError, AssertionError, KeyError, ValueError) as e:
                problem = '本期内容尚未通过发布门槛：' + str(e)[:450]
            break
    # Validate the actual complete edition, not just the presence of four files.
    try:
        gate.validate(current)
    except (AssertionError, KeyError, ValueError) as e:
        problem = '当前整期结构验收失败：' + str(e)[:450]
    require(problem is None or not changed, problem or '')
    head = git('rev-parse', 'HEAD')
    remote = api.request('GET', '/git/ref/heads/main')['object']['sha']
    if remote != head:
        return {'status':'pending', 'action':'superseded', 'delivered':False,
                'commit':head, 'expected_date':day.isoformat(), 'current_date':current['date'],
                'problem':None, 'content_generation_controlled':False}
    runs = api.request('GET', '/actions/runs?head_sha=' + head + '&per_page=100')['workflow_runs']
    runs = [r for r in runs if r.get('path') == '.github/workflows/pages.yml' and r.get('head_branch') == 'main']
    action = delivery_action(runs, live_matches(current))
    if action == 'dispatch':
        # Let a normal push-triggered Pages run appear before adding a dispatch.
        age = now.timestamp() - int(git('log', '-1', '--format=%ct'))
        if changed or age >= 120:
            api.request('POST', '/actions/workflows/pages.yml/dispatches', {'ref':'main'})
            action = 'deployment_requested'
        else:
            action = 'waiting_for_push_deployment'
    elif action == 'rerun':
        latest = max(runs, key=lambda r: int(r['id']))
        api.request('POST', f'/actions/runs/{latest["id"]}/rerun', {})
        action = 'retry_requested'
    elif action == 'exhausted':
        problem = problem or '当前提交部署或线上验收未通过；已达到三次尝试上限。'
    if current['date'] < day.isoformat():
        pending = sorted(p.name for p in (ROOT / 'articles').glob(day.isoformat() + '-*.html'))
        problem = problem or ('到检查时仍未发布完整一期。已有正文文件：' + ('、'.join(pending) if pending else '无') + '。需由内容生成任务补齐、核验并提交当期核验记录。')
    delivered = action == 'delivered' and current['date'] >= day.isoformat() and problem is None
    if delivered:
        notify(api, datetime.fromisoformat(current['date']).date())
    elif problem and (overdue(now, day) or action == 'exhausted'):
        notify(api, day, problem)
    return {'checked_at':now.isoformat(), 'expected_date':day.isoformat(), 'current_date':current['date'],
            'commit':head, 'action':action, 'delivered':delivered, 'problem':problem,
            'content_generation_controlled':False,
            'status':'failed' if problem and (overdue(now, day) or action == 'exhausted') else 'passed' if delivered else 'pending'}

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', default='/tmp/daily-release/results.json')
    args = parser.parse_args()
    now = datetime.now(timezone.utc)
    try:
        result = run(now, GitHubAPI())
    except Exception as e:
        # Do not log request headers, tokens, or raw API response bodies.
        detail = str(e)[:450] if isinstance(e, (ReleaseError, AssertionError, KeyError, ValueError)) else type(e).__name__
        result = {'status':'failed', 'problem':detail, 'checked_at':now.isoformat(), 'content_generation_controlled':False}
    output = Path(args.output); output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
    print(json.dumps(result, ensure_ascii=False, indent=2))
    if os.environ.get('GITHUB_STEP_SUMMARY'):
        with open(os.environ['GITHUB_STEP_SUMMARY'], 'a', encoding='utf-8') as summary:
            summary.write('# 每日推送发布保障\n\n```json\n' + json.dumps(result, ensure_ascii=False, indent=2) + '\n```\n')
    if result['status'] == 'failed':
        raise SystemExit(1)

if __name__ == '__main__':
    main()
