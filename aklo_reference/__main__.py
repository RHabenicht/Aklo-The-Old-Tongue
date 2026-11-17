"""Provisional Aklo word lookup from a public fan lexicon."""
import argparse
import json
import re
import unicodedata
from functools import lru_cache
from importlib.resources import files
from . import research

TOKENS = re.compile(r"[^\W\d_]+(?:[\u0300-\u036f]+)?(?:[\u2019'-][^\W\d_]+(?:[\u0300-\u036f]+)?)*|\s+|.", re.UNICODE)

@lru_cache(maxsize=1)
def data():
    with files("aklo_reference").joinpath("data/lexicon.json").open(encoding="utf-8") as f:
        return json.load(f)

def normalize(term):
    return unicodedata.normalize("NFC", term).replace("’", "'").casefold()

def lookup(term):
    return data()["entries"].get(normalize(term), [])

def analyze(text, terms=None):
    """Preserve punctuation; flag ambiguous/unmapped tokens without inventing words."""
    tokens = TOKENS.findall(text)
    if terms is None:
        terms = data()["entries"]
    out, issues = [], []
    i = 0
    while i < len(tokens):
        t = tokens[i]
        if t.isspace() or not any(c.isalpha() for c in t):
            out.append(t)
            i += 1
            continue
        key, count = normalize(t), 1
        for n in range(min(7, len(tokens)-i), 1, -1):
            candidate = ''.join(tokens[i:i+n])
            if '\n' not in candidate and normalize(candidate) in terms:
                key, count = normalize(candidate), n
                break
        original = ''.join(tokens[i:i+count])
        forms = terms.get(key, [])
        if len(forms) == 1:
            out.append(forms[0])
        else:
            out.append(f'⟦{original}?⟧')
            issues.append({'term':original,'type':'ambiguous' if forms else 'unknown','forms':forms})
        i += count
    return {'gloss': ''.join(out), 'issues': issues}

def main(argv=None):
    p = argparse.ArgumentParser(description="Aklo — The Old Tongue: source-labelled lexical research")
    p.add_argument("--cache-dir", help="Override the local research cache")
    sub = p.add_subparsers(dest="command", required=True)
    lookup_cmd = sub.add_parser("lookup")
    lookup_cmd.add_argument("term")
    lookup_cmd.add_argument("--expanded", action="store_true")
    gloss_cmd = sub.add_parser("translate")
    gloss_cmd.add_argument("text")
    gloss_cmd.add_argument("--expanded", action="store_true")
    for name in ("research", "reverse"):
        q = sub.add_parser(name)
        q.add_argument("term")
        q.add_argument("--core-only", action="store_true")
        q.add_argument("--include-generated", action="store_true")
    sync_cmd = sub.add_parser("sync")
    sync_cmd.add_argument("source", choices=["all", *research.SOURCES], nargs="?", default="all")
    sub.add_parser("sources")
    args = p.parse_args(argv)
    core = data()["entries"]
    if args.command == "lookup":
        if args.expanded:
            result = research.search(core, args.term, expanded=True, path=args.cache_dir)
        else:
            result = {"term": args.term, "forms": lookup(args.term)}
    elif args.command == "translate":
        print("PROVISIONAL LEXICAL GLOSS (not a completed translation)")
        result = analyze(args.text, research.translation_entries(core, args.expanded, args.cache_dir))
    elif args.command in ("research", "reverse"):
        result = research.search(core, args.term, reverse=args.command == "reverse",
                                 expanded=not args.core_only,
                                 include_generated=args.include_generated, path=args.cache_dir)
    elif args.command == "sync":
        chosen = None if args.source == "all" else [args.source]
        result = research.sync(args.cache_dir, chosen)
    else:
        result = {"core": data()["source"], "external": research.status(args.cache_dir),
                  "rc1_spec": research.RC1_SPEC}
    print(json.dumps(result, ensure_ascii=False, indent=2))
    if args.command == "sync" and any(v["status"] == "error" for v in result.values()):
        return 1
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
