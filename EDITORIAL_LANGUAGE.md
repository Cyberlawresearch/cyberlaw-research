# 科技法研究每日推送：中文语言与译名审校规范

适用范围：全球科技法简报、域外法学论文精读、法学经典著作、科技法研究新作、技术课程及媒体摘编的编辑文字。

## 一、译名与原文

- 优先使用已有通行中文译名。核对原题与学术语境；没有公认译名时，采用准确自然的中文译名并保留完整原始英文/其他语言题名，不将编辑拟译称为正式译名。
- 专业概念根据其法律功能翻译，不把英文词形逐字移植。例如 Free Speech Is a Triangle 译作“言论自由的三角结构”；curational due process 在平台语境下译为“内容治理的正当程序”，保留英文术语以便对照；Broken Promises of Privacy 的中文编辑题名使用“隐私保护的落空：如何应对匿名化失效”。温斯坦利的 True Magistracy Restored 涉及治理制度，不是单个官职的恢复。原始题名、作者、引文、DOI、版本与来源链接不得改写。
- 根据法域分别辨别 regulation 的法规、规制与监管，liability 的法律责任与赔偿责任，remedy 的救济与补救，natural rights（自然权利）与 rights of nature（自然界的权利）。不得用通用词表机械替换。区分个人信息匿名化、去标识化、假名化；区分主体资格、权利能力、行为归属和责任承担。
- 书籍、论文标题、归档、关联阅读及检索索引保持一致；章节名如为编者自拟，应准确说明本节论题，不冒充原作者的标题或直接引语。

## 二、各栏中文表达

- 新闻：先明确谁在何时采取何种措施，说明文件、裁判、调查、意见征求等真实法律状态及实际影响。避免英文被动句直译和“获建议”“遭凭证入侵”等搭配；没有信息量的重复收尾删去。事实、研判及前瞻仍严格分开。
- 论文：按问题、论证及制度后果展开；读者应看得出作者提出什么、根据什么、争议在哪里。避免“核心挑战”“制度增量”“把某种理论放进……”等悬空表达，用具体法律关系和规范命题代替。
- 经典：采用准确译名和通行法学、思想史术语；以全书结构、各章论证和争议组织文本，不滥用“地图”“三句话带走”等讲稿式用语。严格区分作者原论、后世评价与当代延伸。
- 新作：明确研究问题、主要发现和研究方法；自然介绍题名、作者、刊物与日期，避免机械拼接出版字段，不能把作者提出的制度设想写成已验证结果。
- 技术课程：保留面向法律研究者的易懂例子，技术术语首次出现给出必要定义；避免过度口语化、营销式标题和无助于理解的比喻。
- 媒体摘编：直接引语及原始短摘逐字保留。编辑说明用“正文涉及相关主题”“来源暂无法访问”等读者容易理解的表述，保留实际核验局限，不掩盖遗漏。

## 三、发布前审校

每次生成内容后，先对照原文核对专业概念、否定关系、限定条件、主语与法律状态，再从中文读者角度通读全文。将过长定语拆开，主动交代施事者，消除生硬直译与无意义重复。标题应体现具体研究问题或事实，避免为了去机器翻译而改变事实、作者立场、术语精确性和出处。

历史资料的语言维护使用经逐句核对的 `scripts/editorial_language_edits.json` 与构建阶段的 `scripts/apply_editorial_language.py`，先修订构建副本，再生成检索索引。保留源文件、直接引语、原题、链接、章节锚点及历史核验记录。全站巡检只生成待复核候选项，不以关键词自动认定语病，也不得把巡检当作逐篇人工审校。构建报告保存在 Actions 测试产物中，不显示给读者。

### 本轮核对依据（译名示例）
- Balkin, [Free Speech Is a Triangle](https://columbialawreview.org/content/free-speech-is-a-triangle/)，原文论述三方结构、curational due process 和 information fiduciaries。
- Ohm, [Broken Promises of Privacy](https://www.uclalawreview.org/broken-promises-of-privacy-responding-to-the-surprising-failure-of-anonymization-2/)，原刊摘要强调匿名化措施未能兑现隐私保护承诺。
- Cohen, [Configuring the Networked Self](https://juliecohen.com/configuring-the-networked-self/)，作者列出的各部分涉及文化、主体性与日常实践中的 play。
- 温斯坦利，参见[原著题名及文本](https://www.davidmhart.com/liberty/Levellers/Winstanley/1652-LawFreedom/index.html)及[中国农业历史与文化网站的译名与制度分析](https://www.ihns.ac.cn/agri-his/history/nszl_1/202607/t20260720_8252427.html)。本轮采用简明中文编辑题名，不声称为某一中译本正式书名。
