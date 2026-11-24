"""Command line: build, check, icp, proofs, decide."""
import argparse
import json
import sys
from datetime import date
from pathlib import Path

from . import check as checkmod, decisions as decmod, export, messaging, proofs as proofmod


def build(data, out_dir, as_of=None):
    ctx = messaging.analyze(data, as_of)
    ctx["statement_parts"] = messaging.statement_parts(ctx)
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
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
