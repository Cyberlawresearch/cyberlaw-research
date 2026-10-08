"""Apply verified source corrections before validation and Pages deployment.

The source HTML for 2026-10-08 is kept as the original fact-edition snapshot.
This build step materializes the verified domestic additions and research analysis
into the deployed artifact, while preserving a transparent audit record in
.github/editions/2026-10-08.news.json.
"""
from __future__ import annotations

from copy import deepcopy
import json
import re
from pathlib import Path

from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parents[1]
PAGE = ROOT / "articles/2026-10-08-tech-law-brief.html"
ANALYSIS_FILES = [ROOT / "assets" / f"oct8-a{i}.json" for i in range(1, 5)]

MOHRSS_ANALYSIS = [
    "征求意见稿的关键不只是增加若干权益条款，而是以部门规章形式承认传统劳动关系与完全独立承揽之间存在需要劳动法最低保障的用工类型。平台的劳动规则、算法分配、奖惩和申诉程序因此可能成为可被行政监管和争议审查的用工管理行为。",
    "《新就业形态用工分层分类规则及平台算法合规清单》：可对照劳动关系、不完全符合劳动关系和其他合作用工三类情形，梳理报酬、工时、奖惩、算法说明、个人信息、职业伤害和争议处理的责任主体与证据要求。",
    "《平台用工“中间类型”的劳动法定位》：研究部门规章将受劳动管理但未完全建立劳动关系的劳动者纳入保护后，最低劳动标准、合同自由、责任主体和劳动关系认定之间如何衔接。",
    "我国此前主要通过指导意见、平台劳动规则指引、算法和劳动报酬等专项指南，以及职业伤害保障试点完善新就业形态保护。此次征求意见稿首次以规章形式系统整合基本权益、算法规则、用工分类、争议解决和监管责任。",
    "征求意见截至11月8日。最终制度的实际影响取决于“不完全符合确立劳动关系情形”的识别标准、平台与合作企业责任分配、算法规则的可审查程度，以及行政执法与争议解决程序能否衔接。",
]

DOMESTIC = [
    {
        "date": "2026-10-08",
        "title": "人社部就《新就业形态劳动者权益保障办法》公开征求意见",
        "meta": "2026-10-08 · 中国 · 人力资源社会保障部",
        "original": "人力资源社会保障部关于《新就业形态劳动者权益保障办法（征求意见稿）》公开征求意见的通知",
        "fact": "人力资源社会保障部10月8日发布《新就业形态劳动者权益保障办法（征求意见稿）》，向社会公开征求意见至11月8日。这是我国首次拟以规章形式，将企业实施劳动管理、但不完全符合确立劳动关系情形的新就业形态劳动者纳入劳动法律制度保障。征求意见稿共54条，涉及基本劳动权益、劳动规则与算法、企业用工分类、纠纷解决、监管职责和法律责任；目前仍处于公开征求意见阶段，尚未生效。",
        "url": "https://www.news.cn/politics/20261008/6e01730616fc4900b2892af1e904914e/c.html",
        "source": "人力资源社会保障部／新华社",
        "analysis": MOHRSS_ANALYSIS,
    },
    {
        "date": "2026-10-06",
        "title": "DeepSeek据报新一轮融资认购额超过800亿元，拟为上市和国产算力生态储备资金",
        "meta": "2026-10-06 · 中国 · 中国人工智能产业／DeepSeek",
        "original": "DeepSeek set to net over $12 billion in new fundraising, source says",
        "fact": "Reuters援引知情人士称，DeepSeek本轮融资已获得超过800亿元人民币的认购承诺，最终规模可能达到1000亿元，目标估值约5000亿元；宁德时代和腾讯据报作出较大金额承诺。公司正为潜在境内上市作准备，并与华为推进面向昇腾芯片的软件工具合作。融资规模、估值和投资者安排目前尚未由DeepSeek或相关投资者正式确认。",
        "url": "https://www.reuters.com/world/asia-pacific/deepseek-raise-least-12-billion-tencent-backed-funding-bloomberg-news-reports-2026-10-06/",
        "source": "Reuters",
    },
    {
        "date": "2026-10-08",
        "title": "腾讯据报考虑发行至多50亿美元境外债券，用于扩大AI和计算基础设施投入",
        "meta": "2026-10-08 · 中国 · 腾讯控股",
        "original": "Tencent mulls $5 billion bond sale to push AI ambitions, Bloomberg News reports",
        "fact": "Reuters转引Bloomberg报道称，腾讯正在考虑通过境外债券发行筹集至多50亿美元，以支持人工智能和计算基础设施投入。报道所述方案仍处于考虑阶段，腾讯尚未发布正式发行公告，债券币种、期限、定价、承销安排和最终募集金额均有待确定。",
        "url": "https://www.reuters.com/world/asia-pacific/tencent-mulls-5-billion-bond-sale-push-ai-ambitions-bloomberg-news-reports-2026-10-08/",
        "source": "Reuters",
    },
    {
        "date": "2026-10-08",
        "title": "中国加快建设AI数据中心，运营和在建容量据报合计大幅扩张",
        "meta": "2026-10-08 · 中国 · 中国AI数据中心产业",
        "original": "China races to build data centres in bid for AI supremacy",
        "fact": "Financial Times 10月8日报道，中国正依托能源、土地和建设能力加快数据中心布局。报道援引SemiAnalysis数据称，中国现有数据中心计算容量约24GW，另有约50GW在建；内蒙古乌兰察布已成为重要增长区域，华为、阿里巴巴和字节跳动等企业持续投入。报道同时指出，先进芯片供给、水资源、网络安全和项目实际利用率仍是关键约束。",
        "url": "https://www.ft.com/content/e1dd8bff-b06d-4a40-bbb7-c0a6a36f1c8e",
        "source": "Financial Times",
    },
]


def load_analysis() -> dict[str, list[str]]:
    data: dict[str, list[str]] = {}
    for path in ANALYSIS_FILES:
        data.update(json.loads(path.read_text(encoding="utf-8")))
    return data


def direct(item, selector: str):
    return item.select_one(f":scope > {selector}")


def replace_shell(item, row: dict[str, str], number: int, soup: BeautifulSoup) -> None:
    item["id"] = f"research-item-domestic-{number}"
    item["data-event-date"] = row["date"]
    item["data-original-title"] = row["original"]
    item["data-citation"] = json.dumps(
        {
            "type": "news",
            "cnTitle": row["title"],
            "originalTitle": row["original"],
            "sourceName": row["source"],
            "date": row["date"],
            "url": row["url"],
            "foreign": False,
        },
        ensure_ascii=False,
        separators=(",", ":"),
    )
    direct(item, "h3").string = f"{number}. {row['title']}"
    direct(item, ".brief-meta").string = row["meta"]
    original = direct(item, ".brief-original")
    if original is None:
        original = soup.new_tag("p", attrs={"class": "brief-original"})
        direct(item, ".brief-fact").insert_before(original)
    original.clear()
    strong = soup.new_tag("strong")
    strong.string = "原始题名："
    original.append(strong)
    original.append(row["original"])
    direct(item, ".brief-fact").string = row["fact"]
    source = direct(item, ".source")
    source.clear()
    source.append("原始来源：")
    link = soup.new_tag("a", href=row["url"])
    link.string = row["source"]
    source.append(link)


def fill_analysis(item, row: list[str], soup: BeautifulSoup) -> None:
    paragraphs = [
        p
        for p in item.find_all("p", recursive=False)
        if "analysis-pending" in p.get("class", []) or p.has_attr("data-a")
    ][:3]
    labels = ["法治研判：", "智库选题参考：", "论文选题："]
    if len(paragraphs) != 3:
        raise ValueError(f"missing analysis slots: {item.get('id')}")
    for paragraph, label, text in zip(paragraphs, labels, row[:3]):
        paragraph.attrs.pop("style", None)
        paragraph.attrs.pop("data-a", None)
        paragraph["class"] = [x for x in paragraph.get("class", []) if x != "analysis-pending"]
        paragraph.clear()
        strong = soup.new_tag("strong")
        strong.string = label
        paragraph.append(strong)
        paragraph.append(text)
    insight = direct(item, "script.brief-insight")
    if insight is None:
        insight = soup.new_tag("script", type="application/json")
        insight["class"] = "brief-insight"
        direct(item, ".source").insert_before(insight)
    insight.string = json.dumps(
        {"background": row[3], "outlook": row[4]},
        ensure_ascii=False,
        separators=(",", ":"),
    )


def main() -> None:
    if not PAGE.is_file():
        return
    source = PAGE.read_text(encoding="utf-8")
    if "人社部就《新就业形态劳动者权益保障办法》公开征求意见" in source:
        return
    soup = BeautifulSoup(source, "html.parser")
    wrap = soup.select_one(".article-body .article-wrap")
    items = wrap.select(":scope > article.brief-item") if wrap else []
    if len(items) != 20:
        raise ValueError(f"unexpected Oct 8 source item count: {len(items)}")
    international_heading = next(
        (node for node in wrap.find_all("h2", recursive=False) if node.get_text(strip=True) != "国内"),
        None,
    )
    if international_heading is None:
        raise ValueError("missing international heading")

    base_shells = items[-3:]
    shells = [*base_shells, deepcopy(base_shells[0])]
    kept = items[:17]
    domestic_heading = soup.new_tag("h2")
    domestic_heading.string = "国内"
    international_heading.insert_before(domestic_heading)

    data = load_analysis()
    for index, (shell, row) in enumerate(zip(shells, DOMESTIC), 1):
        replace_shell(shell, row, index, soup)
        analysis = row.get("analysis") if index == 1 else data[str(index - 1)]
        fill_analysis(shell, analysis, soup)
        international_heading.insert_before(shell)

    international_heading.string = "国际"
    for index, item in enumerate(kept, 5):
        heading = direct(item, "h3")
        heading.string = f"{index}. {re.sub(r'^\s*\d+[.、]\s*', '', heading.get_text(' ', strip=True))}"
        fill_analysis(item, data[str(index - 1)], soup)

    lead = soup.select_one(".article-hero .lead")
    if lead:
        lead.string = "2026年10月8日 · 21条"
    if soup.body:
        soup.body["data-analysis-status"] = "completed"

    PAGE.write_text(str(soup), encoding="utf-8")
    print(json.dumps({"page": str(PAGE.relative_to(ROOT)), "news_count": 21, "domestic": 4, "foreign": 17}, ensure_ascii=False))


if __name__ == "__main__":
    main()
