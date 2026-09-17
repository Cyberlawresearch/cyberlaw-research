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
            browser = p.chromium.launch(executable_path=None if Path(p.chromium.executable_path).exists() else shutil.which('chromium'))
            for width, height in [(1440, 1000), (390, 844)]:
                context = browser.new_context(viewport={'width': width, 'height': height})
                context.add_cookies([{'name':'cyberlaw_user','value':'researcher20','url':base,'sameSite':'Lax'}])
                page = context.new_page()
                errors = []
                page.on('pageerror', lambda error: errors.append(str(error)))

                for asset in ('context-refine.js', 'context-insight.js', 'news-layout-fix.css'):
                    expected = (ROOT/'assets'/asset).read_bytes()
                    for attempt in range(10):
                        response = context.request.get(urljoin(base, f'assets/{asset}?v=context-test-{attempt}'))
                        if response.ok and hashlib.sha256(response.body()).digest() == hashlib.sha256(expected).digest():
                            break
                        time.sleep(6)
                    else:
                        raise AssertionError('Deployed asset differs from the tested commit: ' + asset)

                # Same-event progression: the 17 Sep EU KIDS Act proposal must connect
                # to the 16 Sep policy announcement, but not to broad AI/data stories.
                page.goto(urljoin(base, 'articles/2026-09-17-tech-law-brief.html'), wait_until='networkidle')
                kids = page.locator('#research-item-7')
                kids.locator('[data-act="timeline"]').click()
                panel = kids.locator('.ctx-inline-panel')
                panel.get_by_text('专题时间线', exact=True).wait_for()
                panel.get_by_role('tab', name='未成年人上网与年龄核验', exact=True).wait_for()
                timeline_text = panel.inner_text()
                assert '2026-09-16' in timeline_text and '未满13岁' in timeline_text
                assert '数据中心' not in timeline_text and '芯片' not in timeline_text and '版权' not in timeline_text
                links = panel.locator('.ctx-timeline a')
                assert 1 <= links.count() <= 4
                assert len(links.evaluate_all('(nodes)=>nodes.map(n=>n.href)')) == len(set(links.evaluate_all('(nodes)=>nodes.map(n=>n.href)')))

                # A timeline link must land on the exact historical item anchor.
                link = links.first
                anchor = unquote(urlparse(link.get_attribute('href')).fragment)
                link.click()
                page.wait_for_load_state('networkidle')
                page.locator(f'[id="{anchor}"]').wait_for()
                assert page.locator(f'[id="{anchor}"] h3').count() == 1

                # Related reading may be sparse or empty, but generic same-field material
                # must not be padded in and books must never appear.
                page.goto(urljoin(base, 'articles/2026-09-17-tech-law-brief.html'), wait_until='networkidle')
                agent = page.locator('#research-item-4')
                agent.locator('[data-act="related"]').click()
                r_panel = agent.locator('.ctx-inline-panel')
                r_panel.get_by_text('关联阅读', exact=True).wait_for()
                assert not r_panel.get_by_text('经典著作', exact=True).count()
                assert not r_panel.locator('a[href*="laws-empire"],a[href*="rawls"],a[href*="morality-of-law"]').count()
                related_hrefs = r_panel.locator('.ctx-related a').evaluate_all('(nodes)=>nodes.map(n=>n.href)')
                assert len(related_hrefs) == len(set(related_hrefs))

                # Agent interoperability must no longer automatically create a broad
                # "智能体治理" timeline containing unrelated permission/safety items.
                agent.locator('[data-act="timeline"]').click()
                a_panel = agent.locator('.ctx-inline-panel')
                a_panel.get_by_text('专题时间线', exact=True).wait_for()
                agent_text = a_panel.inner_text()
                assert '数据中心' not in agent_text and '版权' not in agent_text

                # Background/outlook and cite tools still coexist with the stricter panels.
                agent.locator('[data-act="background"]').click()
                a_panel.get_by_text('背景信息与未来前瞻', exact=True).wait_for()
                assert a_panel.get_by_text('背景信息', exact=True).count() == 1
                assert a_panel.get_by_text('未来前瞻', exact=True).count() == 1
                assert a_panel.locator('.ctx-insight-block').count() == 2
                agent.locator('[data-act="cite"]').click()
                a_panel.get_by_text('引用与导出', exact=True).wait_for()

                # Foreign news has an extra original-title row but must keep facts
                # full-width and exactly three research-analysis cards.
                foreign = page.locator('#research-item-16')
                foreign.locator('.brief-original').wait_for()
                layout = foreign.evaluate('''el=>{
                  const rect=n=>{const r=n.getBoundingClientRect();return {x:r.x,y:r.y,width:r.width,height:r.height}};
                  const original=el.querySelector(':scope > .brief-original');
                  const fact=el.querySelector(':scope > .brief-fact');
                  const analysis=[...el.children].filter(n=>n.tagName==='P'&&!n.classList.contains('brief-original')&&!n.classList.contains('brief-fact')&&!n.classList.contains('source'));
                  return {original:rect(original),fact:rect(fact),analysis:analysis.map(rect)};
                }''')
                assert len(layout['analysis']) == 3
                assert abs(layout['original']['width'] - layout['fact']['width']) < 5
                if width > 800:
                    tops = [x['y'] for x in layout['analysis']]
                    assert max(tops) - min(tops) < 5
                    assert all(x['width'] < layout['fact']['width'] * .55 for x in layout['analysis'])
                else:
                    tops = [x['y'] for x in layout['analysis']]
                    assert tops == sorted(tops) and len(set(round(x) for x in tops)) == 3

                assert page.evaluate('document.documentElement.scrollWidth <= window.innerWidth + 1')
                assert not errors, errors
                page.screenshot(path=str(output.parent/f'context-topics-{width}.png'))
                results.append({'test':f'context-ui-{width}','status':'passed','detail':'Direct related-reading links, narrow same-event timelines, background/outlook, exact anchors and foreign-news layout pass responsively.'})
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
