"""Targeted reader regression checks. Fixtures never use production storage.
Live checks use real Pages assets and disposable browser-local accounts/data.
This is not a factual/legal/bibliographic audit or a cloud-auth security test.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import sys
import time
import uuid
from urllib.parse import urljoin, urlsplit

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[2]
RESULTS = []
FIXTURE_URL = 'https://reader.invalid/articles/fixture.html'
NOTE = 'cyberlawNotesV1::fixture'
FULL = 'cyberlawFullFavoritesV2::fixture'
INSP = 'cyberlawInspirationFavoritesV2::fixture'
STYLE = '<style>.fav-popover{position:fixed;display:none;z-index:100}.fav-popover.show{display:block}[hidden]{display:none!important}</style>'
STORAGE = """() => {
 const data={}; window.testStore=data; window.failKey='';
 Object.defineProperty(window,'localStorage',{value:{
   getItem:k=>data[k]??null,
   setItem:(k,v)=>{if(k===window.failKey)throw new DOMException('Full','QuotaExceededError');data[k]=String(v)},
   removeItem:k=>{delete data[k]}
 }});
 window.CyberlawAuth={user:'fixture',key:k=>k+'::fixture'};
 window.scrolledTo=''; Element.prototype.scrollIntoView=function(){window.scrolledTo=this.id};
}"""


def record(name, function):
    try:
        detail = function() or 'Assertions passed'
        RESULTS.append({'test': name, 'status': 'passed', 'detail': detail})
        print('PASS', name, flush=True)
    except Exception as error:
        RESULTS.append({'test': name, 'status': 'failed', 'detail': str(error)[:3000]})
        print('FAIL', name, str(error)[:500], flush=True)


def fixture(browser, body, url=FIXTURE_URL):
    context = browser.new_context(offline=True)
    page = context.new_page()
    page.set_default_timeout(4000)
    page.set_content(STYLE + '<main><h1>完整著作题名</h1>' + body + '</main>')
    page.evaluate(STORAGE)
    page.errors = []
    page.on('pageerror', lambda error: page.errors.append(str(error)))
    return context, page, url


def execute(page, asset, url):
    # About:blank DOM fixtures use explicit location/storage doubles; no navigation.
    page.evaluate('([code,href])=>Function("location",code)({href})',
                  [(ROOT / 'assets' / asset).read_text(encoding='utf-8'), url])


def put(page, key, value):
    page.evaluate('([key,value])=>localStorage.setItem(key,value)', [key, json.dumps(value, ensure_ascii=False)])


def get(page, key):
    return page.evaluate('key=>JSON.parse(localStorage.getItem(key)||"[]")', key)


def write_note(page, index=0, text='临时测试笔记'):
    actions = page.locator('.ctx-actions').nth(index)
    actions.locator('[data-note-inline]').click()
    actions.locator('.note-inline-text').fill(text)
    actions.locator('[data-note-save]').click()


def fixture_notes(browser, case):
    id_attr = '' if case == 'missing-id' else 'id="research-item-1"'
    body = f'<section class="article-body" {id_attr}><div class="ctx-actions"><button data-act="fav">加入我的收藏</button></div><h2>作者、版本与问题背景</h2><p>正文内容。</p></section>'
    if case == 'item':
        body = '<section class="article-body">' + ''.join(
            f'<article class="brief-item" id="news-{i}"><h3>{i}. 具体新闻{i}</h3><p>新闻内容{i}</p><div class="ctx-actions"><button data-act="fav">加入我的收藏</button></div></article>' for i in (1, 2)) + '</section>'
    context, page, url = fixture(browser, body)
    try:
        put(page, 'cyberlawNotesV1::other', [{'id': 'untouched', 'content': 'other account fixture'}])
        if case == 'existing':
            put(page, FULL, [{'id': 'existing', 'itemKey': url + '#research-item-1', 'note': '保留备注'}])
        if case.startswith('corrupt'):
            key = NOTE if case == 'corrupt-notes' else FULL
            page.evaluate('key=>localStorage.setItem(key,"BROKEN_DATA")', key)
        if case == 'quota':
            page.evaluate('key=>window.failKey=key', NOTE)
        execute(page, 'notes-inline.js', url)
        write_note(page, 1 if case == 'item' else 0)
        assert not page.errors, page.errors
        assert get(page, 'cyberlawNotesV1::other')[0]['id'] == 'untouched'
        if case.startswith('corrupt'):
            assert page.evaluate('key=>localStorage.getItem(key)', key) == 'BROKEN_DATA'
            assert page.locator('.note-inline-text').input_value() == '临时测试笔记'
            assert len(page.evaluate('Object.keys(testStore)')) == 2
            return 'Unreadable storage retained byte-for-byte; no new persistent write'
        if case == 'quota':
            assert get(page, NOTE) == []
            assert page.locator('.note-inline-text').input_value() == '临时测试笔记'
            assert '笔记未保存' in page.locator('.fav-toast').inner_text()
            return 'Failed save retains editor input; no false success'
        notes, favorites = get(page, NOTE), get(page, FULL)
        assert len(notes) == len(favorites) == 1
        assert notes[0]['sourceTitle'] == ('具体新闻2' if case == 'item' else '完整著作题名')
        assert notes[0]['sourceUrl'] == url + ('#news-2' if case == 'item' else '#research-item-1')
        assert '写笔记' not in notes[0]['sourceExcerpt'] and '加入我的收藏' not in notes[0]['sourceExcerpt']
        assert notes[0]['favoriteId'] == favorites[0]['id']
        if case == 'existing':
            assert favorites[0]['note'] == '保留备注'
    finally:
        context.close()


def select_excerpt(page):
    page.locator('#excerpt').evaluate("""el=>{const r=document.createRange();r.selectNodeContents(el);
      const s=getSelection();s.removeAllRanges();s.addRange(r);document.dispatchEvent(new Event('selectionchange'))}""")
    page.locator('.fav-popover.show').click()


def fixture_excerpt_save(browser, corrupt=False):
    context, page, url = fixture(browser, '<section class="article-body"><p id="excerpt">Alpha \n <em>beta</em>   gamma.</p></section>')
    try:
        if corrupt:
            page.evaluate('key=>localStorage.setItem(key,"BROKEN_EXCERPTS")', INSP)
        execute(page, 'favorites.js', url)
        select_excerpt(page)
        assert not page.errors, page.errors
        if corrupt:
            assert page.evaluate('key=>localStorage.getItem(key)', INSP) == 'BROKEN_EXCERPTS'
            return 'Unreadable excerpts are not replaced'
        saved = get(page, INSP)
        assert len(saved) == 1 and saved[0]['text'] == 'Alpha beta gamma.'
        assert saved[0]['sourceAnchor'] == 'excerpt'
        assert page.evaluate('getSelection().isCollapsed')
        select_excerpt(page)
        assert len(get(page, INSP)) == 1 and page.evaluate('getSelection().isCollapsed')
        assert page.locator('mark').count() == 0
    finally:
        context.close()


def fixture_excerpt_jump(browser, case):
    body = '<section class="article-body"><p id="excerpt">Alpha \n <em>beta</em>   gamma.</p>'
    if case in ('ambiguous', 'anchored'):
        body += '<p id="second">Alpha beta gamma.</p>'
    body += '</section>'
    context, page, url = fixture(browser, body, FIXTURE_URL + '?fav=legacy')
    try:
        saved = {'id': 'legacy', 'text': 'Alpha beta gamma.', 'pageUrl': FIXTURE_URL,
                 'startPath': [999], 'endPath': [999], 'startOffset': 0, 'endOffset': 999}
        if case == 'anchored': saved['sourceAnchor'] = 'second'
        if case == 'wrong-page': saved['pageUrl'] = FIXTURE_URL.replace('fixture.html', 'other.html')
        put(page, INSP, [saved]); execute(page, 'favorites.js', url)
        if case in ('ambiguous', 'wrong-page'):
            page.wait_for_timeout(220)
            assert page.evaluate('window.scrolledTo') == ''
            if case == 'ambiguous': assert '未能准确定位' in page.locator('.fav-toast').inner_text()
        else:
            page.wait_for_function('window.scrolledTo!==""')
            assert page.evaluate('window.scrolledTo') == ('second' if case == 'anchored' else 'excerpt')
        assert not page.errors, page.errors
        assert page.evaluate('getSelection().isCollapsed')
    finally:
        context.close()


def live_checks(browser, site, output):
    context = browser.new_context(viewport={'width': 1440, 'height': 1000}, accept_downloads=True)
    page = context.new_page(); page.set_default_timeout(20000)
    errors = []; page.on('pageerror', lambda error: errors.append(str(error)))
    token = uuid.uuid4().hex
    prefix = 'reader-regression-' + token
    note_key = 'cyberlawNotesV1::researcher20'
    full_key = 'cyberlawFullFavoritesV2::researcher20'
    insp_key = 'cyberlawInspirationFavoritesV2::researcher20'
    site = site.rstrip('/') + '/'
    base_path = urlsplit(site).path

    def navigate(path):
        response = page.goto(urljoin(site, path), wait_until='domcontentloaded')
        assert response and response.status == 200, f'Page unavailable: {path}'

    def login(user):
        page.locator('#login-user').wait_for()
        # This override lives only inside this fresh browser profile, not on a server.
        page.evaluate("""([user,password])=>{
          let h=0x811c9dc5;for(const c of `${user}|${password}`){h^=c.charCodeAt(0);h=Math.imul(h,0x01000193)>>>0}
          localStorage.setItem(`cyberlawPasswordVersion::${user}`,'3');
          localStorage.setItem(`cyberlawPasswordOverride::${user}`,String(h>>>0));
        }""", [user, token])
        page.locator('#login-user').fill(user); page.locator('#login-password').fill(token)
        page.locator('#login-form').evaluate('form=>form.requestSubmit()')
        page.locator('.account-user').wait_for()
        assert page.locator('.account-user').inner_text() == user

    try:
        # Verify the served scripts match this exact checkout, not just a green deployment.
        for asset in ('notes-inline.js', 'favorites.js'):
            expected = hashlib.sha256((ROOT / 'assets' / asset).read_bytes()).hexdigest()
            matched = False
            for attempt in range(8):
                response = context.request.get(urljoin(site, 'assets/' + asset) + '?readercheck=' + token + str(attempt))
                if response.status == 200 and hashlib.sha256(response.body()).hexdigest() == expected:
                    matched = True; break
                time.sleep(4)
            assert matched, f'Deployed asset does not match checkout: {asset}'
        navigate('index.html'); login('researcher20')
        assert '网信法研究每日推送' in page.locator('.brand').inner_text()
        for selector in ('.account-favorites', '.account-notes', '.account-settings'):
            assert page.locator(selector).is_visible()
        navigate('articles/2026-09-02-lessig-code.html')
        actions = page.locator('.ctx-actions').first
        actions.locator('[data-note-inline]').wait_for()
        heading = page.locator('main h1').inner_text()
        actions.locator('[data-note-inline]').click()
        actions.locator('.note-inline-text').fill(prefix)
        actions.locator('[data-note-save]').click()
        note = get(page, note_key)[0]; favorite = get(page, full_key)[0]
        assert note['sourceTitle'] == favorite['title'] == heading
        assert note['favoriteId'] == favorite['id'] and '#' in note['sourceUrl']
        assert '写笔记' not in note['sourceExcerpt']
        navigate('notes.html')
        card = page.locator(f'.note-card[data-id="{note["id"]}"]')
        assert prefix in card.inner_text()
        card.locator('[data-edit]').click(); page.locator('#note-content').fill(prefix + '-edited')
        page.locator('#note-form').evaluate('form=>form.requestSubmit()')
        page.reload(wait_until='domcontentloaded'); page.locator('#notes-search').fill(prefix + '-edited')
        assert page.locator('.note-card').count() == 1
        with page.expect_download() as download:
            page.locator('#notes-export').click()
        path = output / 'temporary-notes.md'; download.value.save_as(path)
        assert prefix + '-edited' in path.read_text(encoding='utf-8')
        card = page.locator(f'.note-card[data-id="{note["id"]}"]')
        card.get_by_text('回到原文', exact=True).click()
        page.locator('.ctx-actions [data-note-inline]').first.wait_for()
        assert urlsplit(page.url).fragment == urlsplit(note['sourceUrl']).fragment
        paragraph = page.locator('.article-body .article-wrap > p').nth(6)
        paragraph.scroll_into_view_if_needed()
        paragraph.evaluate("""el=>{const r=document.createRange();r.selectNodeContents(el);const s=getSelection();s.removeAllRanges();s.addRange(r)}""")
        page.locator('.fav-popover.show').click()
        assert page.evaluate('getSelection().isCollapsed')
        excerpt = get(page, insp_key)[0]
        navigate('favorites.html')
        assert page.locator(f'.collection-full[data-id="{favorite["id"]}"]').count() == 1
        page.locator('[data-collection-tab="inspiration"]').click()
        excerpt_card = page.locator(f'.collection-inspiration[data-id="{excerpt["id"]}"]')
        assert excerpt_card.count() == 1
        excerpt_card.locator('[data-note-from-favorite]').click()
        page.locator('#note-content').fill(prefix + '-excerpt-note')
        page.locator('#note-form').evaluate('form=>form.requestSubmit()')
        excerpt_note = get(page, note_key)[0]
        assert excerpt_note['favoriteId'] == excerpt['id'] and 'fav=' in excerpt_note['sourceUrl']
        page.locator(f'.note-card[data-id="{excerpt_note["id"]}"]').get_by_text('回到原文', exact=True).click()
        page.locator('.article-body .article-wrap > p').nth(6).wait_for()
        page.wait_for_function('scrollY>200')
        assert page.evaluate('getSelection().isCollapsed')
        page.screenshot(path=str(output / 'live-reader-desktop.png'), full_page=False)
        page.set_viewport_size({'width': 390, 'height': 844})
        page.screenshot(path=str(output / 'live-reader-mobile.png'), full_page=False)
        # Preserve the original user's fixture records through a normal logout/login cycle.
        before = get(page, note_key)
        page.locator('.account-logout').click(); login('researcher19')
        navigate('notes.html'); assert page.locator('.note-card').count() == 0
        assert get(page, note_key) == before
        page.locator('.account-logout').click(); login('researcher20')
        navigate('notes.html'); assert get(page, note_key) == before
        assert not errors, errors
        return 'Live asset hashes, local login, header entries, note save/edit/reload/search/export, excerpt/no highlight, note-to-excerpt return, and account namespace isolation passed. No server-side auth/cloud-sync claim.'
    except Exception:
        try: page.screenshot(path=str(output / 'live-failure.png'), full_page=False)
        except Exception: pass
        raise
    finally:
        context.close()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--mode', choices=['fixtures', 'live', 'all'], default='all')
    parser.add_argument('--site', default='https://cyberlawresearch.github.io/cyberlaw-research/')
    parser.add_argument('--chromium')
    parser.add_argument('--output', default='reader-test-results')
    args = parser.parse_args()
    output = Path(args.output); output.mkdir(parents=True, exist_ok=True)
    with sync_playwright() as playwright:
        options = {'headless': True}
        if args.chromium: options['executable_path'] = args.chromium
        browser = playwright.chromium.launch(**options)
        try:
            if args.mode in ('fixtures', 'all'):
                for case in ('title', 'missing-id', 'item', 'existing', 'corrupt-notes', 'corrupt-favorites', 'quota'):
                    record('fixture-note-' + case, lambda case=case: fixture_notes(browser, case))
                record('fixture-excerpt-save-and-deduplicate', lambda: fixture_excerpt_save(browser))
                record('fixture-excerpt-corrupt-store', lambda: fixture_excerpt_save(browser, True))
                for case in ('whitespace', 'ambiguous', 'anchored', 'wrong-page'):
                    record('fixture-excerpt-jump-' + case, lambda case=case: fixture_excerpt_jump(browser, case))
            if args.mode in ('live', 'all'):
                record('deployed-reader-journey', lambda: live_checks(browser, args.site, output))
        finally:
            browser.close()
    report = {'commit': os.environ.get('TEST_COMMIT', ''), 'mode': args.mode, 'results': RESULTS,
              'not_covered': ['factual/legal/bibliographic audit', 'whole-site links and archive completeness', 'server-side authentication security', 'cloud synchronization', 'citation format correctness', 'password changes']}
    (output / 'results.json').write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
    summary = os.environ.get('GITHUB_STEP_SUMMARY')
    if summary:
        with open(summary, 'a', encoding='utf-8') as handle:
            handle.write('# 阅读工具回归检查\n\n' + '\n'.join(f'- {x["status"]}: {x["test"]}' for x in RESULTS) + '\n\n仅覆盖列明的测试，不代表全站内容审核通过。\n')
    return 1 if any(x['status'] != 'passed' for x in RESULTS) else 0


if __name__ == '__main__':
    sys.exit(main())
