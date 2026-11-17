"""Optional, source-labelled Aklo research layers. No third-party corpus is bundled."""
import json
import os
import re
import tempfile
import unicodedata
from pathlib import Path
from urllib.request import urlopen

SOURCES = {
    "offerings": {
        "title": "Offerings-to-Cthulhu / LingoJam and fan glossary compilation",
        "revision": "362bea6954092f51f74bf41cdf70996ee387aeff",
        "url": "https://raw.githubusercontent.com/dobbscoin/Offerings-to-Cthulhu/362bea6954092f51f74bf41cdf70996ee387aeff/contrib/site/rlyehian/lexicon.js",
        "license": "Third-party dictionary rights not verified; local research only.",
    },
    "rc1": {
        "title": "RC-1 generated vocabulary report",
        "revision": "0a62c9490c92d035fa09aaadaa156de86cab5cda",
        "url": "https://raw.githubusercontent.com/ChouYuanjue/Rlyehian-Cthuvian-Translator/0a62c9490c92d035fa09aaadaa156de86cab5cda/data/generated/common-generated-report.json",
        "license": "MIT declared in package metadata; corpus redistribution not verified.",
    },
}
# A compact, independently selected research index of RC-1 core concepts.
# These are external reconstructions, not canon or approved dialect overrides.
RC1_ROOTS = {
    "stone": "kthar", "water": "ulh", "fire": "cthugh", "wind": "hral",
    "breath": "hral", "memory": "mnahn", "remember": "mnahn", "time": "rhan",
    "measurement": "zhrn", "large": "ghrath", "small": "vren", "tool": "fmagl",
    "machine": "fmagl", "plant": "rhygg", "sound": "ghor", "voice": "ghor",
    "light": "yll", "reveal": "yll", "offer": "fhayak", "transform": "wk'hmr",
    "hail": "ia", "gate": "nglui",
}
RC1_SPEC = "https://github.com/ChouYuanjue/Rlyehian-Cthuvian-Translator/blob/0a62c9490c92d035fa09aaadaa156de86cab5cda/docs/LANGUAGE_SPEC.md"

def norm(s):
    return unicodedata.normalize("NFC", s).replace("’", "'").replace("‘", "'").casefold().strip()

def cache_dir(path=None):
    return Path(path or os.environ.get("AKLO_CACHE_DIR") or Path.home() / ".cache" / "aklo")

def parse_source(name, raw):
    if name == "offerings":
        match = re.search(r"const\s+LEX\s*=\s*(\{.*\})\s*;\s*$", raw, re.S)
        if not match:
            raise ValueError("Offerings: expected a JSON LEX object")
        obj = json.loads(match.group(1))
        if not isinstance(obj, dict):
            raise ValueError("Offerings: invalid dictionary")
        for key in ("encWords", "encPhrases", "decWords", "decPhrases", "gloss"):
            if not isinstance(obj.get(key), dict):
                raise ValueError("Offerings: missing " + key)
        return obj
    if name != "rc1":
        raise ValueError("Unknown source")
    obj = json.loads(raw)
    if not isinstance(obj, list) or any(
        not isinstance(r, dict) or not isinstance(r.get("source_base"), str)
        or not isinstance(r.get("rc"), str) or not isinstance(r.get("strategy"), str)
        for r in obj
    ):
        raise ValueError("RC-1: invalid generated report")
    return obj

def sync(path=None, selected=None):
    """Explicitly retrieve pinned public files; never execute downloaded code."""
    target = cache_dir(path)
    target.mkdir(parents=True, exist_ok=True)
    status = {}
    for name in selected or SOURCES:
        meta = SOURCES[name]
        temp = None
        try:
            with urlopen(meta["url"], timeout=30) as response:
                payload = response.read(5_000_001)
            if len(payload) > 5_000_000:
                raise ValueError("Source exceeds size limit")
            obj = parse_source(name, payload.decode("utf-8"))
            with tempfile.NamedTemporaryFile("w", encoding="utf-8", dir=target, delete=False) as f:
                temp = Path(f.name)
                json.dump({"revision": meta["revision"], "data": obj}, f, ensure_ascii=False)
            temp.replace(target / (name + ".json"))
            status[name] = {"status": "cached", "revision": meta["revision"]}
        except (OSError, ValueError) as exc:
            if temp is not None:
                temp.unlink(missing_ok=True)
            status[name] = {"status": "error", "message": str(exc)}
    return status

def load(name, path=None):
    file = cache_dir(path) / (name + ".json")
    if not file.exists():
        return None
    obj = json.loads(file.read_text(encoding="utf-8"))
    if obj.get("revision") != SOURCES[name]["revision"]:
        raise ValueError("Stale source cache: " + name + "; run sync")
    return obj["data"]

def records(core, expanded=False, include_generated=False, path=None):
    """Yield distinct source-labelled mappings. Generated coinages are opt-in."""
    seen = set()
    def emit(english, form, source, kind):
        if not isinstance(english, str) or not isinstance(form, str) or not english.strip() or not form.strip():
            return
        key = (norm(english), norm(form), source, kind)
        if key in seen:
            return
        seen.add(key)
        return {"english": english, "form": form, "source": source, "kind": kind}
    for english, forms in core.items():
        for form in forms:
            item = emit(english, form, "jldevops", "source-reference")
            if item: yield item
    if not expanded:
        return
    for english, form in RC1_ROOTS.items():
        item = emit(english, form, "rc1-spec", "external-reconstruction")
        if item: yield item
    off = load("offerings", path)
    if off is not None:
        for table in ("encWords", "encPhrases"):
            for english, form in off[table].items():
                item = emit(english, form, "offerings", "fan-lookup")
                if item: yield item
        for table in ("decWords", "decPhrases"):
            for form, senses in off[table].items():
                if isinstance(senses, list):
                    for english in senses:
                        item = emit(english, form, "offerings", "fan-lookup")
                        if item: yield item
    rc = load("rc1", path)
    if rc is not None:
        for row in rc:
            strategy = row["strategy"]
            if strategy != "offline_semantic_compound" and not include_generated:
                continue
            item = emit(row["source_base"], row["rc"], "rc1", strategy)
            if item: yield item

def search(core, term, reverse=False, expanded=False, include_generated=False, path=None):
    key = "form" if reverse else "english"
    rows = [r for r in records(core, expanded, include_generated, path) if norm(r[key]) == norm(term)]
    other = "english" if reverse else "form"
    return {"term": term, "matches": rows, "ambiguous": len({norm(r[other]) for r in rows}) > 1}

def translation_entries(core, expanded=False, path=None):
    # Preserve the original mapping in core mode. Expanded translation uses
    # source alternatives, and leaves conflicts unresolved. Machine-generated
    # compounds are research candidates only, never automatic translations.
    if not expanded:
        return core
    result = {}
    for row in records(core, expanded=True, path=path):
        if row["source"] == "rc1":
            continue
        forms = result.setdefault(norm(row["english"]), [])
        if norm(row["form"]) not in {norm(f) for f in forms}:
            forms.append(row["form"])
    return result

def status(path=None):
    return {name: {**meta, "cached": (cache_dir(path) / (name + ".json")).is_file()}
            for name, meta in SOURCES.items()}
