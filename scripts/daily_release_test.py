"""Offline regression: no external writes, no real user accounts, no test publication."""
from copy import deepcopy
from datetime import datetime, timedelta, timezone
import importlib.util
import json
from pathlib import Path
import shutil
import tempfile
import unittest
from unittest.mock import patch
import daily_release as release
import edition_gate as gate

ROOT = Path(__file__).resolve().parents[1]

class Rules(unittest.TestCase):
    def test_superseded_checkout_cannot_retry_an_older_deployment(self):
        class API:
            def request(self, method, path, data=None):
                if method == 'GET' and path == '/git/ref/heads/main':
                    return {'object': {'sha': 'newer-head'}}
                raise AssertionError('Stale checkout attempted an external action: '+method+' '+path)
        with tempfile.TemporaryDirectory() as temp:
            with patch.object(release,'ROOT',Path(temp)), patch.object(release,'git',return_value='old-head'), patch.object(release,'load',return_value={'date':'2026-09-08'}), patch.object(gate,'validate'), patch.dict(release.os.environ,{'GITHUB_REPOSITORY':release.REPO}):
                result=release.run(datetime.fromisoformat('2026-09-08T23:55:00+08:00'),API())
        self.assertEqual(result['action'],'superseded')
        self.assertEqual(result['status'],'pending')
        self.assertFalse(result['delivered'])

    def test_midnight_belongs_to_previous_edition(self):
        self.assertEqual(str(release.expected_day(datetime.fromisoformat('2026-09-09T00:17:00+08:00'))),'2026-09-08')
        self.assertEqual(str(release.expected_day(datetime.fromisoformat('2026-09-09T20:17:00+08:00'))),'2026-09-09')
    def test_deadline_is_not_the_producer_schedule(self):
        n=datetime.fromisoformat('2026-09-09T21:47:00+08:00')
        self.assertFalse(release.overdue(n, n.date()))
        self.assertTrue(release.overdue(n+timedelta(minutes=30), n.date()))
    def test_pending_is_not_delivered(self):
        self.assertEqual(release.delivery_action([dict(id=1,status='in_progress',conclusion=None)],True),'running')
    def test_success_requires_live_entry_points(self):
        r=[dict(id=1,status='completed',conclusion='success',run_attempt=1)]
        self.assertEqual(release.delivery_action(r,True),'delivered')
        self.assertEqual(release.delivery_action(r,False),'dispatch')
    def test_retry_budget_is_bounded(self):
        r=[dict(id=1,status='completed',conclusion='failure',run_attempt=1)]
        self.assertEqual(release.delivery_action(r,False),'rerun')
        r[0]['run_attempt']=3
        self.assertEqual(release.delivery_action(r,False),'exhausted')
    def test_old_success_does_not_hide_latest_failure(self):
        r=[dict(id=1,status='completed',conclusion='success'),dict(id=2,status='completed',conclusion='failure')]
        self.assertEqual(release.delivery_action(r,True),'rerun')
    def test_notifications_are_deduplicated_and_closed_only_after_success(self):
        class API:
            def __init__(self):self.rows=[];self.posts=0;self.closed=False
            def request(self,method,path,data=None):
                if method=='GET':return self.rows
                if method=='POST' and path=='/issues':self.posts+=1;self.rows=[dict(data,number=1)]
                if method=='PATCH' and data.get('state')=='closed':self.closed=True
                if method=='PATCH' and 'body' in data:self.rows[0]['body']=data['body']
                return {}
        a=API();day=datetime(2026,9,8).date()
        release.notify(a,day,'缺少已核验正文');release.notify(a,day,'缺少已核验正文')
        self.assertEqual(a.posts,1);self.assertFalse(a.closed)
        release.notify(a,day);self.assertTrue(a.closed)

class Candidate(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory(prefix='release-test-')
        self.root=Path(self.temp.name)/'site'
        shutil.copytree(ROOT,self.root,ignore=shutil.ignore_patterns('.git','__pycache__'))
        self.manifest=release.load(self.root/'data/current-edition.json')
        self.now=datetime.fromisoformat(self.manifest['date']+'T23:50:00+08:00')
        news=release.document(self.root,self.manifest['pages']['brief']).select('.brief-item')
        self.record=deepcopy(self.manifest)
        self.record['review']={'status':'verified','checked_at':self.now.isoformat(),
            'last_news_scan_at':(self.now-timedelta(minutes=15)).isoformat(),
            'checks':{k:True for k in release.CHECKS},
            'sha256':{p:release.digest(self.root/p) for p in self.manifest['pages'].values()},
            'news_event_times':{n['id']:(self.now-timedelta(hours=12)).isoformat() for n in news}}
    def tearDown(self):self.temp.cleanup()
    def test_verified_unchanged_candidate_accepted(self):
        self.assertEqual(release.verify_candidate(self.root,self.record,self.now),self.manifest)
    def test_missing_review_cannot_advance_homepage(self):
        before=(self.root/'index.html').read_bytes()
        self.record['review']['status']='draft'
        with self.assertRaises(release.ReleaseError):release.promote(self.root,self.record,self.now)
        self.assertEqual(before,(self.root/'index.html').read_bytes())
    def test_modified_body_requires_new_review(self):
        p=self.root/self.manifest['pages']['paper'];p.write_text(p.read_text()+' ')
        with self.assertRaises(release.ReleaseError):release.verify_candidate(self.root,self.record,self.now)
    def test_missing_fourth_body_rejected(self):
        (self.root/self.manifest['pages']['classic']).unlink()
        with self.assertRaises(release.ReleaseError):release.verify_candidate(self.root,self.record,self.now)
    def test_expired_news_and_final_scan_rejected(self):
        key=next(iter(self.record['review']['news_event_times']))
        self.record['review']['news_event_times'][key]=(self.now-timedelta(hours=73)).isoformat()
        with self.assertRaises(release.ReleaseError):release.verify_candidate(self.root,self.record,self.now)
        self.record['review']['news_event_times'][key]=self.now.isoformat()
        self.record['review']['last_news_scan_at']=(self.now-timedelta(hours=3)).isoformat()
        with self.assertRaises(release.ReleaseError):release.verify_candidate(self.root,self.record,self.now)
    def test_rollback_and_same_day_are_rejected(self):
        with self.assertRaises(release.ReleaseError):release.promote(self.root,self.record,self.now)
    def test_gate_failure_does_not_touch_source(self):
        old=deepcopy(self.manifest);old['date']=(self.now.date()-timedelta(days=1)).isoformat()
        (self.root/'data/current-edition.json').write_text(json.dumps(old))
        before={p:(self.root/p).read_bytes() for p in release.ENTRY}
        with patch.object(gate,'validate',side_effect=AssertionError('invalid source')):
            with self.assertRaises(AssertionError):release.promote(self.root,self.record,self.now)
        self.assertTrue(all((self.root/p).read_bytes()==s for p,s in before.items()))
    def test_atomic_completion_preserves_history_and_is_idempotent(self):
        old=deepcopy(self.manifest);old['date']=(self.now.date()-timedelta(days=1)).isoformat()
        (self.root/'data/current-edition.json').write_text(json.dumps(old))
        before={p:release.digest(p) for p in (self.root/'articles').glob('*.html') if p.relative_to(self.root).as_posix() not in self.manifest['pages'].values()}
        changed=release.promote(self.root,self.record,self.now)
        self.assertIn('data/current-edition.json',changed)
        self.assertTrue(all(release.digest(p)==s for p,s in before.items()))
        current=release.load(self.root/'data/current-edition.json')
        self.assertEqual(current,self.manifest)
        original=gate.ROOT
        try:
            gate.ROOT=self.root;gate.validate(current)
        finally:gate.ROOT=original
        with self.assertRaises(release.ReleaseError):release.promote(self.root,self.record,self.now)
    def test_future_unfinished_edition_does_not_invalidate_current(self):
        p=self.root/'articles/2099-01-01-new-works.html'
        p.write_bytes((self.root/self.manifest['pages']['newworks']).read_bytes())
        original=gate.ROOT
        try:
            gate.ROOT=self.root;gate.validate(self.manifest)
        finally:gate.ROOT=original

if __name__=='__main__':unittest.main(verbosity=2)
