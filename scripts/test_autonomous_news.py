"""Unit tests requiring no API key, GitHub mutation or web requests."""
from pathlib import Path
from datetime import datetime
from zoneinfo import ZoneInfo
import sys
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parent))
import autonomous_news_research as mod

class ResearchSafetyTests(unittest.TestCase):
 def test_urls(self):
  for u in ("http://example.org/x","https://localhost/x","https://127.0.0.1/x",
            "https://10.0.0.1/a","https://[::1]/","https://user@site.example/x"):
   self.assertFalse(mod.safe_url(u),u)
  self.assertTrue(mod.safe_url("https://www.gov.uk/government/news/some-article"))
 def test_evidence_quote(self):
  self.assertTrue(mod.quote_exists("具体行政处罚决定已经作出","报道指出：具体行政处罚决定已经作出。"))
  self.assertFalse(mod.quote_exists("已经颁布并实施新法","当前文件只是公开征求意见。"))
 def test_duplicates(self):
  t=["某国公布人工智能监管规则征求意见稿"]
  self.assertTrue(mod.duplicate(t[0],"https://a.cn/a",t,set()))
  self.assertTrue(mod.duplicate("其他标题","https://a.cn/a",[],{"https://a.cn/a"}))
  self.assertFalse(mod.duplicate("美国法院裁判未成年人平台法","https://x.cn/b",t,set()))
 def test_coverage_gate(self):
  dt=datetime(2026,10,17,19,15,tzinfo=ZoneInfo("Asia/Shanghai"))
  with self.assertRaisesRegex(ValueError,"Source groups incomplete"):
   mod.make_draft([],[],dt)
  with self.assertRaisesRegex(ValueError,"Only 0"):
   mod.make_draft([],[{"source_group":s[0],"status":"checked"} for s in mod.SEARCHES],dt)
 def test_schema_all_required(self):
  for v in (mod.CANDIDATE_SCHEMA,mod.VERIFY_SCHEMA):
   self.assertEqual(set(v["required"]),set(v["properties"]))

if __name__=="__main__":unittest.main()
