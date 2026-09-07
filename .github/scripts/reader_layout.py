"""Additional viewport and exact excerpt-return assertions; no production data writes."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import sys
from urllib.parse import urljoin
import uuid

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[2]
# Minimal reproduction of the existing header rules, not a replacement site stylesheet.
BASE_CSS = '''*{box-sizing:border-box}body{margin:0;line-height:1.8}.wrap{max-width:1120px;margin:0 auto;padding:0 24px}.top{position:sticky;top:0}.nav{min-height:70px;display:flex;align-items:center;justify-content:space-between;gap:24px}.brand{font-size:20px;font-weight:700;letter-spacing:.04em;text-decoration:none}.navlinks{display:flex;gap:20px;font-size:14px;flex-wrap:wrap}@media(max-width:800px){.nav{align-items:flex-start;padding-top:18px;padding-bottom:18px}.navlinks{display:none}}'''
HEADER = '''<header class="top"><div class="wrap nav"><a class="brand">网信法研究每日推送</a><nav class="navlinks"><a>全球科技法简报</a><a>域外法学论文精读</a><a>法学经典著作</a><a>科技法研究新作</a><a>历史记录</a></nav><div class="account-nav"><a class="account-favorites">我的收藏</a><a class="account-notes">我的笔记</a><a class="account-settings">账号设置</a><span class="account-user">researcher20</span><button class="account-logout">退出</button></div></div></header>'''
RESULTS = []


def header_metrics(page):
    return page.evaluate('''() => {
      const brand=document.querySelector('.brand'), header=document.querySelector('.top');
      const b=brand.getBoundingClientRect(), h=header.getBoundingClientRect();
      const controls=[...document.querySelectorAll('.account-nav>a,.account-nav>button')].map(x=>x.getBoundingClientRect());
      return {brand:brand.textContent.trim(),brandHeight:b.height,headerHeight:h.height,
        brandFits:b.left>=0&&b.right<=innerWidth,
        controlsFit:controls.length===4&&controls.every(r=>r.width>0&&r.left>=0&&r.right<=innerWidth),
        overflow:document.documentElement.scrollWidth>innerWidth+1};
    }''')


def assert_header(page):
    result = header_metrics(page)
    assert result['brand'] == '网信法研究每日推送', result
    assert result['brandHeight'] <= 45 and result['headerHeight'] <= 180, result
    assert result['brandFits'] and result['controlsFit'] and not result['overflow'], result
    return result


def fixture(browser, width):
    context = browser.new_context(viewport={'width': width, 'height': 900}, offline=True)
    try:
        page = context.new_page()
        page.set_content('<style>' + BASE_CSS + (ROOT / 'assets/auth.css').read_text() + '</style>' + HEADER)
        return assert_header(page)
    finally:
        context.close()


def live(browser, site, output):
    site = site.rstrip('/') + '/'
    context = browser.new_context(viewport={'width': 1440, 'height': 1000})
    page = context.new_page(); page.set_default_timeout(20000)
    errors = []; page.on('pageerror', lambda error: errors.append(str(error)))
    token = uuid.uuid4().hex
    checks = []
    try:
        for asset in ('auth.css', 'auth.js'):
            expected = hashlib.sha256((ROOT / 'assets' / asset).read_bytes()).hexdigest()
            response = context.request.get(urljoin(site, 'assets/' + asset) + '?check=' + token)
            assert response.status == 200 and hashlib.sha256(response.body()).hexdigest() == expected, asset
        page.goto(urljoin(site, 'login.html'), wait_until='domcontentloaded')
        # Temporary browser-local credential in a fresh profile, never a server-side password reset.
        page.evaluate('''password=>{
          let h=0x811c9dc5;for(const c of `researcher20|${password}`){h^=c.charCodeAt(0);h=Math.imul(h,0x01000193)>>>0}
          localStorage.setItem('cyberlawPasswordVersion::researcher20','3');
          localStorage.setItem('cyberlawPasswordOverride::researcher20',String(h>>>0));
        }''', token)
        page.locator('#login-user').fill('researcher20'); page.locator('#login-password').fill(token)
        page.locator('#login-form').evaluate('form=>form.requestSubmit()')
        page.locator('.account-user').wait_for()
        checks.append({'page': 'index.html', 'width': 1440, **assert_header(page)})
        article = 'articles/2026-09-02-lessig-code.html'
        page.goto(urljoin(site, article), wait_until='domcontentloaded')
        page.locator('.ctx-actions [data-note-inline]').first.wait_for()
        paragraph = page.locator('.article-body .article-wrap > p').nth(6)
        paragraph.scroll_into_view_if_needed()
        paragraph.evaluate('''el=>{const r=document.createRange();r.selectNodeContents(el);const s=getSelection();s.removeAllRanges();s.addRange(r)}''')
        page.locator('.fav-popover.show').click()
        excerpt = page.evaluate("JSON.parse(localStorage.getItem('cyberlawInspirationFavoritesV2::researcher20'))[0]")
        for width, height, label in ((1440, 1000, 'desktop'), (390, 844, 'mobile')):
            page.set_viewport_size({'width': width, 'height': height})
            page.goto(urljoin(site, 'favorites.html'), wait_until='domcontentloaded')
            page.locator('[data-collection-tab="inspiration"]').click()
            card = page.locator(f'.collection-inspiration[data-id="{excerpt["id"]}"]')
            card.get_by_text('回到原文', exact=True).click()
            page.locator('.article-body .article-wrap > p').nth(6).wait_for()
            # Test the destination paragraph, not merely a nonzero scroll position.
            page.wait_for_function('''() => {
              const p=document.querySelectorAll('.article-body .article-wrap > p')[6];
              if(!p)return false;const r=p.getBoundingClientRect(),h=document.querySelector('.top').getBoundingClientRect();
              return r.top>=h.bottom && r.bottom<=innerHeight && Math.abs(r.top+r.height/2-innerHeight/2)<70;
            }''')
            page.wait_for_timeout(400)
            geometry = paragraph.evaluate('''p=>{const r=p.getBoundingClientRect();return {top:r.top,bottom:r.bottom,text:p.textContent.replace(/\\s+/g,' ').trim()}}''')
            assert geometry['text'] == excerpt['text'], geometry
            assert page.evaluate('getSelection().isCollapsed')
            checks.append({'page': article, 'width': width, 'excerptTop': geometry['top'], 'excerptBottom': geometry['bottom'], **assert_header(page)})
            page.screenshot(path=str(output / ('precise-excerpt-' + label + '.png')))
        for width in (320, 390, 768, 820):
            page.set_viewport_size({'width': width, 'height': 900})
            page.goto(urljoin(site, 'index.html'), wait_until='domcontentloaded')
            page.locator('.account-user').wait_for()
            checks.append({'page': 'index.html', 'width': width, **assert_header(page)})
            if width == 390:
                page.screenshot(path=str(output / 'homepage-mobile.png'))
        assert not errors, errors
        return checks
    except Exception:
        try: page.screenshot(path=str(output / 'layout-failure.png'))
        except Exception: pass
        raise
    finally:
        context.close()


def record(name, function):
    try:
        detail = function()
        RESULTS.append({'test': name, 'status': 'passed', 'detail': detail})
        print('PASS', name, flush=True)
    except Exception as error:
        RESULTS.append({'test': name, 'status': 'failed', 'detail': str(error)[:3000]})
        print('FAIL', name, str(error)[:500], flush=True)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--mode', choices=('fixtures', 'all'), default='all')
    parser.add_argument('--site', default='https://cyberlawresearch.github.io/cyberlaw-research/')
    parser.add_argument('--chromium')
    parser.add_argument('--output', default='reader-test-results')
    args = parser.parse_args(); output = Path(args.output); output.mkdir(parents=True, exist_ok=True)
    with sync_playwright() as playwright:
        options = {'headless': True}
        if args.chromium: options['executable_path'] = args.chromium
        browser = playwright.chromium.launch(**options)
        try:
            for width in (320, 390, 768, 820, 1440):
                record('header-fixture-' + str(width), lambda width=width: fixture(browser, width))
            if args.mode == 'all':
                record('deployed-header-and-precise-excerpt-return', lambda: live(browser, args.site, output))
        finally:
            browser.close()
    (output / 'layout-results.json').write_text(json.dumps({'commit': os.environ.get('TEST_COMMIT', ''), 'results': RESULTS}, ensure_ascii=False, indent=2))
    if os.environ.get('GITHUB_STEP_SUMMARY'):
        with open(os.environ['GITHUB_STEP_SUMMARY'], 'a') as handle:
            handle.write('\n## 移动导航与原文准确定位\n\n' + '\n'.join(f'- {r["status"]}: {r["test"]}' for r in RESULTS) + '\n')
    return 1 if any(r['status'] == 'failed' for r in RESULTS) else 0


if __name__ == '__main__':
    sys.exit(main())
