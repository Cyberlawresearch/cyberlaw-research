from pathlib import Path
import json,re,html

ROOT=Path('.')
OUT=ROOT/'assets'; OUT.mkdir(exist_ok=True)

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

TOPIC_RULES={
'智能体AI':['智能体','agentic','ai agent','自主代理','代理权限'],
'生成式AI与大模型':['生成式AI','生成式人工智能','generative ai','大模型','基础模型','foundation model'],
'AI安全与前沿能力':['AI安全','模型安全','前沿模型','前沿能力','失控','对齐','红队','事故披露'],
'AI风险分级与持续监管':['风险分级','风险规制','动态监管','持续评估','监管沙盒','risk-based'],
'AI行政应用':['政府大模型','政务助手','公共部门AI','行政自动化','自动化行政','AI政务'],
'算法歧视与公平':['算法歧视','algorithmic discrimination','招聘算法','就业算法','算法公平','公平性'],
'自动化决策与正当程序':['自动化决策','automated decision','ADM','due process','正当程序','程序错误'],
'机器遗忘与删除权':['机器遗忘','machine unlearning','删除权','被遗忘权','right to disappear'],
'AI职业伦理与专业责任':['职业伦理','法律职业','律师','专业注意义务','认识论责任','epistemic','legal practice'],
'AI与民主法治':['民主','公共理由','rule of algorithm','民主认识论','公共讨论'],
'数据要素与公共数据':['数据要素','公共数据','数据产品','数据交易','数据市场','授权运营'],
'数据跨境':['数据跨境','跨境数据','cross-border data','数据出境'],
'个人信息与隐私保护':['个人信息','隐私','GDPR','data protection','PIPL'],
'生物识别':['生物识别','人脸识别','面部识别','biometric','facial recognition'],
'儿童与未成年人数据':['儿童','未成年人','children','minor','kids'],
'平台责任与内容治理':['平台责任','内容治理','推荐算法','平台治理','social media','在线平台'],
'反垄断与市场力量':['反垄断','antitrust','垄断','市场支配','competition authority'],
'平台竞争与自我优待':['平台竞争','二选一','自我优待','self-preferencing','应用商店','app store'],
'AI训练与版权':['AI训练','训练数据','fair use','合理使用','训练版权','生成式AI版权'],
'知识产权与技术竞争':['知识产权','版权','著作权','copyright','patent'],
'网络安全事件与漏洞':['网络安全','cybersecurity','漏洞','入侵','勒索','ransomware'],
'关键基础设施安全':['关键基础设施','critical infrastructure','基础设施安全','反破坏'],
'后量子密码':['后量子','post-quantum','PQC','量子密码'],
'芯片与出口管制':['芯片','半导体','出口管制','export control','GPU','先进计算'],
'算力与数据中心':['算力','数据中心','compute','词元','算力网'],
'深度伪造与合成内容':['深度伪造','deepfake','合成内容','数字水印'],
'选举与AI':['选举','election','投票','选民','campaign'],
'自主武器':['自主武器','autonomous weapon','LAWS','致命自主武器'],
'国家安全与军事AI':['国家安全','national security','军事','国防','军方'],
'国际AI治理':['AI治理','人工智能治理','AI Act','AI Office','全球AI治理','国际规则'],
'AI产品责任':['产品责任','product liability','缺陷产品','损害赔偿'],
'司法AI':['司法人工智能','智能法院','辅助裁判','judicial ai','adjudication'],
'预测性执法':['预测性执法','predictive policing','预测性司法','再犯风险'],
'AI审计':['AI审计','算法审计','algorithm audit','fairness audit'],
'数据访问与Data Act':['Data Act','数据访问权','联网产品','身份认证','授权访问'],
}

STOP={'中国','美国','欧盟','英国','韩国','日本','新加坡','澳大利亚','巴西','印度','德国','法国','发布','公布','表示','提出','推进','推动','加强','监管','管理','政策','规则','办法','意见','计划','人工智能','科技','数字','网络','数据','平台','研究','关于','相关','进一步','正式','最新','今日','昨日'}

def strip_tags(s):
    s=re.sub(r'<script\b[^>]*>.*?</script>',' ',s,flags=re.S|re.I)
    s=re.sub(r'<style\b[^>]*>.*?</style>',' ',s,flags=re.S|re.I)
    s=re.sub(r'<[^>]+>',' ',s)
    return re.sub(r'\s+',' ',html.unescape(s)).strip()

def first(pattern,s,default=''):
    m=re.search(pattern,s,re.S|re.I); return strip_tags(m.group(1)) if m else default

def classify(raw,path):
    t=strip_tags(raw); n=path.name
    if 'tech-law-brief' in n:return '全球科技法简报'
    if 'new-works' in n or path.parent.name=='new-works':return '科技法研究新作'
    if '每日法学经典著作' in t or 'LEGAL CLASSIC' in t:return '法学经典著作'
    if '域外法学论文精读' in t or 'CLASSIC PAPERS' in t or path.parent.name=='papers':return '域外法学论文精读'
    return '研究资料'

def tags_for(text):
    low=text.lower(); return [k for k,v in TAG_RULES.items() if any(w.lower() in low for w in v)][:6]

def topics_for(text):
    low=text.lower(); return [k for k,v in TOPIC_RULES.items() if any(w.lower() in low for w in v)]

def date_for(path,raw):
    m=re.search(r'(20\d{2})[-./年](\d{1,2})[-./月](\d{1,2})',str(path)+' '+strip_tags(raw))
    return f'{int(m.group(1)):04d}-{int(m.group(2)):02d}-{int(m.group(3)):02d}' if m else ''

def item_date(meta,page_date):
    m=re.search(r'(?:(20\d{2})年)?(\d{1,2})月(\d{1,2})日',meta)
    if not m:return page_date
    y=m.group(1) or page_date[:4]; return f'{int(y):04d}-{int(m.group(2)):02d}-{int(m.group(3)):02d}' if y else page_date

def excerpt(text,n=260): return text if len(text)<=n else text[:n].rstrip()+'…'

def keywords_for(title,meta,text):
    src=' '.join([title,meta,text[:900]]); keys=[]
    keys += re.findall(r'\b[A-Z][A-Z0-9.-]{1,12}\b|\b[A-Za-z][A-Za-z0-9.-]{2,24}\b',src)
    keys += re.findall(r'[“《]([^”》]{2,18})[”》]',src)
    keys += re.findall(r'[\u4e00-\u9fffA-Za-z0-9·]{2,18}(?:委员会|管理局|法院|检察院|部|局|署|公司|平台|模型|法案|条例|指令|数据库|中心)',src)
    for p in re.split(r'[：:，,；;、“”《》()（）\-—]',re.sub(r'^\s*\d+[.、]\s*','',title)):
        p=p.strip()
        if 2<=len(p)<=14 and p not in STOP:keys.append(p)
    out=[]; seen=set()
    for k in keys:
        k=k.strip(' ·:：,，。.;；'); kl=k.lower()
        if len(k)<2 or k in STOP or kl in seen or kl in {'the','and','for','with','from','this','that','law','legal'}:continue
        seen.add(kl); out.append(k)
    return out[:18]

def h3_blocks(raw):
    hs=list(re.finditer(r'<h3[^>]*>(.*?)</h3>',raw,re.S|re.I)); out=[]
    for i,m in enumerate(hs):
        end=hs[i+1].start() if i+1<len(hs) else len(raw)
        out.append((strip_tags(m.group(1)),raw[m.end():end]))
    return out

records=[]; ideas=[]; news=[]; newworks=[]; paths=[]
for folder in ['articles','papers','new-works']:
    p=ROOT/folder
    if p.exists():paths += sorted(p.glob('*.html'))

for path in paths:
    raw=path.read_text(encoding='utf-8',errors='ignore'); npath=str(path).replace('\\','/')
    title=first(r'<h1[^>]*>(.*?)</h1>',raw) or first(r'<title[^>]*>(.*?)</title>',raw)
    body=first(r'<main[^>]*>(.*?)</main>',raw) or strip_tags(raw); body=re.sub(r'网信法研究每日推送\s*','',body)
    category=classify(raw,path); date=date_for(path,raw); tags=tags_for(title+' '+body)
    records.append({'id':npath,'path':npath,'title':title,'pageTitle':first(r'<title[^>]*>(.*?)</title>',raw),'date':date,'category':category,'tags':tags,'topics':topics_for(title+' '+body),'excerpt':excerpt(body),'text':body[:14000]})

    if category=='全球科技法简报':
        blocks=re.findall(r'<article\b[^>]*class=["\'][^"\']*brief-item[^"\']*["\'][^>]*>(.*?)</article>',raw,re.S|re.I)
        for idx,block in enumerate(blocks,1):
            it=re.sub(r'^\s*\d+[.、]\s*','',first(r'<h3[^>]*>(.*?)</h3>',block)).strip(); meta=first(r'<div\b[^>]*class=["\'][^"\']*brief-meta[^"\']*["\'][^>]*>(.*?)</div>',block)
            facts=[]; src_name=''; src_url=''
            for phtml in re.findall(r'<p\b[^>]*>(.*?)</p>',block,re.S|re.I):
                txt=strip_tags(phtml)
                if not (txt.startswith('法治研判') or txt.startswith('智库选题') or txt.startswith('论文选题') or txt.startswith('原始来源') or txt.startswith('来源')):facts.append(txt)
                if '原始来源' in txt or txt.startswith('来源'):
                    am=re.search(r'<a\b[^>]*href=["\']([^"\']+)["\'][^>]*>(.*?)</a>',phtml,re.S|re.I)
                    if am:src_url=html.unescape(am.group(1)); src_name=strip_tags(am.group(2))
                kind='智库选题' if '智库选题参考' in txt[:20] else ('论文选题' if '论文选题' in txt[:16] else '')
                if kind:
                    tm=re.search(r'《([^》]+)》',txt); idea_title=tm.group(1) if tm else re.sub(r'^(智库选题参考|论文选题)[:：]?','',txt).split('。',1)[0][:80]
                    ideas.append({'id':f'{npath}:{len(ideas)}','kind':kind,'title':idea_title,'description':txt,'source':it,'date':date,'path':npath,'tags':tags_for(it+' '+txt)})
            full=strip_tags(block); nd=item_date(meta,date)
            news.append({'id':f'{npath}#research-item-{idx}','path':npath,'anchor':f'research-item-{idx}','title':it,'date':nd,'meta':meta,'sourceName':src_name,'sourceUrl':src_url,'summary':excerpt(' '.join(facts[:2]),220),'tags':tags_for(it+' '+meta+' '+full),'topics':topics_for(it+' '+meta+' '+full),'keywords':keywords_for(it,meta,full)})

    if category=='科技法研究新作':
        modern=re.findall(r'<article\b[^>]*class=["\'][^"\']*brief-item[^"\']*["\'][^>]*>(.*?)</article>',raw,re.S|re.I)
        candidates=[]
        if modern:
            for b in modern:candidates.append((first(r'<h3[^>]*>(.*?)</h3>',b),b))
        else:
            for h,b in h3_blocks(raw):
                if re.match(r'^\s*\d+[.、]',h):candidates.append((h,b))
        for idx,(h,b) in enumerate(candidates,1):
            it=re.sub(r'^\s*\d+[.、]\s*','',strip_tags(h)).strip(); full=strip_tags(b); meta=first(r'<div\b[^>]*class=["\'][^"\']*brief-meta[^"\']*["\'][^>]*>(.*?)</div>',b)
            if not meta:
                meta=' · '.join(re.findall(r'(?:作者|出处|时间)[:：]\s*([^\n]+?)(?=(?:作者|出处|时间|DOI)[:：]|研究方向[:：]|$)',full)[:3])
            newworks.append({'id':f'{npath}#research-item-{idx}','path':npath,'anchor':f'research-item-{idx}','title':it,'date':date,'meta':meta,'summary':excerpt(full,230),'tags':tags_for(it+' '+full),'topics':topics_for(it+' '+full),'keywords':keywords_for(it,meta,full)})

records.sort(key=lambda x:(x['date'],x['path']),reverse=True); ideas.sort(key=lambda x:(x['date'],x['id']),reverse=True); news.sort(key=lambda x:(x['date'],x['id']),reverse=True); newworks.sort(key=lambda x:(x['date'],x['id']),reverse=True)
(OUT/'research-index.json').write_text(json.dumps(records,ensure_ascii=False,separators=(',',':')),encoding='utf-8')
(OUT/'idea-index.json').write_text(json.dumps(ideas,ensure_ascii=False,separators=(',',':')),encoding='utf-8')
(OUT/'news-index.json').write_text(json.dumps(news,ensure_ascii=False,separators=(',',':')),encoding='utf-8')
(OUT/'newworks-index.json').write_text(json.dumps(newworks,ensure_ascii=False,separators=(',',':')),encoding='utf-8')
print(f'indexed {len(records)} pages, {len(news)} news items, {len(newworks)} new works and {len(ideas)} research ideas')