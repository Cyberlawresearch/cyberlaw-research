from pathlib import Path
exec((Path(__file__).parent/'complete_sept8.py').read_text().split('s=load(P[0])')[0])
s=load(P[2]);cite(s.body,dict(type='book',author='Joseph Raz',originalTitle='The Authority of Law: Essays on Law and Morality',publisher='Oxford University Press',place='Oxford',year='1979',url='https://academic.oup.com/book/10820',cnTitle='法律的权威'))
extra='''<h2 id="book-systems">法律体系的同一性：为什么一条规则属于这个法律秩序</h2><p><strong>法律体系不是把所有有效规则放在一起的清单。</strong>在第五章中，拉兹把同一性问题拆成几个不同层次：一项规则怎样成为单独的法律；哪些法律在同一时点属于同一体系；法律不断改变时，体系为什么仍被认为具有连续性。把这些问题混在一起，很容易把“由同一个国家执行”直接当作完整答案，掩盖规则归属和制度连续性的差别。</p><p>这一分析使法理论能够区分修改法律与更换法律体系，也能区分制定新法与适用既有法律。某项法律被废止，并不意味着其所在法律体系终结；反过来，实际掌权者发生变化时，旧规则继续被使用，也不能仅据文本相同就断定规范基础完全没有变化。这里的重点不是提供适用于所有革命和制度变迁的简易判据，而是先明确“连续的是规则、机构，还是法律秩序”的问题。</p><p>第五章还将法律的存在与实效分开讨论。规则能否被有效执行，与它能否被识别为某一体系的法律相互有关，却不是可以直接画等号的两件事。对读者而言，这部分提醒我们：分析法律的权威，不能跳过法律作为一个有边界、有延续性并由机构维系的秩序这一前提。</p><p class="source">原著第五章：<a href="https://academic.oup.com/book/10820/chapter/158978650">The Identity of Legal Systems</a>。</p>
<h2 id="book-rule-guidance">法治要求如何共同支持人的行为计划</h2><p><strong>法治的出发点是法律能够指导行为，而不是政府声称自己有良好目的。</strong>如果一个人无法知道适用于自己的规则，或者规则在其行动之后才被制定，法律就难以发挥事前指导作用。公开性、前瞻性和清晰性因此首先保护的是人依据规则安排生活的能力，而不只是提高行政机关的管理效率。</p><p>相对稳定与具体情境下的规则调整也需要一起理解。稳定不意味着所有法律永久不变，明确也不意味着可以穷尽一切例外；关键在于，制度是否仍给人以合理机会了解要求、调整计划并预期执行。频繁变化且缺乏过渡安排的规则，即使每次都已经公布，也可能削弱这种能力。</p><p>法治还包含机构条件。规则文字再明确，如果法院缺乏独立性、个人无法实际接近救济程序，或者执法机关可以选择性搁置法律，规则与人的行动之间仍会断开。因此，第十一章并非只谈立法技术；司法、程序和执行控制是规则得以可信地指导行为的组成部分。</p><p><strong>这也解释了法治与正义为什么既有关联，又不能互相替代。</strong>可预期的法律可以减少任意性，却不自动回答财富分配、政治参与和权利内容是否公平。承认一种制度具有部分法治品质，不是为它的实体不正义辩护；指出它不正义，也不意味着无需继续分析公开、稳定和独立审查各自发挥了什么作用。</p><p class="source">原著第十一章：<a href="https://academic.oup.com/book/10820/chapter/158984424">The Rule of Law and its Virtue</a>。</p>
<h2 id="book-dissent">有理由不服从，是否就拥有不服从的权利</h2><p><strong>最后两章的重要区分，是为某次违法提供道德理由，不等于证明存在一项一般的不服从权利。</strong>一个人可能在特定情境下有充分理由违反法律，但法律制度应如何对待这种行为，还涉及他人的权利、共同决策的程序以及政治参与的机会。拉兹由此把行为的正当理由、道德权利与法律上的考虑分开。</p><p>公民不服从通常指向改变公共政策或表达政治立场，良心拒绝则更直接体现个人不愿亲自参与违背其信念的行为。两者可能交叠，但并非总是需要同一种法律回应。判断时不能只问动机是否真诚，还要考察政治参与条件、对第三人的影响，以及豁免或宽容是否会损害他人的平等地位。</p><p>把这一部分放回全书，才能看清拉兹的论证不是在“全面服从”和“任意违法”之间二选一。法律可以提出权威要求，个人也可以要求说明其正当性；否认一项普遍的道德守法义务，并不直接取消法律责任，更不自动赋予每个人不受干预地违反任何法律的资格。</p><p class="source">原著第十四、十五章：<a href="https://academic.oup.com/book/10820/chapter/158986200">A Right to Dissent? I. Civil Disobedience</a>；<a href="https://academic.oup.com/book/10820/chapter-abstract/158986818">A Right to Dissent? II. Conscientious Objection</a>。</p>'''
if not s.find(id='book-systems'):s.find(id='section-9').insert_before(frag(extra))
h=s.find(id='section-10');ps=[]
for n in h.find_next_siblings():
 if n.name=='h2':break
 if n.name=='p' and 'source' not in n.get('class',[]):ps.append(n)
ps[0].clear();ps[0].append(frag('<strong>第一，法律原则能否都被理解为社会来源或法外裁量材料，是解释主义提出的挑战。</strong>David B. Lyons在1982年《The Philosophical Review》的书评摘要中，把本书放在法律与道德关系及德沃金批评的争论背景下讨论。争点在于，法院关于原则的推理是在识别已有法律，还是在法律没有给出答案时进行补充判断；不同回答将改变对疑难案件中裁量范围的理解。'))
ps[1].clear();ps[1].append(frag('<strong>第二，法律的道德约束是否过度依赖个人态度，是William J. Howard的直接质疑。</strong>他在1982年《The American Journal of Jurisprudence》书评中，将拉兹关于没有普遍道德守法义务及尊重法律的论述，与自然法传统关于正当政府、理性和共同生活的看法对照，并据此质疑个人是否成了权威的最终来源。这是批评者对拉兹的解释，不能倒过来当作拉兹自己主张“只有喜欢某项法律才应遵守”。'))
nav=s.select_one('.reading-directory nav')
for id,title in [('book-systems','法律体系的同一性'),('book-rule-guidance','法治与行为计划'),('book-dissent','不服从的理由与权利')]:
 if not nav.select_one('a[href="#'+id+'"]'):
  a=s.new_tag('a',href='#'+id);a.string=title;nav.append(a)
write(P[2],s)
summaries=['18条｜平台算法选择、数字消费救济、能源AI、神经数据与网络安全','尼尔·理查兹：《监控的危险》','约瑟夫·拉兹：《法律的权威》','5项｜司法数据标注、智能体治理、科技立法、法律服务与版权执行']
rootfiles=['index.html','archive.html','briefs.html','papers.html','classics.html','new-works.html']
for name in rootfiles:
 s=load(name)
 for nav in s.select('.navlinks'):
  for a in nav.select('a'):
   if a.get_text(strip=True) in LABEL:a['href']=P[LABEL.index(a.get_text(strip=True))]
 if name=='index.html':
  for i,c in enumerate(s.select('.portal-card')):
   c['href']=P[i];c.select_one('.portal-latest small').string='2026.09.08 · 最新一期';c.select_one('.portal-latest strong').string=summaries[i]
  for a in list(s.select('.navlinks a')):
   if '历史' in a.get_text():a.decompose()
 elif name in ['briefs.html','papers.html','classics.html','new-works.html']:
  i=['briefs.html','papers.html','classics.html','new-works.html'].index(name);ls=s.select_one('.issue-list')
  for d in s.select('.issue-date'):
   for t in list(d.find_all(string=True,recursive=False)):
    if '最新一期' in t:t.extract()
  if not any(a.get('href')==P[i] for a in ls.select('a')):
   ls.insert(0,frag(f'<article class="issue-row"><div class="issue-date"><strong>2026.09.08</strong>最新一期</div><div class="issue-main"><h3>{E(summaries[i])}</h3></div><a class="issue-action" href="{P[i]}">阅读全文 →</a></article>'))
 elif name=='archive.html':
  lead=s.select_one('.lead')
  if lead:lead.string='按栏目查阅历期简报、论文精读、经典著作与研究新作。'
 write(name,s)
for path in P:
 s=load(path)
 for a in s.select('.navlinks a'):
  if a.get_text(strip=True) in LABEL:a['href']=Path(P[LABEL.index(a.get_text(strip=True))]).name
 write(path,s)
print('Completed four source pages, homepage, archive and all four history lists.')
