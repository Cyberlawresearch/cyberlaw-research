from pathlib import Path
import json,re,html

ROOT=Path('.')
OUT=ROOT/'assets'
OUT.mkdir(exist_ok=True)

TAG_RULES={
'人工智能':['人工智能','AI','algorithm','算法','模型','大模型','智能体','agentic','generative'],
'数据与隐私':['数据','隐私','个人信息','GDPR','privacy','data protection','数据要素'],
'平台治理':['平台','platform','内容治理','推荐系统','社交媒体'],
'竞争法':['反垄断','竞争','垄断','antitrust','competition'],
'网络安全':['网络安全','cyber','安全事件','漏洞','CISA','关键基础设施'],
'知识产权':['版权','著作权','知识产权','copyright','patent'],
'算法行政':['行政','政府','公共部门','自动化决策','due process','正当程序'],
'国际治理':['欧盟','EU','美国','韩国','日本','新加坡','国际','global','跨境'],
'数字法治':['法治','rule of law','程序','权利','责任','监管'],
}

def strip_tags(s):
    s=re.sub(r'<script\b[^>]*>.*?</script>',' ',s,flags=re.S|re.I)
    s=re.sub(r'<style\b[^>]*>.*?</style>',' ',s,flags=re.S|re.I)
    s=re.sub(r'<[^>]+>',' ',s)
    s=html.unescape(s)
    return re.sub(r'\s+',' ',s).strip()

def first(pattern,s,default=''):
    m=re.search(pattern,s,re.S|re.I)
    return strip_tags(m.group(1)) if m else default

def classify(raw,path):
    t=strip_tags(raw)
    n=path.name
    if 'tech-law-brief' in n: return '全球科技法简报'
    if 'new-works' in n or path.parent.name=='new-works': return '科技法研究新作'
    if '每日法学经典著作' in t or 'LEGAL CLASSIC' in t: return '法学经典著作'
    if '域外法学论文精读' in t or 'CLASSIC PAPERS' in t or 'PAPER' in t: return '域外法学论文精读'
    if path.parent.name=='papers': return '域外法学论文精读'
    return '研究资料'

def tags_for(text):
    low=text.lower(); out=[]
    for tag,words in TAG_RULES.items():
        if any(w.lower() in low for w in words): out.append(tag)
    return out[:6]

def date_for(path,raw):
    m=re.search(r'(20\d{2})[-./年](\d{1,2})[-./月](\d{1,2})',str(path)+' '+strip_tags(raw))
    if not m: return ''
    return f'{int(m.group(1)):04d}-{int(m.group(2)):02d}-{int(m.group(3)):02d}'

def excerpt(text,n=260):
    return text if len(text)<=n else text[:n].rstrip()+'…'

records=[]; ideas=[]
paths=[]
for folder in ['articles','papers','new-works']:
    p=ROOT/folder
    if p.exists(): paths += sorted(p.glob('*.html'))

for path in paths:
    raw=path.read_text(encoding='utf-8',errors='ignore')
    title=first(r'<h1[^>]*>(.*?)</h1>',raw) or first(r'<title[^>]*>(.*?)</title>',raw)
    page_title=first(r'<title[^>]*>(.*?)</title>',raw)
    body=first(r'<main[^>]*>(.*?)</main>',raw) or strip_tags(raw)
    body=re.sub(r'网信法研究每日推送\s*','',body)
    category=classify(raw,path)
    date=date_for(path,raw)
    tags=tags_for(title+' '+body)
    records.append({
        'id':str(path).replace('\\','/'), 'path':str(path).replace('\\','/'),
        'title':title, 'pageTitle':page_title, 'date':date, 'category':category,
        'tags':tags, 'excerpt':excerpt(body), 'text':body[:14000]
    })
    if category=='全球科技法简报':
        for block in re.findall(r'<article\b[^>]*class=["\'][^"\']*brief-item[^"\']*["\'][^>]*>(.*?)</article>',raw,re.S|re.I):
            source=first(r'<h3[^>]*>(.*?)</h3>',block)
            for phtml in re.findall(r'<p\b[^>]*>(.*?)</p>',block,re.S|re.I):
                txt=strip_tags(phtml)
                kind=''
                if txt.startswith('智库选题参考') or '智库选题参考' in txt[:20]: kind='智库选题'
                elif txt.startswith('论文选题') or '论文选题' in txt[:16]: kind='论文选题'
                if not kind: continue
                title_m=re.search(r'《([^》]+)》',txt)
                idea_title=title_m.group(1) if title_m else re.sub(r'^(智库选题参考|论文选题)[:：]?','',txt).split('。',1)[0][:80]
                desc=txt
                ideas.append({'id':f'{path}:{len(ideas)}','kind':kind,'title':idea_title,'description':desc,'source':source,'date':date,'path':str(path).replace('\\','/'),'tags':tags_for(source+' '+txt)})

records.sort(key=lambda x:(x['date'],x['path']),reverse=True)
ideas.sort(key=lambda x:(x['date'],x['id']),reverse=True)
(OUT/'research-index.json').write_text(json.dumps(records,ensure_ascii=False,separators=(',',':')),encoding='utf-8')
(OUT/'idea-index.json').write_text(json.dumps(ideas,ensure_ascii=False,separators=(',',':')),encoding='utf-8')
print(f'indexed {len(records)} pages and {len(ideas)} research ideas')
