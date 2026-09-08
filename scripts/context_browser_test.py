"""Check contextual reader panels in a disposable browser profile."""
from __future__ import annotations
import argparse
import hashlib
import json
import shutil
import time
from pathlib import Path
from urllib.parse import urljoin, urlparse, unquote
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--base', default='https://cyberlawresearch.github.io/cyberlaw-research/')
    parser.add_argument('--output', default='reader-test-results/context-results.json')
    args = parser.parse_args()
    base = args.base.rstrip('/') + '/'
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    results = []
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(executable_path=None if Path(p.chromium.executable_path).exists() else shutil.which("chromium"))
            for width, height in [(1440, 1000), (390, 844)]:
                context = browser.new_context(viewport={'width': width, 'height': height})
                context.add_cookies([{'name':'cyberlaw_user','value':'researcher20','url':base,'sameSite':'Lax'}])
                page = context.new_page()
                errors = []
                page.on('pageerror', lambda error: errors.append(str(error)))
                expected = (ROOT/'assets/context-refine.js').read_bytes()
                for attempt in range(10):
                    response = context.request.get(urljoin(base, f'assets/context-refine.js?v=context-test-{attempt}'))
                    if response.ok and hashlib.sha256(response.body()).digest() == hashlib.sha256(expected).digest():
                        break
                    time.sleep(6)
                else:
                    raise AssertionError('Deployed script differs from the tested commit')
                page.goto(urljoin(base, 'articles/2026-09-07-tech-law-brief.html'), wait_until='networkidle')
                item = page.locator('#research-item-2')
                item.locator('[data-act="timeline"]').click()
                panel = item.locator('.ctx-inline-panel')
                panel.get_by_role('tab', name='算力互联与资源调度', exact=True).wait_for()
                tabs = panel.get_by_role('tab')
                assert tabs.count() == 2
                assert tabs.nth(1).inner_text() == '智能体治理'
                first = panel.get_by_role('tabpanel').inner_text()
                assert '算力网' in first and '德国网站' not in first
                tabs.nth(1).click()
                second = panel.get_by_role('tabpanel').inner_text()
                assert '数据智能体' in second and '国家数据局调研内蒙古' not in second
                assert panel.locator('[role="tabpanel"]:visible').count() == 1
                dates = panel.locator('[role="tabpanel"]:visible time').all_text_contents()
                assert dates == sorted(dates) and 1 <= len(dates) <= 4
                tabs.nth(1).press('Home')
                assert tabs.nth(0).get_attribute('aria-selected') == 'true'
                item.locator('[data-act="related"]').click()
                panel.get_by_text('关联阅读', exact=True).wait_for()
                assert not panel.get_by_text('经典著作', exact=True).count()
                assert not panel.locator('a[href*="laws-empire"],a[href*="rawls"],a[href*="morality-of-law"]').count()
                assert panel.locator('.ctx-related a').count() > 0
                item.locator('[data-act="cite"]').click()
                panel.get_by_text('引用与导出', exact=True).wait_for()
                item.locator('[data-act="timeline"]').click()
                panel.get_by_role('tab', name='算力互联与资源调度', exact=True).wait_for()
                assert panel.get_by_role('tabpanel').inner_text() == first
                news = page.locator('#research-item-10')
                news.locator('[data-act="timeline"]').click()
                n_panel = news.locator('.ctx-inline-panel')
                n_panel.get_by_role('tab', name='AI安全事件与披露义务', exact=True).wait_for()
                assert n_panel.get_by_role('tab').count() == 2
                assert n_panel.get_by_role('tab').nth(1).inner_text() == '智能体治理'
                assert n_panel.get_by_role('tab', name='智能体治理', exact=True).count() == 1
                assert panel.get_by_role('tab', name='智能体治理', exact=True).count() == 1
                assert not page.get_by_role('tab', name='智能体权限与越权行为', exact=True).count()
                assert not page.get_by_role('tab', name='智能体网络与互操作规范', exact=True).count()
                all_links = n_panel.locator('.ctx-timeline a').evaluate_all('(nodes)=>nodes.map(n=>n.href)')
                assert len(all_links) == len(set(all_links))
                text = n_panel.inner_text()
                assert '版权' not in text and '数据中心' not in text
                n_panel.scroll_into_view_if_needed()
                page.screenshot(path=str(output.parent/f'context-topics-{width}.png'))
                assert page.evaluate('document.documentElement.scrollWidth <= window.innerWidth + 1')
                n_panel.get_by_role('tab').nth(1).click()
                link = n_panel.locator('[role="tabpanel"]:visible a').first
                anchor = unquote(urlparse(link.get_attribute('href')).fragment)
                link.click()
                page.wait_for_load_state('networkidle')
                page.locator(f'[id="{anchor}"]').wait_for()
                assert page.locator(f'[id="{anchor}"] h3').count() == 1
                assert not errors, errors
                results.append({'test':f'context-ui-{width}','status':'passed','detail':'No books; permissions and interoperability share one agent governance tab; distinct factual topics; sorted news; panel switching; exact anchor; responsive layout.'})
                context.close()
            browser.close()
    except Exception as error:
        results.append({'test':'context-browser','status':'failed','detail':str(error)})
        raise
    finally:
        output.write_text(json.dumps({'results':results}, ensure_ascii=False, indent=2), encoding='utf-8')
        print(json.dumps({'results':results}, ensure_ascii=False, indent=2))

if __name__ == '__main__':
    main()
