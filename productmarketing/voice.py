"""Brand voice guide: what your approved copy actually does, so a person can write the rules.

Input: <data>/company/approved-copy/*.md or *.txt (copy already approved for use), the voice note and avoid list in the product profile,
and optionally <data>/company/terminology.csv with columns use, dont_use, note.
The guide describes patterns. It does not make rules. The product marketer decides which patterns are the voice."""
import re
from collections import Counter
from pathlib import Path

from .util import has_phrase, read_csv_rows

STOP = set("a an and are as at be but by for from has have i in is it its of on or our so that the their them they this to was we what when which will with you your can do does not no if then than".split())
MIN_WORDS = 1000
HYPE = ["seamless", "revolutionary", "game-changer", "best-in-class", "world-class", "cutting-edge", "synergy", "leverage", "unleash", "next-generation"]


def load_copy(data):
    d = Path(data) / "company" / "approved-copy"
    out = {}
    for f in sorted(d.glob("*")) if d.exists() else []:
        if f.suffix.lower() in (".md", ".txt"):
            out[f.name] = f.read_text(encoding="utf-8")
    return out


def load_terms(data):
    p = Path(data) / "company" / "terminology.csv"
    return read_csv_rows(p) if p.exists() else []


def clean(text):
    t = re.sub(r"(?m)^#+\s.*$", "", text)
    t = re.sub(r"\[([^\]]*)\]\([^)]*\)", r"\1", t)
    return re.sub(r"[*_`>]", "", t)


def sentences(text):
    return [s.strip() for s in re.split(r"(?<=[.!?])\s+|\n+", clean(text)) if len(re.findall(r"[A-Za-z']+", s)) >= 3]


def words(text):
    return re.findall(r"[A-Za-z][A-Za-z'-]*", clean(text))


def stats(copy):
    allt = "\n".join(copy.values())
    ss, ws = sentences(allt), words(allt)
    low = [w.lower() for w in ws]
    n = len(ws)
    lens = [len(re.findall(r"[A-Za-z']+", s)) for s in ss]
    c = Counter(w for w in low if w not in STOP and len(w) > 3)
    return dict(files=len(copy), words=n, sentences=len(ss), avg_len=(sum(lens) / len(lens)) if lens else 0, long_share=(sum(1 for x in lens if x > 25) / len(lens)) if lens else 0,
                you=sum(1 for w in low if w in ("you", "your")) / n * 100 if n else 0, we=sum(1 for w in low if w in ("we", "our", "us")) / n * 100 if n else 0,
                contractions=len(re.findall(r"\b\w+'(?:t|s|re|ve|ll|d)\b", allt)) / n * 100 if n else 0,
                questions=sum(1 for s in ss if s.endswith("?")), exclaim=sum(1 for s in ss if s.endswith("!")), top=c.most_common(12),
                acronyms=sorted(set(re.findall(r"\b[A-Z]{2,6}\b", clean(allt)))))


def build(ctx, copy, terms):
    p = ctx["profile"]
    s = stats(copy)
    L = [f"# Brand voice guide (draft): {p['brand']}", "", f"Prepared as of {ctx['as_of'].isoformat()}. These are patterns found in copy that is already approved. The product marketer decides which of them are the voice.", "",
         "## Your own words", "", f"- Voice note in the product profile: {p.get('voice') or '[MISSING]'}", ""]
    if not copy:
        return "\n".join(L + ["## What the approved copy does", "", "[MISSING] no approved copy found (company/approved-copy/). Add pieces that were approved and published, then run this again.", ""])
    L += ["## What the approved copy does", "", f"Based on {s['files']} piece(s), {s['words']:,} words, {s['sentences']} sentences."]
    if s["words"] < MIN_WORDS:
        L.append(f"This is a thin sample (under {MIN_WORDS:,} words). Treat the patterns as a first look, not a profile.")
    L += ["", "| Pattern | What was found |", "|---|---|", f"| Average sentence length | {s['avg_len']:.1f} words |", f"| Sentences over 25 words | {round(100 * s['long_share'])}% |",
          f"| Speaks to the reader ('you', 'your') | {s['you']:.1f} per 100 words |", f"| Speaks as the company ('we', 'our') | {s['we']:.1f} per 100 words |",
          f"| Contractions | {s['contractions']:.1f} per 100 words |", f"| Questions | {s['questions']} |", f"| Exclamation marks | {s['exclaim']} |",
          f"| Capitalized abbreviations | {', '.join(s['acronyms']) or 'none'} |", "", "Words used most (not counting common words): " + ", ".join(f"{w} ({n})" for w, n in s["top"]), "",
          "## Observed patterns to consider as rules", ""]
    L.append(f"- Sentence length: approved copy averages {s['avg_len']:.0f} words. " + ("Short and direct." if s["avg_len"] <= 18 else "Longer than most web copy; check whether that is intended."))
    L.append("- Point of view: " + ("addresses the reader directly more than it talks about the company." if s["you"] >= s["we"] else "talks about the company more than it addresses the reader."))
    L.append("- Tone markers: " + ("no exclamation marks." if not s["exclaim"] else f"{s['exclaim']} exclamation mark(s)."))
    L += ["", "## Words to avoid", ""]
    avoid = p["avoid_words"]
    L.append("Your avoid list: " + (", ".join(avoid) or "none set"))
    hits = [(w, f) for f, t in copy.items() for w in avoid + HYPE if has_phrase(t, w)]
    L += ["", "Conflicts: avoided or hype words that appear in approved copy:", ""]
    L += [f"- '{w}' in {f}" for w, f in sorted(set(hits))] or ["- None found."]
    L += ["", "## Terminology", ""]
    if terms:
        L += ["| Use | Do not use | Note |", "|---|---|---|"] + [f"| {t.get('use', '')} | {t.get('dont_use', '')} | {t.get('note', '')} |" for t in terms]
    else:
        L.append("[MISSING] no terminology list (company/terminology.csv).")
    L += ["", "## Before and after", "", "[MISSING: two or three pairs written by a person: a sentence in the old voice and the same sentence in the voice you want]", ""]
    return "\n".join(L)


def check(text, ctx, terms, copy):
    """Compare a draft with the guide. Returns (level, message) pairs: FAIL for avoid words and banned terms, WARN for style drift."""
    res = []
    for w in ctx["profile"]["avoid_words"]:
        if has_phrase(text, w):
            res.append(("FAIL", f"the word '{w}' is on your avoid list"))
    for t in terms:
        bad = t.get("dont_use", "")
        if bad and has_phrase(text, bad):
            res.append(("FAIL", f"use '{t.get('use', '')}' instead of '{bad}'"))
    if copy:
        ref = stats(copy)
        mine = stats({"draft": text})
        if mine["sentences"] and ref["avg_len"] and mine["avg_len"] > 1.5 * ref["avg_len"]:
            res.append(("WARN", f"sentences average {mine['avg_len']:.0f} words; approved copy averages {ref['avg_len']:.0f}"))
        if mine["long_share"] > max(0.25, 2 * ref["long_share"]):
            res.append(("WARN", f"{round(100 * mine['long_share'])}% of sentences are over 25 words; approved copy has {round(100 * ref['long_share'])}%"))
        if mine["exclaim"] and not ref["exclaim"]:
            res.append(("WARN", "the draft uses exclamation marks; the approved copy uses none"))
    return res
