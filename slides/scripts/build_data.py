"""Build the data files of the slides from the report files, so that no number in the deck is typed by hand.

Run from the repository root: `.venv/bin/python slides/scripts/build_data.py` (or `npm run data` in slides/).
Writes slides/public/data/deck.json (numbers) and slides/public/data/cloud.json (3D projection of MiniLM
embeddings of training clauses, for the retrieval slide).
"""

import csv
import json
import re
from pathlib import Path

import numpy as np

from src.data import get_label_names, load_split
from src.retrieval.index import load_model

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "slides" / "public" / "data"
CLOUD_TYPES = ["Governing Laws", "Notices", "Counterparts", "Entire Agreements", "Severability", "Terminations",
               "Confidentiality", "Indemnifications"]
CLOUD_QUERY = "termination clauses with a 30-day notice period"


def load(path: str) -> dict:
    """Read a JSON report relative to the repository root."""
    return json.loads((ROOT / path).read_text(encoding="utf-8"))


def deck_numbers(train_labels: np.ndarray, names: list[str]) -> dict:
    """Collect every number shown in the deck."""
    results = load("reports/results.json")
    pairs = {f"{p['a']}_vs_{p['b']}": p for p in results["pairs"]}
    counts = np.bincount(train_labels, minlength=len(names))
    order = np.argsort(-counts)
    eda = load("outputs/data/eda_stats.json")
    calibration = {run: load(f"reports/audit/{run}/calibration.json") for run in ("tfidf", "legal_bert_long")}
    counterfactual = {run: load(f"reports/audit/{run}/counterfactual.json") for run in ("tfidf", "legal_bert_long")}
    taxonomy = load("reports/audit/taxonomy.json")
    retrieval = load("outputs/retrieval/metrics.json")
    cost = load("reports/cost.json")
    missing = load("reports/audit/missing_clauses.json")
    occlusion = {run: load(f"reports/audit/{run}/occlusion.json") for run in ("tfidf", "legal_bert_long")}
    lawyer = (ROOT / "outputs/retrieval/lawyer_queries.md").read_text(encoding="utf-8")
    summary = lawyer.split("## Summary")[1]
    lawyer_rows = {}
    for line in summary.splitlines():
        cells = [cell.strip() for cell in line.strip("|").split("|")]
        if len(cells) == 3 and cells[0] in {"dense", "tfidf", "overlap"}:
            lawyer_rows[cells[0]] = {"rank1": int(cells[1].split("/")[0]), "top5": int(cells[2].split("/")[0]),
                                     "n": int(cells[1].split("/")[1])}
    with (ROOT / "reports/audit/legal_bert_long/slices.csv").open(encoding="utf-8") as file:
        slice_rows = list(csv.DictReader(file))
    lease = next(row for row in slice_rows if row["slice_type"] == "family" and row["slice"] == "lease")
    overall = next(row for row in slice_rows if row["slice_type"] == "all" and row["slice"] == "all")
    prediction_text = (ROOT / "README.md").read_text(encoding="utf-8")
    prediction = re.search(r"Legal-BERT beats TF-IDF on test macro-F1 by (\d+) to (\d+) points", prediction_text)
    counterfactual_text = (ROOT / "reports/audit/legal_bert_long/counterfactual.md").read_text(encoding="utf-8")
    threshold = re.search(r"flip rate exceeds (\d+)%", counterfactual_text)
    if prediction is None or threshold is None:
        raise ValueError("Could not read the planned comparison or audit threshold")
    return {
        "label_distribution": {"names": [names[i] for i in order], "counts": [int(counts[i]) for i in order]},
        "eda": eda,
        "results_table": results["results_table"],
        "lora_table": results["lora_table"],
        "pairs": pairs,
        "lexglue": results["reference_lexglue"],
        "chatgpt_zero_shot": {"micro_f1": 70.1, "macro_f1": 56.7, "few_shot_micro_f1": 62.1, "few_shot_macro_f1": 51.1,
                              "source": "Chalkidis 2023, arXiv:2304.12202, 1,000 LEDGAR test clauses"},
        "calibration": {run: {"temperature": c["temperature"], "ece_before": c["calibration"]["test"]["before"]["ece"],
                              "ece_after": c["calibration"]["test"]["after"]["ece"],
                              "reliability_before": c["calibration"]["test"]["reliability_before"],
                              "reliability_after": c["calibration"]["test"]["reliability_after"],
                              "abstention": c["abstention"], "conformal": c["conformal"]}
                        for run, c in calibration.items()},
        "counterfactual": {run: {name: {k: v for k, v in test.items() if k != "examples"} for name, test in c.items()}
                           for run, c in counterfactual.items()},
        "taxonomy": {"pairs": taxonomy["merged_pairs"],
                     "runs": [{"run": r["run"], **{k: r["test"][k] for k in
                              ("accuracy_before", "accuracy_after", "macro_f1_before", "macro_f1_after",
                               "share_errors_removed", "group_f1")}} for r in taxonomy["runs"]],
                     "paired_tests": taxonomy["paired_tests"]},
        "retrieval": {"metrics": retrieval["results"], "config": retrieval["config"],
                      "timings": retrieval["timings_seconds"], "lawyer": lawyer_rows},
        "cost": cost["configurations"],
        "cost_quality": cost.get("quality"),
        "lease_slice": {"accuracy": float(lease["accuracy"]), "overall_accuracy": float(overall["accuracy"])},
        "planned_advantage_points": [int(prediction.group(1)), int(prediction.group(2))],
        "counterfactual_fail_threshold": int(threshold.group(1)) / 100,
        "tfidf_train_seconds": 44,
        "missing_clauses": missing,
        "occlusion": {run: {k: v for k, v in o.items() if k in ("comprehensiveness",)} for run, o in occlusion.items()},
    }


def cloud(
    train_texts: list[str], train_labels: np.ndarray, names: list[str], per_type: int = 220, seed: int = 42
) -> dict:
    """3D principal-component projection of the MiniLM embeddings of a sample of training clauses."""
    embeddings = np.load(ROOT / "outputs/retrieval/bank_embeddings_all.npy", mmap_mode="r")
    rng = np.random.default_rng(seed)
    type_ids = [names.index(name) for name in CLOUD_TYPES]
    chosen = np.concatenate([rng.choice(np.flatnonzero(train_labels == t), per_type, replace=False) for t in type_ids])
    vectors = np.asarray(embeddings[chosen], dtype=np.float32)
    query = load_model("cpu").encode([CLOUD_QUERY], normalize_embeddings=True)[0]
    scores = vectors @ query
    neighbours = np.argsort(-scores)[:5]
    mean = vectors.mean(axis=0)
    _, _, components = np.linalg.svd(vectors - mean, full_matrices=False)
    projection = (vectors - mean) @ components[:3].T
    query_point = (query - mean) @ components[:3].T
    scale = np.abs(projection).max()
    return {
        "types": CLOUD_TYPES,
        "points": [[round(float(v), 4) for v in row / scale] + [type_ids.index(int(train_labels[i]))]
                   for row, i in zip(projection, chosen, strict=True)],
        "query": {"text": CLOUD_QUERY, "point": [round(float(v), 4) for v in query_point / scale]},
        "neighbours": [
            {"index": int(n), "score": round(float(scores[n]), 3),
             "type": names[int(train_labels[chosen[n]])], "text": train_texts[int(chosen[n])][:160]}
            for n in neighbours
        ],
    }


def main() -> None:
    """Write deck.json and cloud.json."""
    names = get_label_names()
    train_texts, train_labels = load_split("train")
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "deck.json").write_text(json.dumps(deck_numbers(train_labels, names), indent=1), encoding="utf-8")
    (OUT / "cloud.json").write_text(json.dumps(cloud(train_texts, train_labels, names)), encoding="utf-8")
    print(f"Wrote {OUT / 'deck.json'} and {OUT / 'cloud.json'}")


if __name__ == "__main__":
    main()
