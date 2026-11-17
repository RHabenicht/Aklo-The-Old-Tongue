# Aklo — The Old Tongue

An open-source Python command-line tool for exploring English-to-Aklo vocabulary, starting with the public [JLDevOps/Rlyehian](https://github.com/JLDevOps/Rlyehian) fan lexicon.

**Current scope:** A sourced vocabulary lookup and provisional lexical glossing tool—not a complete language, verified grammar, pronunciation guide, or fluent translator.

## Main features

- **English-to-Aklo word lookup:** Find recorded source forms for individual English terms.
- **Provisional text glossing:** Replace recognized words and expressions with their listed equivalents without inventing missing vocabulary.
- **Multiword phrase recognition:** Match entries such as `cross over` before processing individual words.
- **Ambiguity detection:** Display unresolved markers and alternatives when an English term has multiple source forms, rather than silently choosing one.
- **Unknown-word reporting:** Mark words missing from the reference dictionary as `⟦term?⟧`.
- **Formatting preservation:** Retain punctuation, whitespace, and line breaks in gloss output.
- **Documented source data:** Load 92 English entries extracted from one pinned upstream revision, with its license preserved.
- **Automated checks:** Run unit tests locally or through the included GitHub Actions workflow.

## Requirements

- Python 3.10 or later
- No third-party Python packages

## Getting started

Clone the repository and run these commands from its root directory:

```sh
python -m aklo_reference lookup "call"
python -m aklo_reference translate "cross over, soul!"
python -m aklo_reference sources
```

### Commands

| Command | What it does |
| --- | --- |
| `lookup "word"` | Returns every recorded Aklo form for an English entry, as JSON. |
| `translate "text"` | Produces a provisional gloss and reports ambiguous or unknown terms, as JSON. |
| `sources` | Displays the source repository, pinned revision, and license metadata. |

The `translate` command is named for discoverability; its output is **not** a complete semantic translation.

### Examples

```sh
python -m aklo_reference lookup "soul"
```

```json
{
  "term": "soul",
  "forms": ["orr'e"]
}
```

```sh
python -m aklo_reference translate "cross over, soul!"
```

The provisional gloss contains:

```text
ch', orr'e!
```

For an ambiguous lookup such as `call`, the reference data records both `'ai` and `uln`. The tool flags the term rather than selecting one without sufficient context.

## Vocabulary and research method

The bundled [lexicon](aklo_reference/data/lexicon.json) contains **92 English entries** extracted from the public upstream CSV at [revision `482bd14`](https://github.com/JLDevOps/Rlyehian/commit/482bd14e19d6a25094af800e6e2a65836484d319).

Only records labeled as standalone `word` entries are imported. One source entry was omitted from this derivative dataset. Distinct source spellings for the same English term are preserved as alternatives. The upstream material is a **fan-maintained glossary**, not an authoritative Lovecraftian dictionary.

The database and executable do not provide sentence grammar, morphology, tense, contextual disambiguation, or pronunciation. These would require separate, explicitly sourced design and validation before implementation.

## Testing

```sh
python -m unittest discover -s tests -v
```

The included GitHub Actions workflow runs the test suite on pushes and pull requests.

## Source and licensing

- **Upstream vocabulary:** [JLDevOps/Rlyehian](https://github.com/JLDevOps/Rlyehian)
- **Pinned data file:** [kadishtuor.csv at revision `482bd14`](https://github.com/JLDevOps/Rlyehian/blob/482bd14e19d6a25094af800e6e2a65836484d319/rlyehian/kadishtuor.csv)
- **Upstream license:** MIT; preserved in [`third_party/JLDevOps-LICENSE.txt`](third_party/JLDevOps-LICENSE.txt)

The code in this repository is licensed under the root [MIT license](LICENSE). The upstream vocabulary is separately provided under its original MIT license; retain the original notice when redistributing it.


## Expanded research and reverse lookup

The original 92-entry core remains unchanged. Optional research layers preserve source identity and ambiguity rather than silently replacing established meanings.

```sh
python -m aklo_reference sync
python -m aklo_reference research "blood"
python -m aklo_reference reverse "orr'e"
python -m aklo_reference lookup "remember" --expanded
python -m aklo_reference translate "blood and soul" --expanded
python -m aklo_reference research "winter" --include-generated
python -m aklo_reference sources
```

- `sync [all|offerings|rc1]` downloads and parses pinned public data into a local cache (default `~/.cache/aklo`, or set `AKLO_CACHE_DIR`).
- `research` and `reverse` report source-labelled candidates; `--core-only` restricts them to the original dictionary.
- `--expanded` on lookup and translate makes the RC-1 root index and locally cached Offerings data available. Conflicting forms remain ambiguous. The generated RC-1 report is searchable with `research`, `reverse` and expanded lookup; it is never used automatically by translate.
- `--include-generated` makes RC-1's automatically coined terms visible for research. Generated candidates are not established vocabulary.
- No network requests occur unless `sync` is called. Without an external cache, the original dictionary and small RC-1 research index are still available.

### External source catalog

| Source | Contents | Status |
| --- | --- | --- |
| [Offerings-to-Cthulhu dictionary](https://github.com/dobbscoin/Offerings-to-Cthulhu/blob/362bea6954092f51f74bf41cdf70996ee387aeff/contrib/site/rlyehian/lexicon.js) | 1,951 forward words, 110 forward phrases; reverse forms and glossary | Local cache, third-party rights unverified |
| [RC-1 report](https://github.com/ChouYuanjue/Rlyehian-Cthuvian-Translator/blob/0a62c9490c92d035fa09aaadaa156de86cab5cda/data/generated/common-generated-report.json) | 4,065 generated records: 271 semantic compounds and 3,794 coined forms | Local research cache |
| [RC-1 language specification](https://github.com/ChouYuanjue/Rlyehian-Cthuvian-Translator/blob/0a62c9490c92d035fa09aaadaa156de86cab5cda/docs/LANGUAGE_SPEC.md) | Reconstructed grammar and roots | Small source-labelled research index; grammar not yet implemented |

RC-1 declares MIT in its package metadata; Offerings contains multiple license notices and incorporates a third-party fan glossary and LingoJam data. The full external corpora are not redistributed in this repository. Cache access does not confer redistribution rights. Original source names and links remain intact. Aklo is the project name, not a claim that all historical Mythos languages share a canonical grammar.
