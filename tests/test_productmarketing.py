import json
import shutil
import sys
import tempfile
import unittest
from datetime import date
from pathlib import Path

from productmarketing import accounts, check, cli, decisions, export, icp, messaging, personas, proofs, sales
from productmarketing.util import read_csv_rows

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "sample-data"
AS_OF = date(2026, 9, 15)  # all sample proof points are usable on this date


def deal(i, ind, size, outcome, acv="", days="40", kept="", role="VP of Data", reason="", comp=""):
    return dict(deal_id=f"D{i}", industry=ind, company_size=size, buyer_role=role, outcome=outcome, acv=acv, days_to_close=days,
                use_case="duplicate cleanup", retained_12m=kept, lost_reason=reason, competitor=comp)


def copy_data(d):
    dst = Path(d) / "data"
    shutil.copytree(DATA, dst)
    return dst


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
                 deal(3, "A", "s", "won", role="RevOps manager"), deal(4, "A", "s", "lost", reason="no budget", comp="Clearline Data")]
        self.assertEqual(icp.personas(deals)[0], ("CRM administrator", 2))
        self.assertEqual(icp.lost_reasons(deals), [("no budget", 1)])
        self.assertEqual(icp.lost_competitors(deals), [("Clearline Data", 1)])


class Accounts(unittest.TestCase):
    def test_common_values_need_a_big_enough_list_and_a_big_enough_share(self):
        accts = accounts.load(DATA)
        common = {(f, v) for f, v, _, _ in accounts.common(accts)}
        self.assertIn(("industry", "Retail"), common)
        self.assertNotIn(("industry", "Healthcare"), common)
        self.assertEqual(accounts.common(accts[:5]), [])

    def test_list_compared_with_wins(self):
        segs = icp.segments(messaging.load(DATA)["deals"])
        no_wins, off_list = accounts.compare_with_wins(segs, accounts.load(DATA))
        self.assertEqual([x["segment"] for x in no_wins], ["Insurance, 1000-10000"])
        self.assertEqual([x["segment"] for x in off_list], ["Healthcare, 1000-10000"])

    def test_the_document_warns_that_a_list_is_not_proof_of_fit(self):
        ctx = messaging.analyze(DATA, AS_OF)
        self.assertIn("not proof of buyer fit", "\n".join(messaging.icp_lines(ctx)))

    def test_no_list_is_marked_missing_not_guessed(self):
        with tempfile.TemporaryDirectory() as d:
            data = copy_data(d)
            (data / "accounts" / "target-accounts.csv").unlink()
            text = "\n".join(messaging.icp_lines(messaging.analyze(data, AS_OF)))
            self.assertIn("[MISSING] no target account list provided", text)


class Sales(unittest.TestCase):
    def test_notes_are_counted_by_segment_and_unknown_deals_ignored(self):
        deals = [deal(1, "Retail", "big", "won"), deal(2, "Retail", "big", "lost")]
        notes = [dict(deal_id="D1", rep_id="R1", note_type="why-won", note="a", date=""), dict(deal_id="D2", rep_id="R2", note_type="objection", note="b", date=""),
                 dict(deal_id="D404", rep_id="R3", note_type="other", note="c", date="")]
        out = sales.by_segment(notes, deals)
        self.assertEqual(out[("Retail", "big")]["n"], 2)
        self.assertEqual(len(out[("Retail", "big")]["reps"]), 2)
        self.assertEqual(len(out), 1)


class Decisions(unittest.TestCase):
    def test_status_draft_until_a_segment_is_confirmed(self):
        self.assertEqual(decisions.status({}), "DRAFT")
        self.assertEqual(decisions.status({"a": {"decision": "rejected"}}), "DRAFT")
        self.assertEqual(decisions.status(decisions.load(DATA)), "CONFIRMED")

    def test_only_a_named_person_with_a_valid_decision_is_recorded(self):
        with tempfile.TemporaryDirectory() as d:
            with self.assertRaises(ValueError):
                decisions.add(d, "Retail, 1000-10000", "maybe", "Someone")
            with self.assertRaises(ValueError):
                decisions.add(d, "Retail, 1000-10000", "confirmed", "  ")
            self.assertFalse(decisions.path(d).exists())
            decisions.add(d, "Retail, 1000-10000", "confirmed", "Sam", "core", on="2026-11-01")
            self.assertEqual(decisions.load(d)["retail, 1000-10000"]["decided_by"], "Sam")

    def test_the_latest_decision_wins(self):
        with tempfile.TemporaryDirectory() as d:
            decisions.add(d, "X, big", "confirmed", "Sam", on="2026-11-01")
            decisions.add(d, "X, big", "rejected", "Sam", "changed my mind", on="2026-11-05")
            self.assertEqual(decisions.load(d)["x, big"]["decision"], "rejected")
            self.assertEqual(decisions.status(decisions.load(d)), "DRAFT")

    def test_cli_decide_refuses_an_empty_name(self):
        with tempfile.TemporaryDirectory() as d:
            self.assertEqual(cli.main(["decide", "--data", d, "--segment", "A, b", "--decision", "confirmed", "--by", " "]), 1)
            self.assertEqual(cli.main(["decide", "--data", d, "--segment", "A, b", "--decision", "confirmed", "--by", "Sam"]), 0)

    def test_without_decisions_the_document_says_draft_and_the_statement_slot_is_open(self):
        with tempfile.TemporaryDirectory() as d:
            data = copy_data(d)
            decisions.path(data).unlink()
            ctx, doc = cli.build(data, Path(d) / "out", AS_OF)
            text = doc.read_text()
            self.assertIn("ICP status: DRAFT", text)
            self.assertIn("not confirmed by the product marketer", text)
            res = check.check_doc(text, messaging.load_profile(data / "company" / "product-profile.json"))
            self.assertTrue(any(l == "FAIL" and "still a draft" in m for l, m in res))
            self.assertEqual(json.loads((Path(d) / "out" / "positioning.json").read_text())["icp_status"], "DRAFT")


class Proofs(unittest.TestCase):
    def test_statuses(self):
        t = date(2026, 11, 24)
        ok = dict(id="a", source="s", approved_by="x", approved_on="2026-01-01", expires_on="2027-06-01")
        self.assertEqual(proofs.status(ok, t)[0], "valid")
        self.assertIn("valid until", proofs.status(ok, t)[1])
        self.assertIn("expires soon", proofs.status(dict(ok, expires_on="2026-12-31"), t)[1])
        self.assertEqual(proofs.status(dict(ok, expires_on="2026-09-30"), t), ("unusable", "expired 2026-09-30"))
        self.assertEqual(proofs.status(dict(ok, source=""), t), ("unusable", "no source"))
        self.assertEqual(proofs.status(dict(ok, approved_by=""), t), ("unusable", "not approved"))
        self.assertEqual(proofs.status(dict(ok, approved_on=""), t), ("unusable", "not approved"))
        self.assertEqual(proofs.status(dict(ok, expires_on=""), t)[0], "valid")
        self.assertEqual(proofs.status(dict(ok, expires_on="next year"), t)[0], "unusable")

    def test_a_pillar_needs_two_usable_proof_points_and_expiry_matters(self):
        early = messaging.analyze(DATA, AS_OF)
        late = messaging.analyze(DATA, date(2026, 11, 24))
        find_early = next(x for x in early["ranked"] if x["d"]["id"] == "d3")
        find_late = next(x for x in late["ranked"] if x["d"]["id"] == "d3")
        self.assertEqual(len(find_early["usable"]), 2)
        self.assertEqual(find_late["usable"], ["p5"])
        self.assertEqual(find_late["unusable"], [("p6", "expired 2026-09-30")])
        text = messaging.render(dict(late, statement_parts=messaging.statement_parts(late)))
        self.assertIn("Not usable (expired 2026-09-30)", text)
        self.assertIn("only 1 usable proof point", text)

    def test_unknown_proof_id_is_reported_not_trusted(self):
        with tempfile.TemporaryDirectory() as d:
            data = copy_data(d)
            prof = json.loads((data / "company" / "product-profile.json").read_text())
            prof["differentiators"][4]["proof"] = ["p99"]
            (data / "company" / "product-profile.json").write_text(json.dumps(prof))
            ctx = messaging.analyze(data, AS_OF)
            x = next(x for x in ctx["ranked"] if x["d"]["id"] == "d5")
            self.assertEqual(x["usable"], [])
            self.assertEqual(x["unusable"], [("p99", "not in the proof-point register")])

    def test_old_style_inline_proof_is_rejected_with_a_clear_message(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "p.json"
            p.write_text(json.dumps(dict(brand="b", product="p", domain="d", category="c", avoid_words=[], differentiators=[dict(id="d1", claim="c", proof=[dict(text="x")])])))
            with self.assertRaises(ValueError):
                messaging.load_profile(p)


class Personas(unittest.TestCase):
    def test_guides_come_from_interviews_and_lead_with_pillars_that_answer_the_pains(self):
        ctx = messaging.analyze(DATA, AS_OF)
        by = {p["name"]: p for p in ctx["personas"]}
        self.assertEqual(set(by), {"Data leader", "Analytics leader", "Finance leader"})
        self.assertEqual(by["Analytics leader"]["pains"][0][0], "reports do not match")
        self.assertTrue(by["Analytics leader"]["lead"][0][1]["d"]["claim"].startswith("Find them"))
        self.assertTrue(set(by["Data leader"]["proof_ids"]) <= {"p1", "p2", "p4", "p5", "p6"})

    def test_a_persona_with_no_interviews_is_flagged_not_filled_in(self):
        prof = dict(personas=[dict(name="Ghost", titles=["Chief Ghost"])])
        out = personas.build(prof, [], [], [], [], {})
        text = "\n".join(personas.lines(out))
        self.assertIn("[MISSING] none with this persona", text)
        self.assertIn("[MISSING] no pillar answers this persona's pains yet", text)

    def test_shared_claims_are_never_in_lead_with(self):
        ctx = messaging.analyze(DATA, AS_OF)
        shared = {x["d"]["claim"] for x in ctx["ranked"] if len(x["overlap"]) >= 2}
        for p in ctx["personas"]:
            self.assertFalse(shared & {x["d"]["claim"] for _, x in p["lead"]})

    def test_without_persona_groups_the_top_buyer_titles_are_used(self):
        deals = [deal(i, "A", "s", "won", role="VP of Data") for i in range(3)] + [deal(9, "A", "s", "won", role="BI Director")]
        self.assertEqual([g["name"] for g in personas.groups({}, deals)], ["VP of Data", "BI Director"])


class Messaging(unittest.TestCase):
    def ctx(self, as_of=AS_OF):
        c = messaging.analyze(DATA, as_of)
        c["statement_parts"] = messaging.statement_parts(c)
        return c

    def test_claim_without_proof_cannot_be_a_pillar(self):
        c = self.ctx()
        nop = "Works across customer relationship management (CRM), billing and support systems"
        claims = [x["d"]["claim"] for x in c["pillars"]]
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

    def test_statement_uses_the_confirmed_segment(self):
        who = dict(self.ctx()["statement_parts"])["For"]
        self.assertIn("financial services companies with 1000-10000 employees", who)

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
            ctx, doc = cli.build(d, Path(d) / "out", AS_OF)
            text = doc.read_text()
            self.assertIn("[MISSING] none provided", text)
            self.assertIn("ICP status: DRAFT", text)


class Export(unittest.TestCase):
    def test_brand_profile_has_what_the_content_assistant_needs(self):
        with tempfile.TemporaryDirectory() as d:
            ctx, _ = cli.build(DATA, d, AS_OF)
            b = json.loads((Path(d) / "brand-profile.json").read_text())
        for k in ("brand", "domain", "audiences", "themes", "avoid_words", "competitors"):
            self.assertIn(k, b)
        for name, t in b["themes"].items():
            self.assertTrue(t["triggers"], name)
            self.assertTrue(0 <= t["fit"] <= 1)
        self.assertEqual(max(t["fit"] for t in b["themes"].values()), 1.0)
        self.assertIn("Data leader (VP of Data, Head of Data Engineering)", b["audiences"])

    def test_draft_icp_is_stated_in_the_exported_profile(self):
        with tempfile.TemporaryDirectory() as d:
            data = copy_data(d)
            decisions.path(data).unlink()
            cli.build(data, Path(d) / "out", AS_OF)
            b = json.loads((Path(d) / "out" / "brand-profile.json").read_text())
        self.assertIn("still a DRAFT", b["note"])

    def test_brand_profile_loads_in_the_content_strategy_assistant_if_present(self):
        other = ROOT.parent / "b2b-content-strategy-assistant"
        if not other.exists():
            self.skipTest("content strategy assistant repo not next to this one")
        sys.path.insert(0, str(other))
        try:
            from contentstrategy import brand
            with tempfile.TemporaryDirectory() as d:
                cli.build(DATA, d, AS_OF)
                b = brand.load(Path(d) / "brand-profile.json")
            self.assertTrue(b["themes"])
        finally:
            sys.path.remove(str(other))

    def test_positioning_json_contents(self):
        with tempfile.TemporaryDirectory() as d:
            cli.build(DATA, d, AS_OF)
            p = json.loads((Path(d) / "positioning.json").read_text())
        self.assertEqual(p["icp_status"], "CONFIRMED")
        self.assertEqual({x["segment"] for x in p["icp_confirmed"]}, {"Retail, 1000-10000", "Financial services, 1000-10000"})
        self.assertTrue(all(len(x["usable_proof"]) >= 1 for x in p["pillars"]))
        self.assertEqual(p["statement_parts"][0]["label"], "For")
        self.assertIn(dict(id="p7", usable=False, status="not approved"), p["proof_register"])
        self.assertEqual(p["icp_hypotheses"][0]["decision"], "confirmed")


class Check(unittest.TestCase):
    PROFILE = messaging.load_profile(DATA / "company" / "product-profile.json")

    def built(self, as_of=AS_OF):
        with tempfile.TemporaryDirectory() as d:
            _, doc = cli.build(DATA, d, as_of)
            return doc.read_text()

    def test_fresh_build_fails_until_slots_are_filled(self):
        res = check.check_doc(self.built(), self.PROFILE)
        self.assertTrue(any("[MISSING] slots" in m for _, m in res))

    def test_pillar_with_one_usable_proof_fails(self):
        res = check.check_doc(self.built(date(2026, 11, 24)), self.PROFILE)
        self.assertTrue(any("proof point(s)" in m for _, m in res))

    def test_finished_doc_has_no_failures(self):
        t = self.built()
        claim = "Keep them out: monitoring so duplicate records don't come back"
        t = t.replace(f"[MISSING: write it. Strongest pillar: {claim}]", "Duplicate records stay out because the platform keeps watching.")
        t = t.replace(f"[MISSING: write it. Claim nobody tracked makes: {claim}]", "It keeps monitoring data quality after setup.")
        t = t.replace("[MISSING: one sentence for this persona, written by a person from the evidence above]", "Written by the product marketer.")
        t = t.replace("Response: [MISSING: from sales and win-loss calls]", "Response: covered in the sales playbook")
        self.assertNotIn("[MISSING", t)
        res = check.check_doc(t, self.PROFILE)
        self.assertEqual([m for l, m in res if l == "FAIL"], [])
        self.assertTrue(any("still need a product marketer decision" in m for l, m in res))

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
        for f in ("company/product-profile.json", "customers/interviews.csv", "customers/sales-input.csv"):
            self.assertIn("Made-up", (DATA / f).read_text(), f)

    def test_account_list_has_ids_not_names(self):
        for r in read_csv_rows(DATA / "accounts" / "target-accounts.csv"):
            self.assertRegex(r["account_id"], r"^A\d{3}$")


if __name__ == "__main__":
    unittest.main()
