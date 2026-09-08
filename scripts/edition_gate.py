"""Validate the declared complete edition and its live reader entry points."""
from __future__ import annotations
import argparse
from datetime import date
import hashlib,json,posixpath,re
from pathlib import Path
from urllib.parse import urljoin,urlsplit
from bs4 import BeautifulSoup
ROOT=Path(__file__).resolve().parents[1]
MANIFEST=ROOT/'data/current-edition.json'
LABELS=['全球科技法简报','域外法学论文精读','法学经典著作','科技法研究新作']
HISTORIES=['briefs.html','papers.html','classics.html','new-works.html']
def soup(path):return BeautifulSoup((ROOT/path).read_text(encoding='utf-8'),'html.parser')
def target(parent,href):
 u=urlsplit(href or '')
 if u.scheme or u.netloc:return None
 return posixpath.normpath(posixpath.join(posixpath.dirname(parent),u.path))
def sync_navigation(paths):
 changed=0
 for file in ROOT.rglob('*.html'):
  if '.git' in file.parts or '.github' in file.parts:continue
  doc=BeautifulSoup(file.read_text(encoding='utf-8'),'html.parser');modified=False
  for a in doc.select('.navlinks a'):
   label=a.get_text(strip=True)
   if label in LABELS:
    href=posixpath.relpath(paths[LABELS.index(label)],file.parent.relative_to(ROOT).as_posix())
    if a.get('href')!=href:a['href']=href;modified=True
  if modified:file.write_text(str(doc),encoding='utf-8');changed+=1
 return changed
def normalized(s):return re.sub(r'[^\w\u4e00-\u9fff]','',s.lower())
def validate(m):
 paths=list(m['pages'].values());day=date.fromisoformat(m['date'])
 assert list(m['pages'])==['brief','paper','classic','newworks']
 assert len(paths)==len(set(paths))==4
 docs=[]
 for p in paths:
  resolved=(ROOT/p).resolve();assert resolved.is_relative_to(ROOT) and resolved.is_file(),p
  assert day.isoformat() in p,p
  d=soup(p);docs.append(d)
  assert d.select_one('main h1') and d.select_one('.article-body'),p
  text=d.select_one('main').get_text(' ',strip=True)
  assert not any(bad in text for bad in ['本期最值得先看','Cyberlaw Research','正文待补','待发布正文','占位内容']),p
  assert d.select_one('.brand').get_text(strip=True)=='网信法研究每日推送'
  for label,dest in zip(LABELS,paths):
   a=next((a for a in d.select('.navlinks a') if a.get_text(strip=True)==label),None)
   assert a is not None and target(p,a.get('href'))==dest,(p,label)
 index=soup('index.html')
 assert [a.get('href') for a in index.select('.portal-card')]==paths
 for label,dest in zip(LABELS,paths):
  a=next((a for a in index.select('.navlinks a') if a.get_text(strip=True)==label),None)
  assert a is not None and a.get('href')==dest,label
 assert all(m['date'].replace('-','.') in n.get_text() for n in index.select('.portal-latest small'))
 assert len(index.select('a[href="archive.html"]'))==1
 archive=soup('archive.html')
 for p,listing in zip(paths,HISTORIES):
  assert archive.select_one(f'a[href="{listing}"]'),listing
  first=soup(listing).select_one('.issue-list .issue-row')
  assert first is not None and first.select_one(f'a[href="{p}"]'),listing
 news=docs[0].select('.brief-item')
 assert len(news)==m['news_count'] and 18<=len(news)<=20
 for n in news:
  assert n.get('id') and n.select_one('h3') and n.select_one('.brief-meta')
  facts=n.select_one('.brief-fact');assert facts and len(facts.get_text(strip=True))>=65
  text=n.get_text(' ',strip=True)
  assert all(label in text for label in ['法治研判','智库选题参考','论文选题']),n['id']
  assert n.select('.source a[href^="https://"]'),n['id']
  assert 0<=(day-date.fromisoformat(n['data-event-date'])).days<=2,n['id']
  c=json.loads(n['data-citation']);assert c['originalTitle'] and c['url']
 titles=[normalized(n.h3.get_text()) for n in news];assert len(titles)==len(set(titles))
 works=docs[3].select('.brief-item');assert len(works)==m['newworks_count']==5
 previous=[]
 for folder in ['articles','papers','new-works']:
  for p in (ROOT/folder).glob('*.html'):
   if p.relative_to(ROOT).as_posix() in paths:continue
   if 'new-work' in p.name or folder=='new-works':previous.append(p.read_text(encoding='utf-8'))
 prior='\n'.join(previous)
 for w in works:
  assert re.search('[\u4e00-\u9fff]',w.h3.get_text())
  c=json.loads(w['data-citation']);assert c['author'] and c['originalTitle'] and c['journal']
  assert int(c['year'])>=day.year-2
  assert c['url'] not in prior,('Previously published source',c['url'])
  if c.get('doi'):assert c['doi'] not in prior,('Previously published DOI',c['doi'])
  assert 100<=len(w.select_one('.work-reading').get_text(strip=True))<=260
 lengths=[len(d.select_one('.article-body').get_text(' ',strip=True)) for d in docs]
 assert lengths[1]>=2500 and lengths[2]>=4500 and lengths[2]>=lengths[1]*1.4,lengths
 for p,d in zip(paths,docs):
  ids=[n['id'] for n in d.select('[id]')];assert len(ids)==len(set(ids)),p
  for a in d.select('main a[href]'):
   dest=target(p,a['href'])
   if dest is not None and urlsplit(a['href']).path:assert (ROOT/dest).is_file(),(p,a['href'])
 return {'date':m['date'],'pages':paths,'news':len(news),'newworks':len(works),'body_lengths':lengths,'status':'passed'}
def browser_check(m,base,output):
 from playwright.sync_api import sync_playwright
 import time
 base=base.rstrip('/')+'/';paths=list(m['pages'].values());results=[]
 with sync_playwright() as p:
  browser=p.chromium.launch();context=browser.new_context()
  for attempt in range(12):
   try:
    response=context.request.get(urljoin(base,'data/current-edition.json')+'?edition-verification='+str(attempt))
    if response.ok and response.json()==m:break
   except Exception:pass
   time.sleep(5)
  else:raise AssertionError('Live manifest does not match the completed edition')
  for path in ['index.html','archive.html']+HISTORIES+paths:
   expected=(ROOT/path).read_bytes()
   for attempt in range(12):
    response=context.request.get(urljoin(base,path)+'?edition-verification='+str(attempt))
    if response.ok and hashlib.sha256(response.body()).digest()==hashlib.sha256(expected).digest():break
    time.sleep(5)
   else:raise AssertionError('Deployed page differs from tested commit: '+path)
  context.close()
  for width,height in [(1440,1000),(390,844)]:
   context=browser.new_context(viewport={'width':width,'height':height})
   context.add_cookies([{'name':'cyberlaw_user','value':'researcher20','url':base,'sameSite':'Lax'}])
   page=context.new_page();errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
   page.goto(urljoin(base,'index.html'),wait_until='networkidle')
   assert page.locator('.portal-card').count()==4
   assert [urlsplit(u).path for u in page.locator('.portal-card').evaluate_all('(xs)=>xs.map(x=>x.href)')]==[urlsplit(urljoin(base,x)).path for x in paths]
   assert page.locator('a[href="archive.html"]').count()==1
   assert page.evaluate('document.documentElement.scrollWidth<=innerWidth+1')
   page.screenshot(path=str(output.parent/f'edition-home-{width}.png'),full_page=True)
   for i,path in enumerate(paths):
    page.goto(urljoin(base,path),wait_until='networkidle')
    assert 'login.html' not in page.url and page.locator('main h1').is_visible()
    assert page.evaluate('document.documentElement.scrollWidth<=innerWidth+1'),path
    if i in [0,3]:
     count=m['news_count'] if i==0 else 5
     assert page.locator('.brief-item').count()==count
     assert page.locator('.brief-item [data-act="related"]').count()==count
    else:assert page.locator('[data-act="cite"]').count()>=1
    assert not page.get_by_text('本期最值得先看',exact=True).count()
    if i==0:page.screenshot(path=str(output.parent/f'edition-brief-{width}.png'))
   assert not errors,errors
   context.close();results.append({'test':f'current-edition-{width}','status':'passed','detail':'Exact deployed bytes, current homepage, four bodies, archive lists and reader controls.'})
  browser.close()
 output.write_text(json.dumps({'date':m['date'],'results':results},ensure_ascii=False,indent=2),encoding='utf-8')
 return results
def main():
 parser=argparse.ArgumentParser();parser.add_argument('--sync-nav',action='store_true');parser.add_argument('--base');parser.add_argument('--output',default='/tmp/edition-check/results.json');args=parser.parse_args()
 if not MANIFEST.exists():print('No completed edition manifest yet; this run cannot certify a new edition.');return
 m=json.loads(MANIFEST.read_text())
 if args.sync_nav:print('Updated navigation:',sync_navigation(list(m['pages'].values())))
 print(json.dumps(validate(m),ensure_ascii=False))
 if args.base:
  output=Path(args.output);output.parent.mkdir(parents=True,exist_ok=True)
  print(json.dumps(browser_check(m,args.base,output),ensure_ascii=False))
if __name__=='__main__':main()
