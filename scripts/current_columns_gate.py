"""Validate and sync independently published current columns."""
from __future__ import annotations
import argparse, hashlib, json, posixpath, re, time
from datetime import date
from pathlib import Path
from urllib.parse import urljoin, urlsplit
from urllib.request import Request, urlopen
from bs4 import BeautifulSoup

ROOT=Path(__file__).resolve().parents[1]
MANIFEST=ROOT/'data/current-edition.json'
KEYS=['brief','paper','classic','newworks']
LABELS=['全球科技法简报','域外法学论文精读','法学经典著作','科技法研究新作']
HISTORIES=['briefs.html','papers.html','classics.html','new-works.html']

def soup(path):
    return BeautifulSoup((ROOT/path).read_text(encoding='utf-8'),'html.parser')

def target(parent,href):
    u=urlsplit(href or '')
    if u.scheme or u.netloc:return None
    return posixpath.normpath(posixpath.join(posixpath.dirname(parent),u.path))

def sync_navigation(paths):
    changed=0
    for file in ROOT.rglob('*.html'):
        if '.git' in file.parts or '.github' in file.parts:continue
        d=BeautifulSoup(file.read_text(encoding='utf-8'),'html.parser');modified=False
        parent=file.parent.relative_to(ROOT).as_posix()
        for a in d.select('.navlinks a'):
            label=a.get_text(strip=True)
            if label in LABELS:
                href=posixpath.relpath(paths[LABELS.index(label)],parent)
                if a.get('href')!=href:a['href']=href;modified=True
        if modified:
            file.write_text(str(d),encoding='utf-8');changed+=1
    return changed

def validate(m):
    assert list(m.get('pages',{}))==KEYS
    assert list(m.get('page_dates',{}))==KEYS
    paths=[m['pages'][k] for k in KEYS]
    days={k:date.fromisoformat(m['page_dates'][k]) for k in KEYS}
    assert max(days.values()).isoformat()==m['date']
    assert len(set(paths))==4
    docs=[]
    for key,p in zip(KEYS,paths):
        f=(ROOT/p).resolve();assert f.is_relative_to(ROOT) and f.is_file(),p
        assert days[key].isoformat() in Path(p).name,(key,p)
        d=soup(p);docs.append(d)
        assert d.select_one('main h1') and d.select_one('.article-body'),p
        assert d.select_one('.brand') and d.select_one('.brand').get_text(strip=True)=='网信法研究每日推送'
        text=d.select_one('main').get_text(' ',strip=True)
        assert not any(x in text for x in ['本期最值得先看','正文待补','待发布正文','占位内容']),p
        for label,dest in zip(LABELS,paths):
            a=next((x for x in d.select('.navlinks a') if x.get_text(strip=True)==label),None)
            assert a is not None and target(p,a.get('href'))==dest,(p,label)
    home=soup('index.html');cards=home.select('.portal-card')
    assert [a.get('href') for a in cards]==paths
    stamps=home.select('.portal-latest small');assert len(stamps)==4
    for key,node in zip(KEYS,stamps):assert m['page_dates'][key].replace('-','.') in node.get_text(),key
    assert len(home.select('a[href="archive.html"]'))==1
    for p,listing in zip(paths,HISTORIES):
        first=soup(listing).select_one('.issue-list .issue-row')
        assert first is not None and first.select_one(f'a[href="{p}"]'),listing
    news=docs[0].select('.brief-item');assert len(news)==m['news_count'] and 18<=len(news)<=20
    for n in news:
        assert n.get('id') and n.select_one('h3') and n.select_one('.brief-meta')
        facts=n.select_one('.brief-fact');assert facts and len(facts.get_text(strip=True))>=65
        txt=n.get_text(' ',strip=True);assert all(x in txt for x in ['法治研判','智库选题参考','论文选题'])
        assert n.select('.source a[href^="https://"]')
        assert 0<=(days['brief']-date.fromisoformat(n['data-event-date'])).days<=2
        c=json.loads(n['data-citation']);assert c.get('originalTitle') and c.get('url')
    works=docs[3].select('.brief-item');assert len(works)==m['newworks_count']==5
    assert len(docs[1].select_one('.article-body').get_text(' ',strip=True))>=2500
    assert len(docs[2].select_one('.article-body').get_text(' ',strip=True))>=4500
    return {'date':m['date'],'page_dates':m['page_dates'],'pages':paths,'news':len(news),'newworks':len(works),'status':'passed'}

def read_url(url):
    req=Request(url,headers={'User-Agent':'cyberlaw-current-columns-gate'})
    with urlopen(req,timeout=20) as r:return r.read()

def remote_check(m,base):
    base=base.rstrip('/')+'/';paths=['index.html','archive.html',*HISTORIES,*m['pages'].values(),'data/current-edition.json']
    for attempt in range(12):
        try:
            if json.loads(read_url(urljoin(base,'data/current-edition.json')+'?v='+str(attempt)))==m:break
        except Exception:pass
        time.sleep(5)
    else:raise AssertionError('live manifest mismatch')
    for path in paths[:-1]:
        expected=(ROOT/path).read_bytes()
        for attempt in range(12):
            try:
                actual=read_url(urljoin(base,path)+'?v='+str(attempt))
                if hashlib.sha256(actual).digest()==hashlib.sha256(expected).digest():break
            except Exception:pass
            time.sleep(5)
        else:raise AssertionError('deployed page differs: '+path)
    return {'remote':'passed','base':base}

def main():
    p=argparse.ArgumentParser();p.add_argument('--sync-nav',action='store_true');p.add_argument('--base');args=p.parse_args()
    m=json.loads(MANIFEST.read_text(encoding='utf-8'))
    if args.sync_nav:print('Updated navigation:',sync_navigation([m['pages'][k] for k in KEYS]))
    print(json.dumps(validate(m),ensure_ascii=False))
    if args.base:print(json.dumps(remote_check(m,args.base),ensure_ascii=False))

if __name__=='__main__':main()
