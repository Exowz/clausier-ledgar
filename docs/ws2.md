# WS2 Retrieval: handover note

Owner: Wiyao (from Tue 20 Oct), Ewan (from Thu 22 Oct). Tasks T06 (index) and T07 (evaluation). Last updated:
Thu 22 Oct.

## Goal

From a pasted clause or a lawyer's question ("termination clauses with a 30-day notice period"), return the most
similar clauses of the clause bank (the LEDGAR train split, 60,000 clauses), and show it works (course checkpoint m2).

## What WS2 may use from the rest of the repo

- `src.data.load_split(split, n=None, seed=42) -> (texts, labels)`: `n` gives a seeded subset. Use it to develop
  on a few thousand clauses; the full 60k bank is embedded by Ewan.
- `src.data.get_label_names()`, `src.data.normalize_text(text)`, `src.utils.set_seed`, `src.utils.PROJECT_ROOT`.
- Nothing else: WS2 does not import classification or audit code.

## Decisions (fixed, taken from the course)

- Dense index: `sentence-transformers/all-MiniLM-L6-v2`, `encode(texts, normalize_embeddings=True)`, scores
  `D @ q` (cosine, since rows have norm 1), top-k with `np.argsort(-scores)[:k]`. Embeddings cached to
  `outputs/retrieval/` as `.npy`. No FAISS, no other embedding model.
- Lexical comparison: TF-IDF vectors + cosine, and the keyword overlap score (`words_of(q) & words_of(c)`). No BM25,
  no rank fusion.
- Constraint filter: a `re` function that extracts durations ("30 days", "thirty (30) days", "sixty days") so that
  a query asking for a 30-day notice only keeps clauses that mention 30 days.
- Evaluation, with "same label = relevant" as the proxy: queries = test clauses (a seeded sample is fine), bank =
  train. Report top-1 accuracy and precision at 5 and 10, dense versus TF-IDF versus keyword overlap.
- `data/queries.yaml`: 15 to 20 lawyer-style queries, each with the clause type a lawyer expects. Check the top 5
  results by hand and write down what is right and wrong.
- Only techniques seen in class. Python 3.11, seed 42, CLI with argparse, no absolute paths, `ruff check .` clean,
  small tests in `tests/` that do not download anything.

## Files

`src/retrieval/index.py` (embed, cache, top-k, TF-IDF and keyword scores), `src/retrieval/constraints.py`
(durations), `src/retrieval/evaluate.py` (CLI, writes `outputs/retrieval/metrics.json` and example results),
`data/queries.yaml`, the `retrieval` target of the `Makefile`.

## Done / left

Done: T06 and T07. `make retrieval` embeds the 60,000 training clauses (73 s on an M2 Pro GPU, cached in
`outputs/retrieval/bank_embeddings_all.npy`, not in git), evaluates 1,000 seeded test queries and the 18 lawyer
queries, and writes `outputs/retrieval/metrics.md`, `lawyer_queries.md` and `examples.md`. `--n-bank 2000
--n-queries 100 --device cpu` runs in about 15 s for development. Results and the hand reading are in the README
(Results, Clause retrieval).

Left: nothing required. For an app, `DenseIndex(embed(...), load_model()).search(query, k)` and `search_with_days`
answer one question at a time.
