import shutil
import tempfile
import unittest
from datetime import date
from pathlib import Path

from productmarketing import cli, launches, messaging, research, reviews, voice

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "sample-data"
TODAY = date(2026, 11, 24)


def ctx_for(as_of=TODAY, data=DATA):
    c = messaging.analyze(data, as_of)
    c["statement_parts"] = messaging.statement_parts(c)
    return c


def copy_data(d):
    dst = Path(d) / "data"
    shutil.copytree(DATA, dst)
    return dst


class Research(unittest.TestCase):
    def test_gaps_are_found_from_the_evidence_and_ranked(self):
        g = research.gaps(ctx_for())
        titles = [x["title"] for x in g]
        self.assertIn("Persona: Finance leader", titles)
        self.assertFalse(any(t.startswith("Persona: Data leader") for t in titles))
        self.assertTrue(any(t.startswith("Proof: Find them") for t in titles))
        self.assertTrue(any(t.startswith("Proof: Works across") for t in titles))
        self.assertIn("Segment: Healthcare, 1000-10000", titles)
        self.assertEqual([x["priority"] for x in g], sorted(x["priority"] for x in g))

    def test_a_persona_with_no_interviews_ranks_first(self):
        with tempfile.TemporaryDirectory() as d:
            data = copy_data(d)
            rows = [r for r in (data / "customers" / "interviews.csv").read_text().splitlines() if ",CFO," not in r]
            (data / "customers" / "interviews.csv").write_text("\n".join(rows) + "\n")
            g = research.gaps(ctx_for(data=data))
            self.assertEqual((g[0]["kind"], g[0]["priority"], g[0]["title"]), ("persona", 1, "Persona: Finance leader"))

    def test_competitors_without_strengths_get_interview_questions(self):
        g = research.gaps(ctx_for())
        comp = [x["title"] for x in g if x["kind"] == "competitor"]
        self.assertIn("Competitor: Datavault Pro", comp)
        self.assertNotIn("Competitor: Clearline Data", comp)  # its strengths are already on file

    def test_guide_questions_are_numbered_neutral_and_never_state_findings(self):
        t = research.guide(ctx_for())
        self.assertIn("1. Tell me about your role", t)
        self.assertIn("2. Tell me about the last time you dealt with this", t)
        self.assertNotRegex(t, r"(?i)do you agree|wouldn't you|don't you")
        self.assertIn("get consent", t)
        self.assertIn("Reuse these pain labels", t)

    def test_enough_evidence_means_no_gaps(self):
        c = ctx_for(date(2026, 9, 15))
        for p in c["personas"]:
            p["interviews"] = 99
        c["pillars"] = [x for x in c["pillars"] if len(x["usable"]) >= 2 and len(x["hits"]) >= 3]
        c["no_proof"], c["lost_reasons"], c["lost_competitors"] = [], [], []
        c["segments"] = []
        self.assertIn("No gaps found", research.guide(c))

    def test_survey_has_eight_questions_with_options_from_the_data(self):
        t = research.survey(ctx_for())
        self.assertEqual(sum(1 for ln in t.splitlines() if ln.startswith("| ") and ln[2].isdigit()), 8)
        self.assertIn("reports do not match", t)
        self.assertIn("1000-10000", t)
        self.assertIn("two surveys a year", t)
        self.assertIn("[MISSING: who sends it", t)


class Reviews(unittest.TestCase):
    def test_status_for_higher_and_lower_is_better(self):
        self.assertEqual(reviews.status(100, 130, "higher")[0], "met")
        self.assertEqual(reviews.status(100, 60, "higher")[0], "partly met")
        self.assertEqual(reviews.status(100, 40, "higher")[0], "missed")
        self.assertEqual(reviews.status(40, 30, "lower")[0], "met")
        self.assertEqual(reviews.status(40, 52, "lower")[0], "partly met")
        self.assertEqual(reviews.status(40, 90, "lower")[0], "missed")
        self.assertEqual(reviews.status(None, 5, "higher")[0], "no result yet")

    def test_the_review_compares_goals_with_results_and_leaves_lessons_open(self):
        t = reviews.render(ctx_for(), launches.load(DATA), reviews.load(DATA), launches.load_decisions(DATA))
        self.assertIn("| Pipeline sourced (dollars) | 400000 | 520000 | 130% | met |", t)
        self.assertIn("| Support tickets about merges per month | 40 | 52 | 77% (lower is better) | partly met |", t)
        self.assertIn("Review date reached.", t)
        self.assertIn("not proof that the launch caused", t)
        self.assertIn("What worked: [MISSING", t)
        self.assertIn("Decision: [MISSING: continue, adjust or stop", t)

    def test_launches_without_a_decision_or_results_are_not_reviewed(self):
        t = reviews.render(ctx_for(), launches.load(DATA), reviews.load(DATA), launches.load_decisions(DATA))
        self.assertNotIn("(L1)", t)

    def test_an_early_review_is_marked_early(self):
        rows = [dict(launch_id="L1", name="X", target_date="2027-02-15", claims="d1")]
        res = [dict(launch_id="L1", goal_metric="m", goal_value="10", actual_value="5", direction="higher", measured_on="2026-11-01", source="s")]
        t = reviews.render(ctx_for(), rows, res, {})
        self.assertIn("Not due until 2027-08-14", t)
        self.assertIn("[needs product marketer decision]", t)

    def test_missing_results_are_flagged_not_filled(self):
        rows = [dict(launch_id="L1", name="X", target_date="2027-02-15", claims="d1")]
        res = [dict(launch_id="L1", goal_metric="m", goal_value="10", actual_value="", direction="", measured_on="", source="")]
        t = reviews.render(ctx_for(), rows, res, {})
        self.assertIn("[MISSING: result]", t)
        self.assertIn("no result yet", t)


class Voice(unittest.TestCase):
    def test_guide_describes_the_approved_copy_and_warns_about_a_thin_sample(self):
        t = voice.build(ctx_for(), voice.load_copy(DATA), voice.load_terms(DATA))
        self.assertIn("3 piece(s)", t)
        self.assertIn("thin sample", t)
        self.assertIn("Average sentence length", t)
        self.assertIn("The product marketer decides which of them are the voice", t)
        self.assertIn("[MISSING: two or three pairs written by a person", t)
        self.assertIn("| duplicate records | dupes |", t)

    def test_no_approved_copy_is_marked_missing_not_guessed(self):
        t = voice.build(ctx_for(), {}, [])
        self.assertIn("[MISSING] no approved copy found", t)
        self.assertNotIn("Average sentence length", t)

    def test_conflicts_between_approved_copy_and_the_avoid_list_are_shown(self):
        copy = {"a.md": "This is a seamless way to leverage your data. It is simple."}
        t = voice.build(ctx_for(), copy, [])
        self.assertIn("'seamless' in a.md", t)
        self.assertIn("'leverage' in a.md", t)

    def test_check_flags_avoid_words_terminology_and_drift(self):
        c, terms, copy = ctx_for(), voice.load_terms(DATA), voice.load_copy(DATA)
        res = voice.check("Our data cleansing tool is revolutionary! Users love dupes.", c, terms, copy)
        msgs = " | ".join(m for _, m in res)
        self.assertIn("'revolutionary' is on your avoid list", msgs)
        self.assertIn("use 'Data Quality Platform' instead of 'data cleansing tool'", msgs)
        self.assertIn("use 'duplicate records' instead of 'dupes'", msgs)
        self.assertIn("use 'customers' instead of 'users'", msgs)
        long = " ".join(["This sentence keeps going and going without any real stop because it just adds one more clause after another until the reader is lost completely."] * 3)
        self.assertTrue(any(l == "WARN" and "sentences average" in m for l, m in voice.check(long, c, terms, copy)))

    def test_clean_copy_in_the_same_voice_passes(self):
        text = "Your reports should match. Fernhill Data Quality Platform finds duplicate records and keeps watching. Setup takes under two weeks."
        self.assertEqual(voice.check(text, ctx_for(), voice.load_terms(DATA), voice.load_copy(DATA)), [])

    def test_the_voice_check_command_sets_the_exit_code(self):
        with tempfile.TemporaryDirectory() as d:
            ok, bad = Path(d) / "ok.md", Path(d) / "bad.md"
            ok.write_text("Your reports should match. We find duplicate records.")
            bad.write_text("A revolutionary tool.")
            self.assertEqual(cli.main(["voice-check", str(ok), "--data", str(DATA)]), 0)
            self.assertEqual(cli.main(["voice-check", str(bad), "--data", str(DATA)]), 1)


class Build(unittest.TestCase):
    def test_build_writes_the_new_documents_and_stays_deterministic(self):
        with tempfile.TemporaryDirectory() as a, tempfile.TemporaryDirectory() as b:
            cli.build(DATA, a, TODAY)
            cli.build(DATA, b, TODAY)
            for rel in ("research/interview-guide.md", "research/survey.md", "launch-reviews.md", "voice-guide.md"):
                self.assertTrue((Path(a) / rel).exists(), rel)
                self.assertEqual((Path(a) / rel).read_text(), (Path(b) / rel).read_text(), rel)

    def test_single_commands_write_only_their_own_output(self):
        for cmd, expect in (("research", {"research"}), ("reviews", {"launch-reviews.md"}), ("voice", {"voice-guide.md"})):
            with tempfile.TemporaryDirectory() as d:
                self.assertEqual(cli.main([cmd, "--data", str(DATA), "--out-dir", d, "--as-of", "2026-11-24"]), 0)
                self.assertEqual({p.relative_to(d).parts[0] for p in Path(d).rglob("*") if p.is_file()}, expect, cmd)

    def test_no_approved_copy_means_build_skips_the_voice_guide(self):
        with tempfile.TemporaryDirectory() as d:
            data = copy_data(d)
            shutil.rmtree(data / "company" / "approved-copy")
            cli.build(data, Path(d) / "out", TODAY)
            self.assertFalse((Path(d) / "out" / "voice-guide.md").exists())


if __name__ == "__main__":
    unittest.main()
