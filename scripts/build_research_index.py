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

# More specific issue markers used for item-level news timelines.  These are deliberately
# narrower than the broad site taxonomy so that a timeline only keeps genuinely related news.
NEWS_TOPIC_RULES={
'智能体AI':['智能体','agentic','agent ','AI agent','自主代理'],
'生成式AI':['生成式AI','生成式人工智能','generative ai','大模型','基础模型','foundation model'],
'AI安全':['AI安全','模型安全','前沿模型','失控','对齐','红队','incident disclosure','事故披露'],
'AI行政应用':['政府大模型','政务助手','公共部门AI','行政自动化','自动化行政','AI政务'],
'算法歧视':['算法歧视','algorithmic discrimination','招聘算法','就业算法','公平性'],
'自动化决策':['自动化决策','automated decision','ADM','算法决定'],
'数据要素':['数据要素','公共数据','数据产品','数据交易','数据市场','授权运营'],
'数据跨境':['数据跨境','跨境数据','cross-border data','数据出境'],
'个人信息保护':['个人信息','隐私','GDPR','data protection','PIPL','删除权','被遗忘权'],
'生物识别':['生物识别','人脸识别','面部识别','biometric','facial recognition'],
'儿童数据':['儿童','未成年人','children','minor','kids'],
'平台责任':['平台责任','内容治理','推荐算法','平台治理','social media','在线平台'],
'反垄断':['反垄断','antitrust','垄断','市场支配','competition authority'],
'平台竞争':['平台竞争','二选一','自我优待','self-preferencing','应用商店','app store'],
'知识产权':['知识产权','版权','著作权','copyright','patent'],
'AI训练版权':['AI训练','训练数据','fair use','合理使用','版权训练','训练版权'],
'网络安全':['网络安全','cybersecurity','漏洞','入侵','勒索','ransomware'],
'关键基础设施':['关键基础设施','critical infrastructure','基础设施安全','反破坏'],
'后量子密码':['后量子','post-quantum','PQC','量子密码'],
'芯片与出口管制':['芯片','半导体','出口管制','export control','GPU','先进计算'],
'算力基础设施':['算力','数据中心','compute','token','词元','算力网'],
'深度伪造':['深度伪造','deepfake','合成内容','数字水印'],
'选举与AI':['选举','election','投票','选民','campaign'],
'自主武器':['自主武器','autonomous weapon','LAWS','致命自主武器'],
'国家安全':['国家安全','national security','军事','国防','军方'],
'国际AI治理':['AI治理','人工智能治理','AI Act','AI Office','全球AI治理','国际规则'],
'竞争与知识产权':['知识产权反垄断','IP antitrust','patent antitrust'],
}

STOPWORDS={
'中国','美国','欧盟','英国','韩国','日本','新加坡','澳大利亚','巴西','印度','德国','法国',
'发布','公布','表示','提出','推进','推动','加强','监管','管理','政策','规则','办法','意见','计划',
'人工智能','科技','数字','网络','数据','平台','研究','关于','相关','进一步','正式','最新','今日','昨日'
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

def news_topics_for(text):
    low=text.lower(); out=[]
    for tag,words in NEWS_TOPIC_RULES.items():
        if any(w.lower() in low for w in words): out.append(tag)
    return out

def date_for(path,raw):
    m=re.search(r'(20\d{2})[-./年](\d{1,2})[-./月](\d{1,2})',str(path)+' '+strip_tags(raw))
    if not m: return ''
    return f'{int(m.group(1)):04d}-{int(m.group(2)):02d}-{int(m.group(3)):02d}'

def item_date(meta,page_date):
    m=re.search(r'(?:(20\d{2})年)?(\d{1,2})月(\d{1,2})日',meta)
    if not m: return page_date
    year=m.group(1) or (page_date[:4] if page_date else '')
    return f'{int(year):04d}-{int(m.group(2)):02d}-{int(m.group(3)):02d}' if year else page_date

def excerpt(text,n=260):
    return text if len(text)<=n else text[:n].rstrip()+'…'

def keywords_for(title,meta,text):
    src=' '.join([title,meta,text[:800]])
    keys=[]
    # Latin acronyms/product names and compact legal/technical expressions.
    for tok in re.findall(r'\b[A-Z][A-Z0-9.-]{1,12}\b|\b[A-Za-z][A-Za-z0-9.-]{2,24}\b',src):
        if tok.lower() not in {'the','and','for','with','from','this','that','law','legal'}:
            keys.append(tok)
    # Quoted Chinese phrases and organization/product-like chunks are useful entity signals.
    for tok in re.findall(r'[“《]([^”》]{2,18})[”》]',src):
        keys.append(tok)
    # Named organizations / technologies ending in common institutional suffixes.
    for tok in re.findall(r'[\u4e00-\u9fffA-Za-z0-9·]{2,18}(?:委员会|管理局|法院|检察院|部|局|署|公司|平台|模型|法案|条例|指令|数据库|中心)',src):
        keys.append(tok)
    # Short title chunks provide similarity without turning every generic Chinese word into a key.
    cleaned=re.sub(r'^\s*\d+[.、]\s*','',title)
    for part in re.split(r'[：:，,；;、“”《》()（）\-—]',cleaned):
        part=part.strip()
        if 2<=len(part)<=14 and part not in STOPWORDS and not any(sw==part for sw in STOPWORDS):
            keys.append(part)
    out=[]
    seen=set()
    for k in keys:
        k=k.strip(' ·:：,，。.;；')
        if len(k)<2 or k in STOPWORDS: continue
        kl=k.lower()
        if kl in seen: continue
        seen.add(kl); out.append(k)
    return out[:18]

records=[]; ideas=[]; news=[]
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
        blocks=re.findall(r'<article\b[^>]*class=["\'][^"\']*brief-item[^"\']*["\'][^>]*>(.*?)</article>',raw,re.S|re.I)
        for idx,block in enumerate(blocks,1):
            source=first(r'<h3[^>]*>(.*?)</h3>',block)
            source=re.sub(r'^\s*\d+[.、]\s*','',source).strip()
            meta=first(r'<div\b[^>]*class=["\'][^"\']*brief-meta[^"\']*["\'][^>]*>(.*?)</div>',block)
            phtmls=re.findall(r'<p\b[^>]*>(.*?)</p>',block,re.S|re.I)
            facts=[]
            source_name=''; source_url=''
            for phtml in phtmls:
                txt=strip_tags(phtml)
                if txt.startswith('法治研判') or txt.startswith('智库选题') or txt.startswith('论文选题') or txt.startswith('原始来源') or txt.startswith('来源'):
                    pass
                else:
                    facts.append(txt)
                if '原始来源' in txt or txt.startswith('来源'):
                    am=re.search(r'<a\b[^>]*href=["\']([^"\']+)["\'][^>]*>(.*?)</a>',phtml,re.S|re.I)
                    if am:
                        source_url=html.unescape(am.group(1)); source_name=strip_tags(am.group(2))
                kind=''
                if txt.startswith('智库选题参考') or '智库选题参考' in txt[:20]: kind='智库选题'
                elif txt.startswith('论文选题') or '论文选题' in txt[:16]: kind='论文选题'
                if kind:
                    title_m=re.search(r'《([^》]+)》',txt)
                    idea_title=title_m.group(1) if title_m else re.sub(r'^(智库选题参考|论文选题)[:：]?','',txt).split('。',1)[0][:80]
                    ideas.append({'id':f'{path}:{len(ideas)}','kind':kind,'title':idea_title,'description':txt,'source':source,'date':date,'path':str(path).replace('\\','/'),'tags':tags_for(source+' '+txt)})
            fact=' '.join(facts[:2]).strip()
            full=strip_tags(block)
            nd=item_date(meta,date)
            npath=str(path).replace('\\','/')
            news.append({
                'id':f'{npath}#research-item-{idx}',
                'path':npath,
                'anchor':f'research-item-{idx}',
                'title':source,
                'date':nd,
                'meta':meta,
                'sourceName':source_name,
                'sourceUrl':source_url,
                'summary':excerpt(fact,220),
                'tags':tags_for(source+' '+meta+' '+full),
                'topics':news_topics_for(source+' '+meta+' '+full),
                'keywords':keywords_for(source,meta,full)
            })

records.sort(key=lambda x:(x['date'],x['path']),reverse=True)
ideas.sort(key=lambda x:(x['date'],x['id']),reverse=True)
news.sort(key=lambda x:(x['date'],x['id']),reverse=True)
(OUT/'research-index.json').write_text(json.dumps(records,ensure_ascii=False,separators=(',',':')),encoding='utf-8')
(OUT/'idea-index.json').write_text(json.dumps(ideas,ensure_ascii=False,separators=(',',':')),encoding='utf-8')
(OUT/'news-index.json').write_text(json.dumps(news,ensure_ascii=False,separators=(',',':')),encoding='utf-8')
print(f'indexed {len(records)} pages, {len(news)} news items and {len(ideas)} research ideas')
