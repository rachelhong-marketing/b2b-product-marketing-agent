import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

from productmarketing import check, cli, export, icp, messaging
from productmarketing.util import read_csv_rows

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "sample-data"


def deal(i, ind, size, outcome, acv="", days="40", kept="", role="RevOps manager", reason="", comp=""):
    return dict(deal_id=f"D{i}", industry=ind, company_size=size, buyer_role=role, outcome=outcome, acv=acv, days_to_close=days,
                use_case="duplicate cleanup", retained_12m=kept, lost_reason=reason, competitor=comp)


class Icp(unittest.TestCase):
    def test_small_segments_are_not_ranked(self):
        deals = [deal(i, "A", "big", "won", "1000", kept="yes") for i in range(3)]
        segs = icp.segments(deals)
        self.assertFalse(segs[0]["rankable"])
        self.assertNotIn("score", segs[0])

    def test_needs_wins_not_just_deals(self):
        deals = [deal(i, "A", "big", "lost", reason="no budget") for i in range(8)] + [deal(9, "A", "big", "won", "1000", kept="yes")]
        self.assertFalse(icp.segments(deals)[0]["rankable"])

    def test_better_segment_scores_higher(self):
        good = [deal(i, "Good", "mid", "won", "50000", days="20", kept="yes") for i in range(4)] + [deal(9, "Good", "mid", "lost")]
        bad = [deal(i + 20, "Bad", "mid", "lost") for i in range(4)] + [deal(30 + i, "Bad", "mid", "won", "5000", days="90", kept="no") for i in range(3)]
        segs = {s["industry"]: s for s in icp.segments(good + bad)}
        self.assertGreater(segs["Good"]["score"], segs["Bad"]["score"])

    def test_personas_and_lost_reasons(self):
        deals = [deal(1, "A", "s", "won", role="CRM administrator"), deal(2, "A", "s", "won", role="CRM administrator"),
                 deal(3, "A", "s", "won", role="RevOps manager"), deal(4, "A", "s", "lost", reason="no budget", comp="tidybase")]
        self.assertEqual(icp.personas(deals)[0], ("CRM administrator", 2))
        self.assertEqual(icp.lost_reasons(deals), [("no budget", 1)])
        self.assertEqual(icp.lost_competitors(deals), [("tidybase", 1)])


class Messaging(unittest.TestCase):
    def ctx(self):
        c = messaging.analyze(DATA)
        c["statement_parts"] = messaging.statement_parts(c)
        return c

    def test_claim_without_proof_cannot_be_a_pillar(self):
        c = self.ctx()
        claims = [x["d"]["claim"] for x in c["pillars"]]
        nop = "Works across customer relationship management (CRM), billing and support systems"
        self.assertNotIn(nop, claims)
        self.assertIn(nop, [x["d"]["claim"] for x in c["no_proof"]])
        self.assertEqual(len(claims), 3)

    def test_shared_claims_are_flagged_and_rank_lower(self):
        c = self.ctx()
        by = {x["d"]["id"]: x for x in c["ranked"]}
        self.assertEqual(by["d1"]["overlap"], [])
        self.assertEqual(sorted(by["d4"]["overlap"]), ["Clearline Data", "Purestream"])
        self.assertGreater(by["d1"]["score"], by["d4"]["score"])

    def test_output_is_deterministic_and_has_open_slots(self):
        a, b = messaging.render(self.ctx()), messaging.render(self.ctx())
        self.assertEqual(a, b)
        self.assertIn("[MISSING", a)
        self.assertIn("Response: [MISSING", a)

    def test_missing_profile_fields_raise(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "p.json"
            p.write_text(json.dumps({"brand": "x"}))
            with self.assertRaises(ValueError):
                messaging.load_profile(p)

    def test_empty_inputs_do_not_crash(self):
        with tempfile.TemporaryDirectory() as d:
            (Path(d) / "company").mkdir()
            shutil.copy(DATA / "company" / "product-profile.json", Path(d) / "company")
            ctx, doc = cli.build(d, Path(d) / "out")
            text = doc.read_text()
            self.assertIn("[MISSING] none provided", text)


class Export(unittest.TestCase):
    def test_brand_profile_has_what_the_content_assistant_needs(self):
        with tempfile.TemporaryDirectory() as d:
            ctx, _ = cli.build(DATA, d)
            b = json.loads((Path(d) / "brand-profile.json").read_text())
        for k in ("brand", "domain", "audiences", "themes", "avoid_words", "competitors"):
            self.assertIn(k, b)
        for name, t in b["themes"].items():
            self.assertTrue(t["triggers"], name)
            self.assertTrue(0 <= t["fit"] <= 1)
        self.assertEqual(max(t["fit"] for t in b["themes"].values()), 1.0)

    def test_brand_profile_loads_in_the_content_strategy_assistant_if_present(self):
        other = ROOT.parent / "b2b-content-strategy-assistant"
        if not other.exists():
            self.skipTest("content strategy assistant repo not next to this one")
        sys.path.insert(0, str(other))
        try:
            from contentstrategy import brand
            with tempfile.TemporaryDirectory() as d:
                cli.build(DATA, d)
                b = brand.load(Path(d) / "brand-profile.json")
            self.assertTrue(b["themes"])
        finally:
            sys.path.remove(str(other))

    def test_positioning_json_contents(self):
        with tempfile.TemporaryDirectory() as d:
            cli.build(DATA, d)
            p = json.loads((Path(d) / "positioning.json").read_text())
        self.assertTrue(p["pillars"])
        self.assertTrue(all(len(x["proof"]) >= 1 for x in p["pillars"]))
        self.assertEqual(p["statement_parts"][0]["label"], "For")


class Check(unittest.TestCase):
    PROFILE = messaging.load_profile(DATA / "company" / "product-profile.json")

    def built(self):
        with tempfile.TemporaryDirectory() as d:
            _, doc = cli.build(DATA, d)
            return doc.read_text()

    def test_fresh_build_fails_until_slots_and_proof_are_fixed(self):
        res = check.check_doc(self.built(), self.PROFILE)
        msgs = " ".join(m for _, m in res)
        self.assertIn("[MISSING] slots", msgs)

    def test_finished_doc_passes(self):
        t = self.built()
        claim = "Keep them out: monitoring so duplicate records don't come back"
        t = t.replace(f"[MISSING: write it. Strongest pillar: {claim}]", "Duplicate records stay out because the platform keeps watching.")
        t = t.replace(f"[MISSING: write it. Claim nobody tracked makes: {claim}]", "It keeps monitoring data quality after setup.")
        t = t.replace("Response: [MISSING: from sales and win-loss calls]", "Response: covered in the sales playbook")
        self.assertNotIn("[MISSING", t)
        self.assertEqual(check.check_doc(t, self.PROFILE), [])

    def test_avoid_words_are_caught_but_the_avoid_list_itself_is_not(self):
        t = self.built()
        self.assertEqual([m for _, m in check.check_doc(t, self.PROFILE) if "avoid list" in m], [])
        res = check.check_doc(t.replace("Edit the wording", "A revolutionary edit of the wording"), self.PROFILE)
        self.assertTrue(any("revolutionary" in m for _, m in res))

    def test_acronym_must_be_spelled_out(self):
        res = check.check_doc("CRM first\n## Words to avoid\n", self.PROFILE)
        self.assertTrue(any("acronym 'CRM'" in m for _, m in res))


class Hygiene(unittest.TestCase):
    def test_no_real_company_names_or_personal_details(self):
        banned = ["epsilon", "walmart", "pubmatic", "neustar", "rachel", "@gmail"]
        for p in ROOT.rglob("*"):
            rel = p.relative_to(ROOT).parts
            if p.is_file() and p.suffix in (".py", ".md", ".csv", ".json") and "output" not in rel and "tests" not in rel and ".git" not in rel:
                low = p.read_text(encoding="utf-8", errors="ignore").lower()
                for w in banned:
                    if w in low and not (w == "rachel" and p.name in ("README.md", "LICENSE")):
                        self.fail(f"{w!r} found in {p.relative_to(ROOT)}")

    def test_sample_data_is_marked_made_up(self):
        self.assertIn("Made-up", (DATA / "company" / "product-profile.json").read_text())
        self.assertIn("Made-up", (DATA / "customers" / "interviews.csv").read_text())


if __name__ == "__main__":
    unittest.main()
