"""Check a positioning document: no hype words, no gaps hidden, proof under every pillar, acronyms spelled out."""
import re

from .util import has_phrase


def check_doc(text, profile):
    res = []
    f = lambda m: res.append(("FAIL", m))
    w = lambda m: res.append(("WARN", m))
    scan = text.split("\n## Words to avoid")[0]
    for word in profile["avoid_words"]:
        if has_phrase(scan, word):
            f(f"the word '{word}' is on your avoid list")
    open_slots = len(re.findall(r"\[MISSING", text))
    if open_slots:
        f(f"{open_slots} [MISSING] slots are still open")
    pillars = re.split(r"(?m)^### Pillar \d+:", text)[1:]
    if not pillars:
        f("no messaging pillars found")
    for i, block in enumerate(pillars, 1):
        block = block.split("\n## ")[0]
        proofs = re.findall(r"(?m)^- Proof \(([^)]*)\)", block)
        if len(proofs) < 2:
            f(f"pillar {i} has {len(proofs)} proof point(s); it needs at least 2")
        for m in proofs:
            if "source:" not in m:
                f(f"pillar {i} has a proof point with no source")
    if "ICP status: DRAFT" in text:
        f("the ideal customer profile is still a draft: the product marketer has not recorded a decision (use `decide`)")
    undecided = len(re.findall(r"(?m)^- .*: needs a decision", text))
    if undecided:
        w(f"{undecided} ranked segment(s) still need a product marketer decision")
    if "## Positioning statement" not in text:
        f("no positioning statement section")
    if "Closed deals:" not in text:
        w("no 'Data used' section, so the evidence base is not stated")
    known = set(profile.get("known_acronyms", [])) | {"DRAFT"}
    seen = set()
    for m in re.finditer(r"\b[A-Z]{2,6}\b", text):
        a = m.group(0)
        if a in known or a in seen:
            continue
        seen.add(a)
        before, after = text[max(0, m.start() - 1):m.start()], text[m.end():m.end() + 2]
        if not ((before == "(" and after.startswith(")")) or after == " ("):
            f(f"acronym '{a}' is not spelled out on first use")
    return res


def format_results(res):
    return "\n".join(f"{l}: {m}" for l, m in res) if res else "Document OK"
