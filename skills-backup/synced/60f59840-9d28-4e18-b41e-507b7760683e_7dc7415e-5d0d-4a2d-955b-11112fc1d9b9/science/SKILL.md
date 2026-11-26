---
name: science
description: Scientific research and rigorous-citation skill for claude.ai. Triggers on research, paper, arxiv, PubMed, literature review, theorem, simulation, biology, chemistry, physics, scientific writing, IMRaD, LaTeX, hypothesis test, statistical analysis, bioinformatics, formal verification (Lean/Coq), or any request where rigorous citation and methodology matter more than speed. Uses web_search and web_fetch on arxiv/PubMed/doi.org/journal sites for primary sources, the bash sandbox for SciPy/NumPy/scikit-learn/biopython/RDKit when computation is needed, and writes proper IMRaD-structured output with paraphrased citations and explicit uncertainty. Replaces the Claude Code v2 version that depended on Milvus, sentence-transformers Arxiv-RAG, and MCTS research trees — none of which work reliably in claude.ai.
---

# Science — claude.ai Research Workflow

The job: when the user asks something where being *right* matters more than being *fast*, switch into research mode. Real sources, paraphrased citations, explicit uncertainty, methodology stated, IMRaD structure for writeups.

This is the claude.ai version. The Claude Code Milvus + Arxiv-RAG + MCTS version assumes a local vector DB, a sentence-transformer model, and a multi-iteration tree search across a paper corpus. None of that works here. What survives: the **research discipline** itself, plus claude.ai's actual tools (web_search, web_fetch, the sandbox for computation, the pdf-reading skill for paper extraction).

---

## When to invoke

Use when the user asks:
- "What does the literature say about X"
- "Run an analysis / simulation / computation on Y"
- "Help me write up Z" (where Z is a paper, technical report, lab writeup)
- "Is the claim that X true / well-supported"
- Domain-specific science terms: arxiv, PubMed, p-value, confidence interval, theorem, proof, ANOVA, dose-response, structure-activity relationship, etc.

Skip for casual factual questions ("what year was the Apollo 11 mission") — those are a single `web_search`, not a research workflow.

---

## Workflow

### Step 1 — Scope the question

Before searching anything, restate:
- What's the precise claim or question?
- What discipline? (matters for which sources are primary)
- What kind of answer is wanted: a literature summary, a fresh computation, a writeup?

If the question is malformed (vague, presupposes a false premise, conflates two questions), surface that before searching. A research pass on a malformed question wastes both Claude's tokens and the user's time.

### Step 2 — Source identification

Pick the right primary sources by discipline:

| Field | Primary | Secondary |
|---|---|---|
| Physics, math, CS, ML | arxiv.org | journal sites, conference proceedings, NeurIPS / ICML / ICLR |
| Life sciences, medicine | pubmed.ncbi.nlm.nih.gov, biorxiv.org, medrxiv.org | journal sites |
| Chemistry | pubs.acs.org, pubs.rsc.org, ChemRxiv | RDKit / ChEMBL for compound data |
| Earth/climate | NOAA, NASA, IPCC reports | journal sites |
| Social science | osf.io, ssrn.com | journal sites; flag replication caveats explicitly |
| Software engineering empirical | empiricalse.org, ICSE/FSE proceedings | flag if claim is from blog vs paper |
| Formal methods / proofs | Mathlib, Coq stdlib, Lean community | textbooks, paper appendices |

**Use `web_search` to find candidate sources, then `web_fetch` on the actual paper page or PDF.** Do not rely on the search snippet alone for any claim that will be cited.

### Step 3 — Read carefully, paraphrase always

For each source you'll cite:
- Fetch the actual paper (via `web_fetch` on the abstract page; if a PDF URL is reachable, fetch that)
- Read enough to verify the claim you're attributing to it (don't rely on the abstract for fine-grained claims)
- For long papers where you need a specific finding: use the `pdf-reading` skill workflow (page-by-page) rather than naïve full-text dumping
- **Always paraphrase. Never quote directly except in extreme cases.** Per claude.ai's copyright rules, quotes max 15 words, max 1 per source, paraphrasing is the default.

When citing inline, state the finding in your own words and indicate the source. Example: "Smith et al. (2023) found that [paraphrased finding]." Use `` tags only when web_search results have been used and citation indices are available; otherwise state the source naturally.

### Step 4 — Explicit uncertainty

Distinguish:
- What the source actually claims
- What's implied or inferred
- What's contested in the literature
- What's *your* synthesis going beyond any single source

Bad: "X causes Y." (asserting causation that the source might not have established)
Good: "X is associated with Y in observational studies; the strongest causal evidence is [specific RCT or natural experiment], which has [specific limitation]."

For meta-questions (does the literature converge?), name dissenting views explicitly.

### Step 5 — Computation, when needed

If the request involves running a simulation, fitting a model, or doing a calculation:
- Use the bash sandbox at `/home/claude/`
- Standard libraries available via `pip install --break-system-packages`: numpy, scipy, pandas, scikit-learn, statsmodels, biopython, rdkit, matplotlib, plotly, sympy, networkx
- Heavy / specialized tools (Lean, Coq, Stan, JAGS, GROMACS): can sometimes install via apt, but check time budget first. For Lean specifically, `elan` then `lake` is the install path.
- Show the actual code that was run, the actual output, and any caveats about the computation (numerical stability, convergence, sample size).

For statistical analyses: state the test, the assumptions, whether the assumptions hold for this data, and the actual p-values / effect sizes / confidence intervals — not just "significant" or "not significant".

### Step 6 — Writeup (when applicable)

If the user wants a paper / report / writeup, use **IMRaD** structure (Introduction, Methods, Results, and Discussion):

- **Introduction**: what's the question, what's known, what's the gap, what are we doing
- **Methods**: exactly what was done, in enough detail that someone could replicate
- **Results**: what was found — facts only, no interpretation here
- **Discussion**: what it means, what it doesn't mean, limitations, future work

For LaTeX output, write a `.tex` file in `/home/claude/` and try to compile via `pdflatex` if needed. Common packages: amsmath, amssymb, booktabs, biblatex/natbib, hyperref, geometry. If the user wants a particular journal style (`acmart`, `IEEEtran`, `elsarticle`), use the matching documentclass.

### Step 7 — Honest endnote

Close every research-mode response with one sentence about what's still uncertain, what wasn't checked, or what would change the conclusion. Don't pretend to a confidence you don't have.

---

## What got stripped from v2

- **Arxiv-RAG with overlap chunking + Milvus** — Milvus is a server-grade vector DB, not installable per-session. The "overlap chunking" insight (1/3 overlap prevents context loss) is still good practice when chunking, but it's not load-bearing for normal research. Use `pdf-reading` skill workflow instead.
- **MCTS research tree exploration** — multi-iteration tree search across a paper corpus needs subagents to score branches in parallel. In claude.ai, do at most 1–2 levels of follow-up search by hand, prioritized by what answers the actual question.
- **GroundedPRM step-level paper verification** — replaced by Step 4 (explicit uncertainty) and Step 7 (honest endnote). Verification is built into the workflow rather than being a separate ML pipeline.
- **Sentence-transformer embeddings** — `pip install sentence-transformers` is possible in the sandbox but slow to first-use and rarely needed for one-shot research. Skip unless the user explicitly wants embedding-based work.
- **293-skill ScienceClaw aggregation** — was always a label for "be rigorous about this domain". Kept as a routing concept; not as 293 actual subskills.

---

## Discipline-specific notes

**ML / AI papers**: arxiv abstracts are written by authors and overstate findings. Always check the experimental section for sample sizes, ablations, and which baselines were chosen. Be especially skeptical of claims about "emergent" behavior — most are sensitive to evaluation choices.

**Medicine / clinical research**: distinguish observational vs. RCT, and note effect sizes (NNT, absolute risk reduction) rather than just relative risks. Single trials rarely establish anything; meta-analyses and Cochrane reviews are stronger.

**Social science**: many findings post-2010 have failed to replicate. Default to skepticism on flashy single-study results. Check Many Labs / Open Science Collaboration replication status when relevant.

**Formal verification / theorem proving**: when stating that something is "proved", state in *which* system (Lean 4 / Mathlib, Coq, Isabelle), and whether the proof has been checked end-to-end or relies on `sorry` / admitted axioms.

**Chemistry**: structure-activity claims need the actual structure (SMILES or InChI), not just a name. RDKit can canonicalize.

**Bioinformatics**: state the genome build, the alignment tool, the version, and the parameters. "Aligned with BWA" is not enough; "BWA-MEM v0.7.17 with default params against GRCh38" is.

---

## Tool reference

| Need | Tool |
|---|---|
| Find candidate sources | `web_search` |
| Fetch paper / abstract | `web_fetch` |
| Read PDF carefully | the `pdf-reading` skill workflow |
| Run analysis / model | `bash_tool` (numpy, scipy, etc.) |
| Write paper | `create_file` (.tex, .md, .docx — use docx skill for Word) |
| Visualize data | `bash_tool` with matplotlib → save PNG → `view` to display |
| Visualize structure (e.g., a study design) | `visualize:show_widget` |
| Track research state across sessions | `memory_user_edits` for stable facts; `conversation_search` for prior threads |

---

## Anti-patterns

- **Bibliography hallucination**: never invent citations. If you can't find a source, say so. Don't fabricate Smith (2019) titles.
- **Confidence inflation**: don't write "X has been shown to..." when the truth is "one study suggests X may...".
- **Discipline confusion**: don't cite a CS arxiv preprint as authoritative on a medical claim.
- **Single-source dependency**: for any non-trivial claim, look for at least one corroborating source. If none exists, that's itself worth reporting.
- **Stale knowledge**: search rather than relying on training data for anything published in the last 2 years.
