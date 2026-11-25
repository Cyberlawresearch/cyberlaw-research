"""Non-destructive quality inspection of the generated website.
Only the media archive's own latest-issue caption is synchronized automatically.
All other candidate defects are reported for review, not silently rewritten.
"""
from __future__ import annotations
from collections import Counter
from pathlib import Path
from urllib.parse import urlsplit, unquote
import json, os, re
from bs4 import BeautifulSoup

def sync_archive_media(root: Path):
    archive=root/'archive.html'
    media=root/'media-ai.html'
    if not archive.is_file() or not media.is_file():
        return
    listing=BeautifulSoup(media.read_text(encoding='utf-8'),'html.parser')
    row=listing.select_one('.issue-list .issue-row')
    if row is None:return
    link=row.select_one('a.issue-action[href]')
    date=row.select_one('.issue-date strong')
    issue=row.select_one('.issue-date span')
    if not (link and date and issue):return
    href=link.get('href','')
    if not re.fullmatch(r'articles/\d{4}-\d{2}-\d{2}-ai-media-digest\.html',href):return
    path=root/href
    if not path.is_file():return
    article=BeautifulSoup(path.read_text(encoding='utf-8'),'html.parser')
    counts=article.select('.article-hero .meta .pill')
    match=next((m for node in counts if (m:=re.search(r'(?:^|[·｜| ])\s*(\d+)\s*篇(?:\s*[·｜| ]|$)',node.get_text(' ',strip=True)))),None)
    if not match:return
    label=f"最新：{date.get_text(strip=True)} · {issue.get_text(strip=True)}（{match.group(1)}篇）"
    text=archive.read_text(encoding='utf-8')
    pattern=r'(<a\b[^>]*href=["\']media-ai\.html["\'][^>]*>\s*<h2>权威媒体AI摘编</h2>\s*<p>)[^<]*(</p>)'
    updated,n=re.subn(pattern,lambda m:m.group(1)+label+m.group(2),text,count=1)
    if n and updated!=text:archive.write_text(updated,encoding='utf-8')
    print('Media archive caption:',label)

def inspect_site(root: Path):
    pages={p.relative_to(root).as_posix():p for p in root.rglob('*.html')
           if not any(x.startswith('.') or x in {'node_modules','dist','build'} for x in p.relative_to(root).parts)}
    identifiers={}; links={}; issues=[]; counts=Counter()
    def add(kind,page,detail):
        counts[kind]+=1;issues.append({'kind':kind,'page':page,'detail':detail})
    for name,path in sorted(pages.items()):
        try:doc=BeautifulSoup(path.read_text(encoding='utf-8'),'html.parser')
        except (UnicodeDecodeError,OSError) as e:
            add('unreadable',name,type(e).__name__);continue
        ids=Counter(x['id'] for x in doc.select('[id]') if x.get('id'))
        identifiers[name]=set(ids)
        for i,n in ids.items():
            if n>1:add('duplicate_id',name,i)
        if not doc.title or not doc.title.get_text(strip=True):add('missing_title',name,'title')
        if not doc.select_one('main h1') and not doc.select_one('h1'):add('missing_heading',name,'h1')
        links[name]=[(a.get('href',''),a.get_text(' ',strip=True)[:60]) for a in doc.select('a[href]')]
    from posixpath import normpath, dirname, join
    for name,items in links.items():
        for href,label in items:
            try:u=urlsplit(href.strip())
            except ValueError:
                add('malformed_link',name,label);continue
            if u.scheme or u.netloc:continue
            path=unquote(u.path)
            if path.startswith('/cyberlaw-research/'):path=path[len('/cyberlaw-research/'):]
            elif path.startswith('/'):continue
            else:path=normpath(join(dirname(name),path)) if path else name
            if path=='.':path='index.html'
            if path.startswith('../') or path.startswith('/'):continue
            if path not in pages and (root/path).is_dir():
                path=normpath(join(path,'index.html'))
            if path not in pages:
                if path.endswith('.html') or not (root/path).exists():add('missing_internal_target',name,href)
                continue
            fragment=unquote(u.fragment)
            if fragment and fragment not in identifiers.get(path,set()):
                # Some legacy reader tools construct IDs at runtime; report as review candidates.
                add('fragment_review',name,href)
    result={'pages':len(pages),'main_pages':sum(not p.startswith('trade-watch/') for p in pages),
            'candidate_counts':dict(counts),'candidates':issues}
    print('Site quality inspection:',json.dumps({k:v for k,v in result.items() if k!='candidates'},ensure_ascii=False))
    for x in issues[:12]:print('Review:',x['kind'],x['page'],x['detail'])
    temp=os.environ.get('RUNNER_TEMP')
    if temp:
        out=Path(temp)/'context-tests'/'site-quality.json'
        out.parent.mkdir(parents=True,exist_ok=True)
        out.write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
    return result

if __name__=='__main__':
    inspect_site(Path(__file__).resolve().parents[1])
