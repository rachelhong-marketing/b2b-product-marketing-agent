"""Command line: build, check, icp."""
import argparse
import json
import sys
from pathlib import Path

from . import check as checkmod, export, icp, messaging


def build(data, out_dir):
    ctx = messaging.analyze(data)
    ctx["statement_parts"] = messaging.statement_parts(ctx)
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    doc = out / "positioning-and-messaging.md"
    doc.write_text(messaging.render(ctx), encoding="utf-8")
    (out / "positioning.json").write_text(json.dumps(export.positioning(ctx), indent=2), encoding="utf-8")
    (out / "brand-profile.json").write_text(json.dumps(export.brand_profile(ctx), indent=2), encoding="utf-8")
    return ctx, doc


def main(argv=None):
    ap = argparse.ArgumentParser(prog="productmarketing", description="Ideal customer profile, positioning and messaging from your own deal, interview and competitor data.")
    sub = ap.add_subparsers(dest="cmd", required=True)
    b = sub.add_parser("build", help="build the positioning document and the hand-off files")
    b.add_argument("--data", required=True)
    b.add_argument("--out-dir", default="output")
    c = sub.add_parser("check", help="check a positioning document")
    c.add_argument("doc")
    c.add_argument("--profile", required=True, help="the product profile JSON")
    i = sub.add_parser("icp", help="show the ideal customer profile table only")
    i.add_argument("--data", required=True)
    a = ap.parse_args(argv)
    if a.cmd == "build":
        ctx, doc = build(a.data, a.out_dir)
        print(f"Wrote {doc}, positioning.json and brand-profile.json in {a.out_dir}")
    elif a.cmd == "check":
        res = checkmod.check_doc(Path(a.doc).read_text(encoding="utf-8"), messaging.load_profile(a.profile))
        print(checkmod.format_results(res))
        return 1 if any(l == "FAIL" for l, _ in res) else 0
    else:
        print("\n".join(icp.table_lines(icp.segments(messaging.load(a.data)["deals"]))))
    return 0
