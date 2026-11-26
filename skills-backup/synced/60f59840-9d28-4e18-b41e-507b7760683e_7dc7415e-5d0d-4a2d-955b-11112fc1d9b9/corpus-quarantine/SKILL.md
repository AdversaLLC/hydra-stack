---
name: corpus-quarantine
description: Filter a keyword-scraped corpus (GitHub repos, arXiv or OpenAlex records, archive.org items) by requiring domain-specific vocabulary, and QUARANTINE the excluded rows as their own file instead of discarding them. Triggers on "scrape repos for X", "pull the literature on X", "how many papers/repos mention X", "rank by stars/citations", or any time a ranking or count is about to be quoted from a keyword search. Observed false-positive rates without this step were 30-45 percent (name collisions like GraphCore-the-graph-library, "mpss" matching a game-server SDK, "bulk synchronous" matching CHARMM). Not for hand-curated lists.
---

# Corpus Quarantine — filter hard, keep the rejects

Keyword search returns everything that shares a word. Rankings and counts are meaningless until
topic-filtered, and a filter you cannot audit is an assertion.

## Workflow

1. **Scrape wide.** Broad queries, high result caps. Do not pre-filter at query time.
2. **Write a STRONG regex** requiring vocabulary only the real domain uses (part numbers, tool
   names, ISA names, project-specific terms). Test it on the top 20 hits by hand first.
3. **Split, do not drop.** `kept, quarantined = cq_split(df, text_cols, strong_pattern)`
4. **Save both files.** `<name>_corpus.csv` and `<name>_false_positives.csv`. The second file is
   what makes the first one credible.
5. **Report the rate.** "N retained of M (X percent false positives)" goes in the document.
6. **Only then** compute rankings, counts, survival curves, or citation orders.

## Known collision patterns (add to yours)

| Token | Collides with |
|---|---|
| graphcore, GraphCore | NetworkX-style graph libraries, game builders, LLM workflow tools |
| ipu | image processing units, Intel IPU network parts |
| poplar, popart | trees, art |
| mpss | mass-SSH tools, game-server SDKs, course notes |
| transputer (OpenAlex) | formal-methods surveys, medical radiation physics |
| bulk synchronous parallel (OpenAlex) | CHARMM, ERA-40 reanalysis, power-electronics surveys |

## Anti-patterns

- Quoting "most-cited" or "top-starred" from an unfiltered bucket.
- Deleting the excluded rows. A reviewer asking "what did you drop?" must get a file, not a shrug.
- A filter with no part numbers or tool names in it — too weak to separate the domain.
