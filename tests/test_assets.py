import shutil
import tempfile
import unittest
from datetime import date
from pathlib import Path

from productmarketing import battlecards, check, cli, decisions, fieldguides, launches, messaging, onesheets, personas, playbook, proofs

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "sample-data"
TODAY = date(2026, 11, 24)      # p6 is expired, p1 to p3 expire soon
EARLY = date(2026, 9, 15)       # every sample proof point is usable


def ctx_for(as_of=TODAY, data=DATA):
    c = messaging.analyze(data, as_of)
    c["statement_parts"] = messaging.statement_parts(c)
    return c


class Battlecards(unittest.TestCase):
    def test_record_against_the_competitor_matches_the_deals(self):
        c = ctx_for()
        lost = [d for d in c["deals"] if d["outcome"] == "lost"]
        n = sum(1 for d in lost if d["competitor"] == "Clearline Data")
        text = battlecards.build(c, next(x for x in c["competitors"] if x["name"] == "Clearline Data"))
        self.assertIn(f"Lost deals naming them: {n} of {len(lost)} lost deals", text)

    def test_shared_claims_are_not_listed_as_differences(self):
        c = ctx_for()
        text = battlecards.build(c, next(x for x in c["competitors"] if x["name"] == "Clearline Data"))
        diff = text.split("## Where we differ")[1].split("## Claims both of us make")[0]
        self.assertNotIn("Set up in under two weeks", diff)
        self.assertIn("Set up in under two weeks", text.split("## Claims both of us make")[1])

    def test_only_usable_proof_is_offered(self):
        text = battlecards.build(ctx_for(), ctx_for()["competitors"][0])
        self.assertNotIn("[p6]", text)
        self.assertIn("[p5]", text)

    def test_strengths_and_handling_are_never_invented(self):
        c = ctx_for()
        with_s = battlecards.build(c, next(x for x in c["competitors"] if x["name"] == "Clearline Data"))
        without = battlecards.build(c, next(x for x in c["competitors"] if x["name"] == "Purestream"))
        self.assertIn("quick to start", with_s)
        self.assertIn("[MISSING: what buyers say they do well", without)
        for t in (with_s, without):
            self.assertIn("[MISSING: how to position when they come up", t)
            self.assertIn("Internal use only", t)

    def test_one_page_per_tracked_competitor(self):
        self.assertEqual(set(battlecards.build_all(ctx_for())), {"clearline-data", "datavault-pro", "purestream"})


class FieldGuides(unittest.TestCase):
    def test_guide_has_the_evidence_and_leaves_the_words_open(self):
        c = ctx_for()
        p = next(x for x in c["personas"] if x["name"] == "Analytics leader")
        t = fieldguides.build(c, p)
        for h in ("## Who they are", "## What hurts", "## What to lead with", "## Proof you can use", "## Objections you will hear", "## What to say"):
            self.assertIn(h, t)
        self.assertIn("reports do not match", t)
        self.assertIn("[MISSING: one sentence for this persona", t)
        self.assertNotIn("[p6]", t)

    def test_a_persona_with_no_evidence_is_flagged(self):
        c = ctx_for()
        ghost = personas.build(dict(personas=[dict(name="Ghost", titles=["Chief Ghost"])]), [], [], [], [], {})[0]
        t = fieldguides.build(c, ghost)
        self.assertIn("[MISSING] no interviews with this persona yet", t)
        self.assertIn("[MISSING] no pillar answers this persona's pains yet", t)


class OneSheets(unittest.TestCase):
    def sheet(self, as_of=TODAY):
        c = ctx_for(as_of)
        return c, onesheets.build(c, next(x for x in c["personas"] if x["name"] == "Data leader"))

    def test_the_external_body_carries_no_internal_research(self):
        _, t = self.sheet()
        body = t.split(onesheets.NOTES)[0]
        self.assertNotRegex(body, r"(?i)interview|win/loss|lost deal")
        self.assertIn("Buyers describe the problem", t.split(onesheets.NOTES)[1])

    def test_only_usable_proof_appears(self):
        c, t = self.sheet()
        for pid in __import__("re").findall(r"\[(p\d+)\]", t):
            self.assertEqual(c["proofs"][pid]["state"], "valid")

    def test_expiring_proof_is_called_out_for_the_writer(self):
        _, t = self.sheet()
        self.assertIn("expiring within 60 days", t)

    def test_asset_check_blocks_unfinished_unusable_and_internal(self):
        c, t = self.sheet()
        prof = messaging.load_profile(DATA / "company" / "product-profile.json")
        res = check.check_asset(t, prof, c["proofs"])
        self.assertTrue(any("[MISSING] slots" in m for _, m in res))
        done = (t.replace("[MISSING: headline, written by a person]", "One record per customer.")
                 .replace("[MISSING: one or two sentences in the buyer's own words]", "Your reports disagree.")
                 .replace("[MISSING: an approved customer quote]", "Quote approved by the customer.")
                 .replace("[MISSING: call to action]", "Book a demo."))
        self.assertEqual([m for l, m in check.check_asset(done, prof, c["proofs"]) if l == "FAIL"], [])
        self.assertTrue(any("p6" in m and "expired" in m for _, m in check.check_asset(done + "\n- extra [p6]\n", prof, c["proofs"])))
        self.assertTrue(any("not in the register" in m for _, m in check.check_asset(done + "\n- extra [p99]\n", prof, c["proofs"])))
        bad = done.replace("One record per customer.", "Our interviews show one record per customer.")
        self.assertTrue(any("internal research" in m for _, m in check.check_asset(bad, prof, c["proofs"])))
        bad = done.replace("One record per customer.", "A revolutionary single record.")
        self.assertTrue(any("revolutionary" in m for _, m in check.check_asset(bad, prof, c["proofs"])))


class Launches(unittest.TestCase):
    def rows(self):
        return {r["launch_id"]: r for r in launches.load(DATA)}

    def test_scoring_and_suggested_path(self):
        r = self.rows()
        self.assertEqual(launches.score(r["L1"])["path"], "market launch")
        self.assertEqual(launches.score(r["L1"])["total"], 13)
        self.assertEqual(launches.score(r["L3"])["path"], "no launch")
        l4 = launches.score(r["L4"])
        self.assertEqual((l4["path"], l4["answered"], len(l4["missing"])), ("sales launch", 5, 2))

    def test_too_few_answers_is_undetermined_not_guessed(self):
        s = launches.score(dict(customers_impacted="many", customer_ask="large"))
        self.assertEqual(s["path"], "undetermined")

    def test_high_points_without_revenue_impact_is_not_a_market_launch(self):
        row = dict(customers_impacted="many", customer_ask="large", value_to_prospects="high", differentiation="high", revenue_impact="low", usage_impact="high", roadmap_fit="yes")
        self.assertEqual(launches.score(row)["path"], "sales launch")

    def test_review_date_is_180_days_after_the_target(self):
        self.assertEqual(launches.review_date(dict(target_date="2027-02-15")), "2027-08-14")
        self.assertIn("[MISSING", launches.review_date(dict(target_date="soon")))

    def test_plan_checks_proof_on_the_linked_claims(self):
        c = ctx_for(TODAY)
        t = launches.render(c, launches.load(DATA), {})
        self.assertIn('needs 2. Not usable: p6 (expired 2026-09-30)', t)
        early = launches.render(ctx_for(EARLY), launches.load(DATA), {})
        self.assertNotIn("needs 2", early.split("## Made-up: review queue")[0])

    def test_decisions_need_a_name_and_a_valid_choice(self):
        with tempfile.TemporaryDirectory() as d:
            with self.assertRaises(ValueError):
                launches.add_decision(d, "L1", "maybe", "Sam")
            with self.assertRaises(ValueError):
                launches.add_decision(d, "L1", "market", " ")
            launches.add_decision(d, "L1", "sales", "Sam", "start small", on="2026-11-25")
            t = launches.render(ctx_for(), launches.load(DATA), launches.load_decisions(d))
            self.assertIn("Decision: sales (Sam, 2026-11-25)", t)
            self.assertIn("Decision: [needs product marketer decision]", t)

    def test_the_cli_refuses_an_unnamed_launch_decision(self):
        with tempfile.TemporaryDirectory() as d:
            self.assertEqual(cli.main(["decide-launch", "--data", d, "--launch", "L1", "--decision", "market", "--by", " "]), 1)
            self.assertEqual(cli.main(["decide-launch", "--data", d, "--launch", "L1", "--decision", "market", "--by", "Sam"]), 0)


class Playbook(unittest.TestCase):
    def test_lists_confirmed_segments_and_points_to_the_other_documents(self):
        t = playbook.build(ctx_for())
        self.assertIn("Retail, 1000-10000 (confirmed by", t)
        self.assertIn("battlecards/clearline-data.md", t)
        self.assertIn("field-guides/data-leader.md", t)
        self.assertIn("Response: [MISSING", t)
        self.assertIn("not proof of fit", t)

    def test_draft_icp_is_stated_not_hidden(self):
        with tempfile.TemporaryDirectory() as d:
            data = Path(d) / "data"
            shutil.copytree(DATA, data)
            decisions.path(data).unlink()
            self.assertIn("[MISSING] the ideal customer profile is not confirmed", playbook.build(ctx_for(data=data)))


class Build(unittest.TestCase):
    def test_build_writes_every_asset_and_is_deterministic(self):
        with tempfile.TemporaryDirectory() as a, tempfile.TemporaryDirectory() as b:
            cli.build(DATA, a, TODAY)
            cli.build(DATA, b, TODAY)
            fa = sorted(p.relative_to(a).as_posix() for p in Path(a).rglob("*") if p.is_file())
            self.assertEqual(fa, sorted(p.relative_to(b).as_posix() for p in Path(b).rglob("*") if p.is_file()))
            for need in ("battlecards/clearline-data.md", "field-guides/data-leader.md", "one-sheets/finance-leader.md", "playbook-outline.md", "launch-triage.md",
                         "positioning-and-messaging.md", "positioning.json", "brand-profile.json"):
                self.assertIn(need, fa)
            for rel in fa:
                self.assertEqual((Path(a) / rel).read_text(), (Path(b) / rel).read_text(), rel)

    def test_single_asset_commands_write_only_that_asset(self):
        for cmd, folder_or_file in (("battlecards", "battlecards"), ("fieldguides", "field-guides"), ("onesheets", "one-sheets"), ("playbook", "playbook-outline.md"), ("launches", "launch-triage.md")):
            with tempfile.TemporaryDirectory() as d:
                self.assertEqual(cli.main([cmd, "--data", str(DATA), "--out-dir", d, "--as-of", "2026-11-24"]), 0)
                top = {p.relative_to(d).parts[0] for p in Path(d).rglob("*") if p.is_file()}
                self.assertEqual(top, {folder_or_file}, cmd)

    def test_check_asset_cli_exit_codes(self):
        with tempfile.TemporaryDirectory() as d:
            cli.build(DATA, d, TODAY)
            self.assertEqual(cli.main(["check-asset", str(Path(d) / "one-sheets" / "data-leader.md"), "--data", str(DATA), "--as-of", "2026-11-24"]), 1)


if __name__ == "__main__":
    unittest.main()
