"""Evaluate clause retrieval by same-label relevance and review lawyer queries."""

import argparse
from pathlib import Path
from time import perf_counter

import numpy as np
import yaml

from src.data import get_label_names, load_split
from src.retrieval.index import MODEL_NAME, DenseIndex, OverlapIndex, TfidfIndex, embed, load_model, search_with_days
from src.utils import ensure_dir, resolve_path, save_json, set_seed


def precision_at_k(retrieved_labels: np.ndarray, query_labels: np.ndarray, k: int) -> np.ndarray:
    """Return each query's share of matching labels among its first k results."""
    return (retrieved_labels[:, :k] == query_labels[:, None]).mean(axis=1)


def bootstrap_mean(values: np.ndarray, n_boot: int = 1000, seed: int = 42) -> tuple[float, float, float]:
    """Return the sample mean and a percentile bootstrap interval over queries."""
    values = np.asarray(values, dtype=float)
    if len(values) == 0:
        raise ValueError("bootstrap_mean requires at least one query")
    rng = np.random.default_rng(seed)
    resamples = rng.choice(values, size=(n_boot, len(values)), replace=True).mean(axis=1)
    return float(values.mean()), float(np.percentile(resamples, 2.5)), float(np.percentile(resamples, 97.5))


def _format_interval(values: tuple[float, float, float]) -> str:
    return f"{values[0]:.3f} [{values[1]:.3f}, {values[2]:.3f}]"


def _snippet(text: str) -> str:
    return text[:200].replace("\n", " ").replace("|", "\\|")


def _load_lawyer_queries(path: Path, label_names: list[str]) -> list[dict[str, str]]:
    with path.open(encoding="utf-8") as file:
        queries = yaml.safe_load(file)
    if not isinstance(queries, list):
        raise ValueError(f"Expected a list of lawyer queries in {path}")
    for item in queries:
        if not isinstance(item, dict) or not isinstance(item.get("query"), str):
            raise ValueError(f"Each lawyer query in {path} needs a query string")
        if item.get("expected") not in label_names:
            raise ValueError(f"Unknown expected label {item.get('expected')!r} in {path}")
    return queries


def main(argv: list[str] | None = None) -> None:
    """Evaluate dense and lexical retrieval, then write metrics and example reports."""
    parser = argparse.ArgumentParser(description="Evaluate LEDGAR clause retrieval")
    parser.add_argument("--n-bank", type=int, default=None)
    parser.add_argument("--n-queries", type=int, default=1000)
    parser.add_argument("--k", type=int, default=10)
    parser.add_argument("--queries", default="data/queries.yaml")
    parser.add_argument("--out", default="outputs/retrieval")
    parser.add_argument("--device", default="auto")
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args(argv)
    if args.n_bank is not None and args.n_bank < 10:
        parser.error("--n-bank must be at least 10")
    if not 1 <= args.n_queries <= 10_000:
        parser.error("--n-queries must be between 1 and 10000")
    if args.k < 10:
        parser.error("--k must be at least 10 to report precision at 10")

    set_seed(args.seed)
    label_names = get_label_names()
    lawyer_queries = _load_lawyer_queries(resolve_path(args.queries), label_names)
    bank_texts, bank_labels = load_split("train", n=args.n_bank, seed=args.seed)
    test_texts, test_labels = load_split("test")
    selected = np.sort(np.random.default_rng(args.seed).choice(10_000, args.n_queries, replace=False))
    query_texts = [test_texts[int(index)] for index in selected]
    query_labels = test_labels[selected]
    dedup_mask = np.load(resolve_path("outputs/data/test_dedup_mask.npy"))
    if dedup_mask.shape != (10_000,) or dedup_mask.dtype != np.bool_:
        raise ValueError("outputs/data/test_dedup_mask.npy must contain 10,000 booleans")
    selected_dedup = dedup_mask[selected]
    if not selected_dedup.any():
        raise ValueError("The sampled test queries contain no deduplicated clauses")
    out = ensure_dir(args.out)

    start = perf_counter()
    model = load_model(None if args.device == "auto" else args.device)
    bank_vectors = embed(bank_texts, model, out / f"bank_embeddings_{args.n_bank or 'all'}.npy")
    query_vectors = embed(query_texts, model)
    embedding_seconds = perf_counter() - start

    indexes = {}
    timings = {"embedding": embedding_seconds}
    rankings = {}
    start = perf_counter()
    indexes["dense"] = DenseIndex(bank_vectors, model)
    rankings["dense"] = indexes["dense"].search_vectors(query_vectors, args.k)
    timings["dense"] = perf_counter() - start
    start = perf_counter()
    indexes["tfidf"] = TfidfIndex(bank_texts)
    rankings["tfidf"] = indexes["tfidf"].search_many(query_texts, args.k)
    timings["tfidf"] = perf_counter() - start
    start = perf_counter()
    indexes["overlap"] = OverlapIndex(bank_texts)
    rankings["overlap"] = indexes["overlap"].search_many(query_texts, args.k)
    timings["overlap"] = perf_counter() - start

    metrics = {
        "config": {"n_bank": len(bank_texts), "n_queries": len(query_texts),
                   "n_dedup_queries": int(selected_dedup.sum()), "k": args.k,
                   "seed": args.seed, "model": MODEL_NAME},
        "timings_seconds": timings,
        "results": {},
    }
    metrics_lines = ["# Clause retrieval metrics", "", "Same clause type is treated as relevant.", "",
                     "| Method | Query set | n | Top-1 accuracy | Precision at 5 | Precision at 10 |",
                     "| --- | --- | ---: | ---: | ---: | ---: |"]
    for method, ranking in rankings.items():
        method_results = {}
        for set_name, mask in (("all", np.ones(len(query_texts), dtype=bool)), ("deduplicated", selected_dedup)):
            retrieved_labels = bank_labels[ranking[mask]]
            labels = query_labels[mask]
            scores = {"top_1_accuracy": bootstrap_mean(precision_at_k(retrieved_labels, labels, 1), seed=args.seed),
                      "precision_at_5": bootstrap_mean(precision_at_k(retrieved_labels, labels, 5), seed=args.seed),
                      "precision_at_10": bootstrap_mean(precision_at_k(retrieved_labels, labels, 10), seed=args.seed)}
            method_results[set_name] = {"n": len(labels), **dict(scores)}
            metrics_lines.append(f"| {method} | {set_name} | {len(labels)} | "
                                 f"{_format_interval(scores['top_1_accuracy'])} | "
                                 f"{_format_interval(scores['precision_at_5'])} | "
                                 f"{_format_interval(scores['precision_at_10'])} |")
        metrics["results"][method] = method_results
    metrics_text = "\n".join(metrics_lines) + "\n"
    save_json(metrics, out / "metrics.json")
    (out / "metrics.md").write_text(metrics_text, encoding="utf-8")

    lawyer_lines = ["# Lawyer queries", ""]
    summary = {method: [0, 0] for method in indexes}
    for number, item in enumerate(lawyer_queries, 1):
        query, expected = item["query"], item["expected"]
        lawyer_lines.extend([f"## Query {number}", "", f"Query: {query}", "", f"Expected clause type: {expected}", ""])
        for method, index in indexes.items():
            results, days = search_with_days(index, query, bank_texts)
            if method == "dense":
                lawyer_lines.extend([f"Days extracted: {', '.join(map(str, sorted(days))) if days else 'none'}", ""])
            lawyer_lines.extend([f"### {method}", "", "| Rank | Score | Label | Expected | Clause |",
                                 "| ---: | ---: | --- | --- | --- |"])
            found = [label_names[int(bank_labels[bank_index])] == expected for bank_index, _ in results]
            summary[method][0] += bool(found and found[0])
            summary[method][1] += any(found)
            for rank, (bank_index, score) in enumerate(results, 1):
                label = label_names[int(bank_labels[bank_index])]
                lawyer_lines.append(f"| {rank} | {score:.3f} | {label} | {'yes' if found[rank - 1] else 'no'} | "
                                    f"{_snippet(bank_texts[bank_index])} |")
            lawyer_lines.append("")
    summary_lines = ["## Summary", "", "| Method | Expected at rank 1 | Expected in top 5 |",
                     "| --- | ---: | ---: |"]
    summary_lines.extend(f"| {method} | {counts[0]}/{len(lawyer_queries)} | {counts[1]}/{len(lawyer_queries)} |"
                         for method, counts in summary.items())
    lawyer_lines.extend(summary_lines)
    (out / "lawyer_queries.md").write_text("\n".join(lawyer_lines) + "\n", encoding="utf-8")

    example_indices = np.random.default_rng(args.seed).choice(len(query_texts), size=min(3, len(query_texts)),
                                                               replace=False)
    example_lines = ["# Seeded test examples", "", "Same clause type is treated as relevant.", ""]
    for number, query_index in enumerate(example_indices, 1):
        example_lines.extend([f"## Example {number}", "", f"Query: {_snippet(query_texts[query_index])}", "",
                              f"Query label: {label_names[int(query_labels[query_index])]}", ""])
        for method, ranking in rankings.items():
            example_lines.extend([f"### {method}", "", "| Rank | Label | Clause |", "| ---: | --- | --- |"])
            for rank, bank_index in enumerate(ranking[query_index, :3], 1):
                example_lines.append(f"| {rank} | {label_names[int(bank_labels[bank_index])]} | "
                                     f"{_snippet(bank_texts[bank_index])} |")
            example_lines.append("")
    (out / "examples.md").write_text("\n".join(example_lines) + "\n", encoding="utf-8")

    print(metrics_text)
    print("\n".join(summary_lines))


if __name__ == "__main__":
    main()
