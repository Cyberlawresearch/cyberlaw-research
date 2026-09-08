"""One-time, source-preserving completion of the September 8 edition."""
from pathlib import Path
from bs4 import BeautifulSoup
import json,re,html
R=Path(__file__).resolve().parents[2]
D='2026-09-08'
P=['articles/'+D+'-tech-law-brief.html','articles/'+D+'-richards-dangers-surveillance.html','articles/'+D+'-raz-authority-of-law.html','articles/'+D+'-new-works.html']
LABEL=['全球科技法简报','域外法学论文精读','法学经典著作','科技法研究新作']
E=html.escape

def load(path): return BeautifulSoup((R/path).read_text(),'html.parser')
def write(path,s):
 for script in s.find_all('script',src=True):
  if any(x in script['src'] for x in ['auth.js','favorites.js','context-tools.js','context-refine.js','related-refine.js','citation-refine.js','notes-inline.js','research-tools.js']):script.decompose()
 (R/path).write_text(str(s),encoding='utf-8')
def cite(node,data):node['data-citation']=json.dumps(data,ensure_ascii=False,separators=(',',':'))
def frag(s):return BeautifulSoup(s,'html.parser')

s=load(P[0]);items=s.select('.brief-item')
assert len(items)==18
for x in s.select('.brief-focus'):x.decompose()
for h in list(s.find_all('h2')):
 if h.get_text(strip=True)=='本期最值得先看':
  if h.find_next_sibling():h.find_next_sibling().decompose()
  h.decompose()
mods={
1:('国家数据局公布“数据要素×”全国总决赛规则与项目名单','2026-09-08','中国 · 国家数据局',None,None),
2:('上海就企业研发准备金制度工作指引及公平竞争影响征求意见','2026-09-07','中国上海 · 上海市科学技术委员会',None,None),
3:('上海启动大型科学仪器设施信息报送检查','2026-09-08','中国上海 · 上海市科学技术委员会','上海市科委9月8日公布年度大型科学仪器设施信息报送检查通知，文件落款为9月6日。检查覆盖2025年7月1日至2026年6月30日入账、财政性资金全部或部分支持且原值30万元以上的相关仪器设施，要求10月12日前报送。信息完整性、时效性、准确性以及设施开放共享情况纳入评价；弄虚作假涉及科研失信的，依科研诚信管理制度处理。',None),
4:('北京经开区公布11家OPC社区布局及AI创业支持措施','2026-09-08','中国北京 · 北京经济技术开发区',None,None),
5:('国新办发布数字贸易新数据，并介绍跨境数据流通情况','2026-09-07','中国 · 国务院新闻办公室／商务部','9月7日国新办新闻发布会介绍数字贸易发展及第五届全球数字贸易博览会安排。商务部披露，2025年可数字化交付的服务进出口为4323.1亿美元，同比增长6.3%；2025年数据跨境流通量为142.3EB，其中企业数据跨境流通量为88.06EB。发布会同时介绍人工智能及跨境数据相关交流安排；这些统计和活动介绍本身不构成新的数据出境豁免规则。',None),
6:('全国网络法治主题宣传活动启动，聚焦数据安全与未成年人保护','2026-09-08','中国 · 中央网信办等','9月8日，2026年“E法同行 兴辽治宁”全国网络法治主题宣传活动在沈阳启动。中央网信办、司法部和全国普法办指导，辽宁有关部门联合主办；活动围绕网络合规经营、劳动权益、数据安全及未成年人个人信息保护等展开。此次为网络普法与政策传播活动，不是新的立法或处罚措施。','普法活动的价值在于帮助平台经营者、新就业群体和未成年人理解现有权利与义务。进一步发挥作用，需要把宣传内容与可获得的投诉、咨询和救济渠道衔接，而不能以活动启动替代对执行效果的评价。'),
7:('澳大利亚发布数字注意义务草案，拟赋予用户推荐信息流选择权','2026-09-08','澳大利亚 · 联邦政府／eSafety','澳大利亚政府9月8日公布“My feed, My Way”及数字注意义务草案，开展定向征求意见。方案要求社交媒体向新老用户提供个性化推荐与仅查看关注账号内容的选择，并将未成年人在线安全责任延伸至有关应用、游戏和AI聊天服务。政府提出由eSafety执行、最高1.092亿澳元处罚等安排，计划年内提交议会；草案尚未成为生效法律。',None),
8:('Google宣布调整欧洲搜索设计以回应《数字市场法》要求','2026-09-08','欧盟 · Google／数字市场监管','据Reuters9月8日报道，Google宣布调整欧洲搜索结果，包括增加专业垂直服务的展示位置，并调整酒店、航空及餐饮等搜索界面。公司表示，这些安排是为回应《数字市场法》下有关自我优待的监管要求，同时主张部分改动可能损害用户体验和本地商户流量。此次新进展是平台公布产品调整，并非欧盟当天另作出处罚决定或确认整改已经合规。',None),
9:('英国CMA说明数字市场竞争制度实施重点','2026-09-07','英国 · Competition and Markets Authority',None,None),
11:('欧盟伦理专家组提出Neuro-AI基础设施治理建议','2026-09-08','欧盟 · European Group on Ethics in Science and New Technologies','欧盟科学与新技术伦理专家组9月8日发布《Governing Neuro-AI: Towards an Infrastructure Approach》声明。专家组建议将神经数据收集、推断、再利用及模型开发所依赖的基础设施一并纳入治理，并关注基本权利、公共利益能力和现有规则的适配性。该声明属于独立专家伦理建议，不是已经生效的欧盟法规，也不直接创设对企业的处罚义务。',None),
12:('华为美国刑事案定于9月8日启动陪审员遴选','2026-09-08','美国 · 纽约东区联邦地区法院','Reuters与AP9月8日报道，华为纽约刑事案定于当日开始陪审员遴选，案件涉及伊朗业务、银行陈述、商业秘密等指控。审判由Ann Donnelly法官主持，预计持续约三个月，华为否认相关不当行为。报道使用的是“预定／预计启动”的程序表述，不能据此认定陪审团已选定或法院已就指控作出有罪判断。',None),
13:('N-able发布N-central远程代码执行漏洞热修复，利用状态披露存在差异','2026-09-06','全球 · N-able／远程运维安全','N-able9月6日公布N-central 2026.3 Hotfix 4，修复CVE-2026-86218所涉预认证远程代码执行问题，修复版本为2026.3.1.14。厂商发行说明仍称未确认生产环境遭到利用，但9月7日专业媒体援引其事件通知称已观察到在野利用，两份披露的口径并不一致。已确认的处置要求是升级受影响版本；不能把本项漏洞与此前另一组身份验证绕过漏洞混为一谈。','漏洞通知的可信度不仅取决于是否及时发布，也取决于不同渠道对漏洞编号、受影响版本和利用状态的表述是否一致。远程运维平台具有跨客户高权限，托管服务商需要在厂商信息仍不完整时记录判断、及时修复，并检查客户通知和补丁责任的分工。'),
14:('Boston Scientific因网络攻击调整业绩预期，披露经营连续性影响','2026-09-08','美国 · Boston Scientific／证券信息披露','Boston Scientific9月8日通过监管文件说明，8月25日发现的网络安全事件影响制造、订单处理和全球发货，公司预计难以达到此前公布的第三季度及全年销售与调整后利润指引。公司称主要配送和灭菌设施已经恢复，大部分生产设施重新运行，但完整财务影响仍在评估。新进展是对经营及业绩预期的更新披露，并非9月8日才发生网络攻击。',None),
15:('斯洛文尼亚允许Tesla受监督驾驶辅助系统使用，欧盟统一审批仍待推进','2026-09-07','斯洛文尼亚／欧盟 · 道路交通准入','Reuters9月8日报道，Tesla于9月7日宣布FSD Supervised获得斯洛文尼亚使用许可，该国基础设施部长转发了有关消息。系统仍要求驾驶员持续监督，不属于取消驾驶员责任的完全自动驾驶。Tesla所述欧盟范围投票最早可能在10月6日进行，属于后续程序预期，并不意味着欧盟已作出统一批准。','跨区域采用驾驶辅助系统，需要分别识别成员国许可、车辆型式批准及后续欧盟程序的法律效力。制造商的产品名称和审批预期不能替代许可文件；驾驶员监督要求、系统使用条件及制造商安全义务仍须分别判断。')}
for n,(title,date,meta,facts,analysis) in mods.items():
 it=items[n-1];it.h3.string=f'{n}. {title}';it.select_one('.brief-meta').string=f'{date} · {meta}';it['data-event-date']=date
 if facts:it.select_one('.brief-fact').string=facts
 if analysis:
  for p in it.find_all('p'):
   if p.get_text().startswith('法治研判'):
    p.clear();p.append(frag('<strong>法治研判：</strong>'+analysis));break

def sources(it,ss):
 p=it.select_one('.source');p.clear();p.append('原始来源：')
 for j,(label,title,url) in enumerate(ss):
  if j:p.append('；')
  a=s.new_tag('a',href=url);a.string=label;a['data-original-title']=title;p.append(a)
 title=ss[0][1];it['data-original-title']=title
 cite(it,dict(type='news',cnTitle=re.sub(r'^\d+\.\s*','',it.h3.get_text()),originalTitle=title,sourceName=ss[0][0],date=it['data-event-date'],url=ss[0][2],foreign=int(it['id'].split('-')[-1])>6))
source_updates={
1:[('国家数据局','关于2026年“数据要素×”大赛全国总决赛有关事项的通知','https://www.nda.gov.cn/sjj/zwgk/tzgg/0908/20260908100236590767189_mobile.html'),('国家数据局','2026年“数据要素×”大赛全国总决赛项目名单公示','https://www.nda.gov.cn/sjj/zwgk/tzgg/0908/20260908100505532102751_pc.html')],
2:[('上海市科学技术委员会','关于《上海市企业研发准备金制度登记工作指引（试行）（征求意见稿）》公开征求意见的公告','https://stcsm.sh.gov.cn/zwgk/yjzjzx/yjzjzx/20260907/fd66d41e9c3e4a928ca062479ffebe1e.html')],
3:[('上海市科学技术委员会','关于开展2026年度大型科学仪器设施信息报送检查的通知','https://stcsm.sh.gov.cn/zwgk/tzgs/zhtz/20260908/f3a2eaa410a44ee3bbab030271255ba2.html')],
4:[('首都之窗／北京经开区','11家OPC社区串联成网 2027年力争培育超万名AI开发者 北京经开区OPC社区地图正式发布','https://www.beijing.gov.cn/ywdt/gzdt/202609/t20260908_4855171.html')],
5:[('商务部转载中国新闻网','2025年中国可数字化交付的服务进出口达4323.1亿美元','https://fec.mofcom.gov.cn/article/xwdt/xwdtqtzx/xwfwydyl/202609/7904.html')],
6:[('中央网信办','2026年“E法同行 兴辽治宁”全国网络法治主题宣传活动在辽宁沈阳启动','https://www.cac.gov.cn/2026-09/08/c_1790616581404241.htm')],
7:[('Australian Government','My feed, My Way','https://www.pm.gov.au/media/my-feed-my-way'),('Reuters','Australia targets social media algorithms with new user choice rules','https://www.reuters.com/business/media-telecom/australia-targets-social-media-algorithms-with-new-user-choice-rules-2026-09-08/')],
8:[('Reuters','Google warns of lower quality as it revamps Europe search results to avoid EU fines','https://www.reuters.com/world/google-warns-lower-quality-it-revamps-europe-search-results-avoid-eu-fines-2026-09-08/'),('Global Banking & Finance Review／Reuters','Exclusive-Google warns of lower quality as it revamps Europe search results to avoid EU fines','https://www.globalbankingandfinance.com/exclusive-google-warns-lower-quality-revamps-europe-search/')],
9:[('Competition and Markets Authority','On track: delivering the promises of the digital markets regime','https://www.gov.uk/government/speeches/on-track-delivering-the-promises-of-the-digital-markets-regime')],
11:[('European Commission','Experts call for a new approach to Neuro-AI governance','https://research-and-innovation.ec.europa.eu/news/all-research-and-innovation-news/experts-call-new-approach-neuro-ai-governance-2026-09-08_en?prefLang=pl'),('European Group on Ethics','Experts call for a new approach to Neuro-AI governance','https://ethicsadvice.eu/events/experts-call-for-a-new-approach-to-neuro-ai-governance/')],
12:[('Reuters','Huawei heads to trial in US over its business dealings with Iran','https://www.reuters.com/legal/litigation/huawei-heads-trial-us-over-its-business-dealings-iran-2026-09-08/'),('Associated Press','China’s Huawei Technologies faces racketeering trial in New York','https://apnews.com/article/ed66f29aa8539941aa8fad311d511cc2')],
13:[('N-able','N-central 2026.3 Hotfix 4 (CVE-2026-86218)','https://status.n-able.com/2026/09/06/n-central-2026-3-hotfix-4-cve-2026-86218/'),('BleepingComputer','N-able patches max severity N-central flaw amid ongoing attacks','https://www.bleepingcomputer.com/news/security/n-able-patches-max-severity-n-central-flaw-amid-ongoing-attacks/')],
14:[('Reuters','Boston Scientific says unlikely to meet 2026 sales, profit forecast after cyberattack','https://www.reuters.com/technology/boston-scientific-says-cyberattack-likely-hurt-2026-sales-profit-2026-09-08/'),('Insurance Journal／Reuters','Boston Scientific Says Unlikely to Meet 2026 Forecast After Cyberattack Disruption','https://www.insurancejournal.com/news/east/2026/09/08/884346.htm')],
15:[('Reuters','Slovenia clears Tesla’s FSD driver assistance ahead of EU vote','https://www.reuters.com/business/slovenia-clears-teslas-fsd-driver-assistance-ahead-eu-vote-2026-09-08/'),('AOL／Reuters','Slovenia clears Tesla’s FSD driver assistance ahead of EU vote','https://www.aol.com/articles/slovenia-clears-teslas-fsd-driver-071753000.html')]}
for n,ss in source_updates.items():sources(items[n-1],ss)
new={
10:{'title':'韩国通过2027—2029年消费者政策规划，推进数字权利与集体救济','date':'2026-09-08','meta':'韩国 · 消费者政策委员会／国务调整室','facts':'韩国消费者政策委员会9月8日审议通过第七次消费者政策基本计划，规划期为2027—2029年。方案将AI市场监测、消费者数据传输及停止传输权、无障碍数字服务与损害救济结合，并提出扩大集体诉讼及引入法院责令经营者提交资料的制度。后两项属于规划中的制度建设方向，不能写成集体诉讼新法已经通过。','law':'数字消费损害往往具有单人损失小、经营者掌握关键证据、受影响群体广泛等特征。将数据权利、公共监测与集体救济放在同一计划中，有助于连接事前预防与事后补救，但具体诉权、举证及法院权限仍须后续立法明确。','think':'人工智能消费风险的跨部门监测与群体救济机制','thinktext':'可研究平台订阅、自动化交易及模型服务引发的大规模小额损害，如何由消费者保护、数据监管和司法程序协同处理。重点评估监管信息进入民事诉讼、公共监测支持代表人诉讼的制度条件。','paper':'数字消费纠纷中的信息不对称与证据提出义务','papertext':'经营者掌握算法日志和交易记录时，消费者的证明困难是否足以支持特别的资料提出命令，是值得展开的程序法问题。研究可比较披露范围、商业秘密保护和不配合的不利后果，避免把救济困难简单化为举证责任倒置。','sources':[('국무조정실','제17차 소비자정책위원회','https://www.opm.go.kr/opm/news/press-release.do'),('연합뉴스','소비자 집단소송제도 확대도입 추진…사용자 친화 키오스크 개발','https://www.yna.co.kr/view/AKR20260908148700002')]},
16:{'title':'英国就AI赋能清洁能源系统征集证据，关注标准、监管和系统韧性','date':'2026-09-08','meta':'英国 · Department for Energy Security and Net Zero','facts':'英国能源安全与净零部9月8日启动“Vision for an AI-enabled clean energy system”证据征集，截止11月6日，适用于英格兰、苏格兰和威尔士。文件就AI用于能源预测、规划、协调和运行的机会与障碍征询产业、监管机构、研究者和消费者组织意见。政府特别询问何处需要协调、标准和监管明确性；本次是政策形成前的证据征集，并非已制定能源AI准入新规。','law':'AI进入能源运行后，风险不再止于预测误差，而可能影响供能连续性、基础设施安全和消费者待遇。先围绕真实部署收集证据，能够为系统接入、人工接管、供应商义务和行业监管分工提供事实基础。','think':'能源系统人工智能化的国家级安全与监管协同框架','thinktext':'可从电网调度、需求响应及分布式储能三个层面识别对AI的共同依赖，评估单点模型故障的系统性传播。研究应统筹能源监管、网络安全、数据基础设施和应急保障，形成部署条件与退出预案。','paper':'关键基础设施中预测模型与控制系统的责任区分','papertext':'同一算法仅提供预测建议与直接控制能源设备时，其运营者的注意义务和损害归责应当不同。研究可围绕人工决策保留、供应商可控性及持续更新义务建立分层标准。','sources':[('Department for Energy Security and Net Zero','Vision for an AI-enabled clean energy system (HTML)','https://www.gov.uk/government/calls-for-evidence/vision-for-an-ai-enabled-clean-energy-system/vision-for-an-ai-enabled-clean-energy-system-html')]},
17:{'title':'韩国披露删除请求外泄后的补救，Google暂停相关信息展示并承诺整改','date':'2026-09-08','meta':'韩国 · 性别平等家庭部／Google','facts':'News1于9月8日援引韩国性别平等家庭部说明，数字性犯罪受害者向Google提出删除请求时提交的个人资料曾被转交并公开在第三方研究网站。新的补救进展是9月7日起相关韩国请求内容停止展示，政府继续开展协调，并收到Google有关防止再发生的承诺；支援机构暂停经该渠道提交删除请求，等待安全措施核查。现阶段仍在核查范围和违法责任，不能把Google道歉或整改承诺当成监管处罚结果。','law':'行使删除权所需提交的身份证明和侵害说明，本身可能成为高度敏感的新数据。平台为研究或透明度目的分享投诉记录时，应把救济渠道保密、必要性控制和第三方责任纳入独立审查，避免救济过程制造二次伤害。','think':'跨境平台内容救济渠道中的受害者信息保护','thinktext':'可评估国内机构协助当事人向境外平台申诉时，身份资料和证据如何被继续共享，并建立跨机构紧急阻断和安全恢复机制。国家层面可推动平台投诉接口的保密标准及第三方透明度数据库的脱敏要求。','paper':'权利救济材料二次利用的目的限制与保密义务','papertext':'投诉材料为证明侵害而提交，不代表投诉人同意将其用于公开研究或透明度展示。研究可区分平台处理原侵权内容的义务与保护申诉人资料的独立义务，并讨论多主体转交时的责任分配。','sources':[('News1／파이낸셜뉴스','구글에 불법촬영물 지워달랬는데…이름·학교·피해 내용까지 퍼졌다','https://www.fnnews.com/news/202609081001178590')]},
18:{'title':'Google威胁情报报告记录攻击转向智能体自动化及AI资产勒索','date':'2026-09-08','meta':'全球 · Google Threat Intelligence Group','facts':'Google威胁情报团队9月8日发布《From Prompting to Autonomy – The Evolution of Adversarial AI》，总结2026年第二季度观察。报告记录攻击者在侵入云资源后，以智能体执行批量凭据窃取，并针对AI开发依赖和安全扫描器实施操纵。报告还披露专有模型、源代码和研究数据成为窃取勒索目标；这些是今日发布的研究发现，不应将报告内较早的攻击日期改写为今日。','law':'模型权重、代理指令、访问凭据与云算力已构成相互连接的安全资产。组织对AI工具的管理不能只检查输出内容，还需落实最小权限、依赖审查、异常调用记录及供应商与部署者之间的事件处置分工。','think':'智能体攻击自动化对国家网络防御响应体系的影响','thinktext':'可评估攻击时间被压缩后，关键行业人工审批和分散通报机制是否仍能有效应对。重点研究模型供应链、云资源和身份系统的联合监测，以及可自动隔离但保留审计的处置机制。','paper':'智能体自动化攻击背景下网络安全注意义务的动态调整','papertext':'当攻击速度和可复制性显著改变，原来被视为合理的补救时限是否仍然充分，需要结合可获得的防护能力判断。研究可从风险可预见性、工具控制和措施成本出发，讨论持续注意义务的具体化。','sources':[('Google Threat Intelligence Group','GTIG AI Threat Tracker: From Prompting to Autonomy – The Evolution of Adversarial AI','https://cloud.google.com/blog/topics/threat-intelligence/from-prompting-to-autonomy-the-evolution-of-adversarial-ai'),('Infosecurity Magazine','AI Coding Tools Now a Prime Target for Threat Actors, Google Warns','https://www.infosecurity-magazine.com/news/ai-coding-tools-threat-actors/')]}}
for n,x in new.items():
 it=items[n-1];it.clear();it['data-event-date']=x['date']
 it.append(frag(f'<h3>{n}. {E(x["title"])}</h3><div class="brief-meta">{x["date"]} · {E(x["meta"])}</div><p class="brief-fact">{E(x["facts"])}</p><p><strong>法治研判：</strong>{E(x["law"])}</p><p><strong>智库选题参考：《{E(x["think"])}》</strong>。{E(x["thinktext"])}</p><p><strong>论文选题：《{E(x["paper"])}》</strong>。{E(x["papertext"])}</p><p class="source"></p>'))
 sources(it,x['sources'])
body=s.select_one('.article-body .article-wrap')
for h in list(body.find_all('h3',recursive=False)):h.decompose()
for h in list(body.find_all('h2',recursive=False)):
 if '跟踪' in h.get_text():
  for sib in list(h.find_next_siblings()):sib.decompose()
  h.decompose();break
for x in list(body.select('.follow-up')):x.decompose()
body.append(frag('<h2>继续跟踪</h2><div class="follow-up"><p><strong>澳大利亚平台义务：</strong>跟进定向征求意见结果、信息流默认设置和eSafety执行权限的最终条文。</p><p><strong>韩国数字消费救济：</strong>关注集体诉讼和资料提出命令何时进入正式立法，以及删除请求渠道的安全恢复。</p><p><strong>欧洲数字市场：</strong>跟进Google搜索整改的监管反馈，区分企业自评与监管结论。</p><p><strong>能源AI：</strong>跟进英国11月6日证据征集结果，以及标准、接入条件和系统韧性的后续安排。</p><p><strong>医疗供应连续性：</strong>关注Boston Scientific对生产恢复和财务影响的进一步披露。</p></div>'))
write(P[0],s)
s=load(P[3]);it=s.select('.brief-item')[0];it.clear();it['data-original-title']='Ground-truth is law: The invisible conceptual work behind AI'
it.append(frag('<h3>1. “标准答案”即法律：司法人工智能背后的隐形概念劳动</h3><div class="brief-meta">Camille Girard-Chanudet · “Ground-truth is law: The invisible conceptual work behind AI” · <em>Big Data &amp; Society</em>, Vol.12 No.2 · 2025年6月19日在线发表 · DOI:10.1177/20539517251352823</div><p class="work-reading">文章通过法国司法领域两项人工智能项目的田野研究，追踪目标确定、数据集建立、分类体系设计、标注和运行监测中的概念选择。研究发现，法律判断并未随着机器学习而消失，而是转移到训练资料及所谓“标准答案”的形成过程。其价值在于揭示技术中立表述背后的规范劳动，为分析司法数据标注者的判断权限、训练标签的合法性以及算法问责提供具体研究对象。</p><p class="source">原始来源：<a href="https://journals.sagepub.com/doi/10.1177/20539517251352823" data-original-title="Ground-truth is law: The invisible conceptual work behind AI">Big Data &amp; Society：开放全文</a></p>'))
metas=[dict(type='article',author='Camille Girard-Chanudet',originalTitle='Ground-truth is law: The invisible conceptual work behind AI',journal='Big Data & Society',year='2025',volume='12',issue='2',doi='10.1177/20539517251352823'),dict(type='article',author='Noam Kolt',originalTitle='Governing AI Agents',journal='Notre Dame Law Review',year='2026',volume='101',pages='335',note='335为起始页，不表示全文只有一页'),dict(type='article',author='Gregory M. Dickinson',originalTitle='Law Proofing the Future',journal='Harvard Journal on Legislation',year='2026',volume='63',issue='1'),dict(type='article',author='Carol A. Needham',originalTitle='Regulation of the Use of Generative Artificial Intelligence Tools in the Delivery of Legal Services: Verification and Accountability',journal='Washington University Journal of Law and Policy',year='2025',volume='77',issue='1',pages='184–211'),dict(type='article',author='Chien-Chih Lu',originalTitle='From safe harbours to over-enforcement: the rise of AI and copyright monitoring',journal='Journal of Intellectual Property Law & Practice',year='2025',volume='20',issue='9',pages='617–632',doi='10.1093/jiplp/jpaf053')]
for it,m in zip(s.select('.brief-item'),metas):
 m.update(url=it.select_one('.source a')['href'],cnTitle=re.sub(r'^\d+\.\s*','',it.h3.get_text()));cite(it,m)
for p in s.select('.follow-up'):p.decompose()
write(P[3],s)
s=load(P[1]);cite(s.body,dict(type='article',author='Neil M. Richards',originalTitle='The Dangers of Surveillance',journal='Harvard Law Review',year='2013',volume='126',issue='7',pages='1934–1965',url='https://harvardlawreview.org/print/vol-126/the-dangers-of-surveillance/',cnTitle='监控的危险'))
h=s.find(id='section-7');ps=[]
for x in h.find_next_siblings():
 if x.name=='h2':break
 if x.name=='p':ps.append(x)
ps[1].clear();ps[1].append(frag('<strong>第二，作者主张禁止连存在本身都被保密的国内监控计划。</strong>这里区分的是单个侦查措施的必要保密与整个监控制度的秘密存在。理查兹提出的是规范主张，不是说美国现行法已经全面采纳这一禁令。'))
ps[2].clear();ps[2].append(frag('<strong>第三，作者反对未经适当授权的全面互联网监控。</strong>他要求有意义的司法程序，并对威胁思想隐私的观察进行严格审查。重点不只是数据量大，而是总体性监控是否失去具体授权、监督和可争议的边界。'))
write(P[1],s)
(R/'data'/'current-edition.json').write_text(json.dumps({'date':D,'pages':dict(zip(['brief','paper','classic','newworks'],P)),'news_count':18,'newworks_count':5},ensure_ascii=False,indent=2)+'\n')
print('Corrected news and paper; replaced duplicate new work.')
