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
    manifest = json.loads((ROOT/'data/current-edition.json').read_text(encoding='utf-8'))
    current_brief = manifest['pages']['brief']
    current_news_count = manifest['news_count']
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(executable_path=None if Path(p.chromium.executable_path).exists() else shutil.which('chromium'))
            for width, height in [(1440, 1000), (390, 844)]:
                context = browser.new_context(viewport={'width': width, 'height': height})
                context.add_cookies([{'name':'cyberlaw_user','value':'researcher20','url':base,'sameSite':'Lax'}])
                page = context.new_page()
                errors = []
                page.on('pageerror', lambda error: errors.append(str(error)))

                for asset in ('context-refine.js', 'context-insight.js', 'news-layout-fix.css', 'research-tools.js', 'account.js', 'research-tools.css'):
                    expected = (ROOT/'assets'/asset).read_bytes()
                    for attempt in range(10):
                        response = context.request.get(urljoin(base, f'assets/{asset}?v=context-test-{attempt}'))
                        if response.ok and hashlib.sha256(response.body()).digest() == hashlib.sha256(expected).digest():
                            break
                        time.sleep(6)
                    else:
                        raise AssertionError('Deployed asset differs from the tested commit: ' + asset)

                # Always verify the brief currently exposed by current-edition.json.
                page.goto(urljoin(base, current_brief), wait_until='networkidle')
                current_items = page.locator('.brief-item')
                assert current_items.count() == current_news_count
                assert current_items.count() >= 10
                assert page.locator('.brief-fact').count() == current_news_count
                assert page.locator('.source a[href^="https://"]').count() >= current_news_count

                current_first = current_items.first
                assert current_first.locator('[data-act="background"]').count() == 1
                current_first.locator('[data-act="background"]').click()
                current_panel = current_first.locator('.ctx-inline-panel')
                current_panel.get_by_text('背景信息与未来前瞻', exact=True).wait_for()
                assert current_panel.locator('.ctx-insight-block').count() == 2

                assert current_first.locator('[data-act="related"]').count() == 1
                current_first.locator('[data-act="related"]').click()
                current_panel.get_by_text('关联阅读', exact=True).wait_for()

                current_foreign = page.locator('.brief-item:has(.brief-original)').first
                assert current_foreign.count() == 1
                current_layout = current_foreign.evaluate('''el=>{
                  const rect=n=>{const r=n.getBoundingClientRect();return {x:r.x,y:r.y,width:r.width,height:r.height}};
                  const original=el.querySelector(':scope > .brief-original');
                  const fact=el.querySelector(':scope > .brief-fact');
                  const analysis=[...el.children].filter(n=>n.tagName==='P'&&!n.classList.contains('brief-original')&&!n.classList.contains('brief-fact')&&!n.classList.contains('source'));
                  return {original:rect(original),fact:rect(fact),analysis:analysis.map(rect)};
                }''')
                assert len(current_layout['analysis']) == 3
                assert abs(current_layout['original']['width'] - current_layout['fact']['width']) < 5
                if width > 800:
                    current_tops = [x['y'] for x in current_layout['analysis']]
                    assert max(current_tops) - min(current_tops) < 5
                    assert all(x['width'] < current_layout['fact']['width'] * .55 for x in current_layout['analysis'])
                else:
                    current_tops = [x['y'] for x in current_layout['analysis']]
                    assert current_tops == sorted(current_tops) and len(set(round(x) for x in current_tops)) == 3

                assert page.evaluate('document.documentElement.scrollWidth <= window.innerWidth + 1')
                assert not errors, errors
                results.append({'test':f'current-brief-{width}','status':'passed','detail':f'{current_brief} passes current news count, contextual tools and responsive foreign-news layout.'})

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
                # Tool regressions use an isolated browser and synthetic account data.
                page.goto(urljoin(base, 'search.html'), wait_until='domcontentloaded')
                page.wait_for_function("Array.from(document.querySelector('#search-cat').options).some(o=>o.value==='科技法技术基础')")
                page.locator('#search-cat').select_option(label='科技法技术基础')
                assert page.locator('#search-count').inner_text() == '56'
                assert page.locator('#search-results .result-card').count() == 30
                page.locator('[data-search-page="next"]').click()
                assert page.locator('#search-results .result-card').count() == 26
                page.locator('#search-q').fill('Token')
                assert 0 < int(page.locator('#search-count').inner_text()) <= 56
                page.locator('#search-reset').click()
                assert int(page.locator('#search-count').inner_text()) > 120
                assert page.locator('#search-results .result-card').count() == 30
                page.locator('#search-cat').select_option(label='权威媒体AI摘编')
                assert int(page.locator('#search-count').inner_text()) > 0
                assert page.evaluate('document.documentElement.scrollWidth <= window.innerWidth + 1')
                page.goto(urljoin(base,'account.html'),wait_until='domcontentloaded')
                page.evaluate("""() => {
                  localStorage.setItem('cyberlawFullFavoritesV2::researcher20',JSON.stringify([{id:'test-favorite',title:'测试收藏'}]));
                  localStorage.setItem('cyberlawNotesV1::researcher20',JSON.stringify([{id:'test-note',title:'测试笔记'}]));
                  localStorage.setItem('cyberlawIdeaStateV2::researcher20',JSON.stringify({'test-idea':'待研究'}));
                }""")
                page.reload(wait_until='domcontentloaded')
                assert '完整收藏 1 项' in page.locator('#account-storage-summary').inner_text()
                assert '笔记 1 条' in page.locator('#account-storage-summary').inner_text()
                with page.expect_download() as info:
                    page.locator('#account-export').click()
                data=json.loads(Path(info.value.path()).read_text(encoding='utf-8'))
                assert set(data)=={'schema','version','account','exportedAt','collections','excerpts','notes','ideaStates'}
                assert data['collections'][0]['id']=='test-favorite' and data['notes'][0]['id']=='test-note'
                assert page.evaluate('document.documentElement.scrollWidth <= window.innerWidth + 1')
                assert not errors, errors
                results.append({'test':f'research-tools-{width}','status':'passed','detail':'Search counts, course/media filters, pagination, responsive layout and private local-data export passed.'})
                # Presence UI test: no real account credentials or online events in CI.
                presence_api = 'https://btgmuyuhmjzgxmpkglah.supabase.co/functions/v1/site-presence'
                calls = []
                def presence_stub(route):
                    request = route.request
                    headers = {'Access-Control-Allow-Origin': '*', 'Access-Control-Allow-Headers': 'content-type, apikey, authorization', 'Access-Control-Allow-Methods': 'POST, OPTIONS', 'Content-Type': 'application/json'}
                    if request.method == 'OPTIONS':
                        route.fulfill(status=204, headers=headers, body='')
                        return
                    data = request.post_data_json
                    calls.append({k: v for k, v in data.items() if k != 'key'})
                    good = data.get('key') == 'a' * 64
                    if not good:
                        route.fulfill(status=401, headers=headers, body=json.dumps({'ok':False,'error':'unauthorized'}))
                    elif data['action'] == 'verify' and data.get('account') == 'researcher02':
                        route.fulfill(status=200, headers=headers, body=json.dumps({'ok':True,'account':'researcher02','admin':True}))
                    elif data['action'] == 'online':
                        route.fulfill(status=200, headers=headers, body=json.dumps({'ok':True,'online':[{'account':'researcher02','last_seen':'2026-11-25T11:00:00Z'},{'account':'researcher03','last_seen':'2026-11-25T11:01:00Z'}]}))
                    elif data['action'] == 'history':
                        assert data.get('days') in (7,30,90,366,400)
                        assert isinstance(data.get('page'),int)
                        rows=[{'active_date':'2026-11-25','account':'researcher02','first_seen':'2026-11-25T10:00:00Z','last_seen':'2026-11-25T11:00:00Z'},{'active_date':'2026-11-24','account':'researcher03','first_seen':'2026-11-24T10:00:00Z','last_seen':'2026-11-24T11:01:00Z'}]
                        if data.get('account'):
                            rows=[row for row in rows if row['account']==data['account']]
                        route.fulfill(status=200, headers=headers, body=json.dumps({'ok':True,'rows':rows,'total':len(rows),'page':1,'page_size':50}))
                    else:
                        route.fulfill(status=403, headers=headers, body=json.dumps({'ok':False,'error':'forbidden'}))
                context.route(presence_api, presence_stub)
                page.goto(urljoin(base,'account.html'), wait_until='domcontentloaded')
                assert page.locator('#presence-admin').is_hidden()
                context.add_cookies([{'name':'cyberlaw_user','value':'researcher02','url':base,'sameSite':'Lax'}])
                page.reload(wait_until='domcontentloaded')
                page.locator('#presence-verify-form').wait_for()
                assert page.locator('#presence-dashboard').is_hidden()
                assert not calls, 'legacy cookie alone must not query the backend'
                page.locator('#presence-verify-key').fill('b'*64)
                page.locator('#presence-verify-form button').click()
                page.wait_for_function("document.getElementById('presence-status').textContent.includes('不正确')")
                assert page.locator('#presence-dashboard').is_hidden()
                page.locator('#presence-verify-key').fill('a'*64)
                page.locator('#presence-verify-form button').click()
                page.locator('#presence-dashboard').wait_for()
                assert page.locator('#presence-count').inner_text() == '2'
                assert page.locator('.presence-row').count() == 2
                page.wait_for_function("document.getElementById('presence-history-status').textContent.includes('共 2 条')")
                assert page.locator('#presence-history-rows tr').count()==2
                page.locator('#presence-history-days').select_option('400')
                page.wait_for_function("!document.getElementById('presence-history-days').disabled")
                page.locator('#presence-history-account').select_option('researcher03')
                page.wait_for_function("document.getElementById('presence-history-status').textContent.includes('共 1 条')")
                assert 'researcher03' in page.locator('#presence-history-rows').inner_text()
                assert 'researcher02' not in page.locator('#presence-history-rows').inner_text()
                assert any(x.get('action')=='history' and x.get('days')==400 and x.get('account')=='researcher03' for x in calls)
                assert all(set(x) <= {'action','account','days','page'} for x in calls)
                assert page.evaluate('document.documentElement.scrollWidth <= window.innerWidth + 1')
                page.locator('#presence-disconnect').click()
                assert page.locator('#presence-dashboard').is_hidden()
                assert page.evaluate("sessionStorage.getItem('technologyLawPresenceSessionV1') === null")
                assert page.locator('#presence-history-rows tr').count()==0
                context.unroute(presence_api, presence_stub)
                results.append({'test':f'presence-admin-{width}','status':'passed','detail':'Non-admin hidden, legacy cookie alone rejected, verified 02 dashboard, logout removes token, no page paths, mobile layout; mock API.'})
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
