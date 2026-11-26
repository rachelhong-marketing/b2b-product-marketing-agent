"""Command line: build, check, icp, proofs, decide."""
import argparse
import json
import sys
from datetime import date
from pathlib import Path

from . import battlecards, check as checkmod, decisions as decmod, export, fieldguides, launches, messaging, onesheets, playbook, proofs as proofmod
from .util import slug


def write_assets(ctx, out, data, only=None):
    """Battlecards, field guides, one-sheet drafts, the playbook outline and launch triage. `only` limits it to some kinds. Returns the files written."""
    out = Path(out)
    written = []

    def put(rel, text):
        f = out / rel
        f.parent.mkdir(parents=True, exist_ok=True)
        f.write_text(text, encoding="utf-8")
        written.append(rel)
    want = lambda k: only is None or k in only
    if want("battlecards"):
        for name, text in battlecards.build_all(ctx).items():
            put(f"battlecards/{name}.md", text)
    for pr in ctx["personas"]:
        if want("fieldguides"):
            put(f"field-guides/{slug(pr['name'])}.md", fieldguides.build(ctx, pr))
        if want("onesheets"):
            put(f"one-sheets/{slug(pr['name'])}.md", onesheets.build(ctx, pr))
    if want("playbook"):
        put("playbook-outline.md", playbook.build(ctx))
    rows = launches.load(data)
    if rows and want("launches"):
        put("launch-triage.md", launches.render(ctx, rows, launches.load_decisions(data)))
    return written


def build(data, out_dir, as_of=None):
    ctx = messaging.analyze(data, as_of)
    ctx["statement_parts"] = messaging.statement_parts(ctx)
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    ctx["assets_written"] = write_assets(ctx, out, data)
    doc = out / "positioning-and-messaging.md"
    doc.write_text(messaging.render(ctx), encoding="utf-8")
    (out / "positioning.json").write_text(json.dumps(export.positioning(ctx), indent=2), encoding="utf-8")
    (out / "brand-profile.json").write_text(json.dumps(export.brand_profile(ctx), indent=2), encoding="utf-8")
    return ctx, doc


def _date(s):
    return date.fromisoformat(s) if s else None


def main(argv=None):
    ap = argparse.ArgumentParser(prog="productmarketing", description="Ideal customer profile hypotheses, positioning and messaging drafts for a product marketer to review and decide.")
    sub = ap.add_subparsers(dest="cmd", required=True)
    b = sub.add_parser("build", help="build the positioning document and the hand-off files")
    b.add_argument("--data", required=True)
    b.add_argument("--out-dir", default="output")
    b.add_argument("--as-of", help="YYYY-MM-DD, for proof-point expiry (default: today)")
    c = sub.add_parser("check", help="check a positioning document")
    c.add_argument("doc")
    c.add_argument("--profile", required=True, help="the product profile JSON")
    i = sub.add_parser("icp", help="show the ideal customer profile hypotheses only")
    i.add_argument("--data", required=True)
    i.add_argument("--as-of")
    pr = sub.add_parser("proofs", help="show the proof-point register and what is usable")
    pr.add_argument("--data", required=True)
    pr.add_argument("--as-of")
    for nm, hlp in (("battlecards", "one internal page per competitor"), ("fieldguides", "one page per buyer persona"), ("onesheets", "one-sheet drafts per persona"),
                    ("playbook", "sales playbook outline"), ("launches", "launch triage and plan skeletons")):
        x = sub.add_parser(nm, help=hlp)
        x.add_argument("--data", required=True)
        x.add_argument("--out-dir", default="output")
        x.add_argument("--as-of")
    ca = sub.add_parser("check-asset", help="check a battlecard, field guide, one-sheet or playbook")
    ca.add_argument("file")
    ca.add_argument("--data", required=True)
    ca.add_argument("--as-of")
    dl = sub.add_parser("decide-launch", help="record a product marketer decision on a launch (only when a named person decides)")
    dl.add_argument("--data", required=True)
    dl.add_argument("--launch", required=True)
    dl.add_argument("--decision", required=True, choices=launches.VALID)
    dl.add_argument("--by", required=True)
    dl.add_argument("--note", default="")
    d = sub.add_parser("decide", help="record a product marketer decision on a segment (only when a named person decides)")
    d.add_argument("--data", required=True)
    d.add_argument("--segment", required=True, help='for example "Retail, 1000-10000"')
    d.add_argument("--decision", required=True, choices=decmod.VALID)
    d.add_argument("--by", required=True, help="the name of the person who decided")
    d.add_argument("--note", default="")
    a = ap.parse_args(argv)
    if a.cmd == "build":
        ctx, doc = build(a.data, a.out_dir, _date(a.as_of))
        print(f"Wrote {doc}, positioning.json and brand-profile.json in {a.out_dir}. ICP status: {ctx['icp_status']}.")
    elif a.cmd == "check":
        res = checkmod.check_doc(Path(a.doc).read_text(encoding="utf-8"), messaging.load_profile(a.profile))
        print(checkmod.format_results(res))
        return 1 if any(l == "FAIL" for l, _ in res) else 0
    elif a.cmd in ("battlecards", "fieldguides", "onesheets", "playbook", "launches"):
        ctx = messaging.analyze(a.data, _date(a.as_of))
        ctx["statement_parts"] = messaging.statement_parts(ctx)
        for rel in write_assets(ctx, a.out_dir, a.data, only={a.cmd}):
            print(f"Wrote {Path(a.out_dir) / rel}")
    elif a.cmd == "check-asset":
        data = Path(a.data)
        prof = messaging.load_profile(data / "company" / "product-profile.json")
        idx = proofmod.index(proofmod.load(data), _date(a.as_of) or date.today())
        res = checkmod.check_asset(Path(a.file).read_text(encoding="utf-8"), prof, idx)
        print(checkmod.format_results(res))
        return 1 if any(l == "FAIL" for l, _ in res) else 0
    elif a.cmd == "decide-launch":
        try:
            launches.add_decision(a.data, a.launch, a.decision, a.by, a.note)
        except ValueError as e:
            print(f"Not recorded: {e}")
            return 1
        print(f"Recorded: launch {a.launch} {a.decision} by {a.by}.")
    elif a.cmd == "icp":
        ctx = messaging.analyze(a.data, _date(a.as_of))
        print("\n".join(messaging.icp_lines(ctx)))
    elif a.cmd == "proofs":
        ctx = messaging.analyze(a.data, _date(a.as_of))
        print("\n".join(proofmod.register_lines(ctx["proofs"], ctx["used_by"])))
    else:
        try:
            decmod.add(a.data, a.segment, a.decision, a.by, a.note)
        except ValueError as e:
            print(f"Not recorded: {e}")
            return 1
        print(f"Recorded: {a.segment} {a.decision} by {a.by}.")
    return 0
