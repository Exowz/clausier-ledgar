"""Review predicted contract clauses against frequent training clause types."""

import argparse
import re
from pathlib import Path

import numpy as np

from src.classification.run_io import load_run
from src.utils import ensure_dir, load_json, resolve_path, save_json, set_seed

DEFAULT_CHECKLIST_SIZE = 12


def _scale_temperature(probs: np.ndarray, temperature: float) -> np.ndarray:
    if temperature <= 0:
        raise ValueError("Temperature must be positive")
    logits = np.log(np.clip(np.asarray(probs, dtype=np.float64), 1e-12, None)) / temperature
    logits -= logits.max(axis=1, keepdims=True)
    exp_logits = np.exp(logits)
    return exp_logits / exp_logits.sum(axis=1, keepdims=True)


def checklist_from_train(train_labels: np.ndarray, label_names: list[str], size: int = 12) -> list[str]:
    """Return the most frequent training types, with label order breaking ties."""
    counts = np.bincount(np.asarray(train_labels, dtype=int), minlength=len(label_names))
    order = sorted(range(len(label_names)), key=lambda index: (-counts[index], index))
    return [label_names[index] for index in order[:size]]


def split_clauses(text: str, min_chars: int = 40) -> list[str]:
    """Split on blank lines and discard short pieces."""
    return [piece for part in re.split(r"\n\s*\n", text)
            if len(piece := part.strip()) >= min_chars]


def review(probs: np.ndarray, label_names: list[str], checklist: list[str], threshold: float) -> dict:
    """Mark clauses by confidence and checklist types as present, check, or missing."""
    values = np.asarray(probs)
    clauses = []
    for index, row in enumerate(values):
        predicted = int(row.argmax())
        confidence = float(row[predicted])
        clauses.append({"index": index, "type": label_names[predicted], "confidence": confidence,
                        "status": "confident" if confidence >= threshold else "check"})
    checklist_rows = []
    for type_name in checklist:
        matching = [row for row in clauses if row["type"] == type_name]
        status = ("present" if any(row["status"] == "confident" for row in matching)
                  else "check" if matching else "missing")
        checklist_rows.append({"type": type_name, "status": status,
                               "clauses": [row["index"] for row in matching]})
    return {"clauses": clauses, "checklist": checklist_rows}


def review_contract(text: str, classifier, label_names: list[str], checklist: list[str], threshold: float,
                    temperature: float = 1.0) -> dict:
    """Split a contract, scale clause probabilities, and return its checklist review."""
    clauses = split_clauses(text)
    if not clauses:
        return review(np.empty((0, len(label_names))), label_names, checklist, threshold)
    probs = np.asarray(classifier.predict_proba(clauses))
    scaled = _scale_temperature(probs, temperature) if temperature != 1.0 else probs
    result = review(scaled, label_names, checklist, threshold)
    for row, clause in zip(result["clauses"], clauses, strict=True):
        row["text"] = clause
    return result


def simulate_contracts(test_labels: np.ndarray, checklist_ids: list[int], n_contracts: int = 500,
                       keep_prob: float = 0.7, n_other: int = 10, seed: int = 42) -> list[dict]:
    """Sample checklist and other test clauses into reproducible simulated contracts."""
    labels = np.asarray(test_labels)
    rng = np.random.default_rng(seed)
    pools = {type_id: np.flatnonzero(labels == type_id) for type_id in checklist_ids}
    others = np.flatnonzero(~np.isin(labels, checklist_ids))
    if any(len(pool) == 0 for pool in pools.values()) or (n_other and len(others) == 0):
        raise ValueError("Every requested type and the other pool must have test clauses")
    contracts = []
    for _ in range(n_contracts):
        indices, present = [], []
        for type_id in checklist_ids:
            if rng.random() < keep_prob:
                indices.append(int(rng.choice(pools[type_id])))
                present.append(int(type_id))
        indices.extend(int(index) for index in rng.choice(others, size=n_other, replace=True))
        contracts.append({"indices": indices, "present_types": present})
    return contracts


def evaluate_simulation(contracts: list[dict], test_probs: np.ndarray, test_labels: np.ndarray,
                        label_names: list[str], checklist: list[str], threshold: float) -> dict:
    """Measure missing flag precision and recall, check share, and present-type outcomes."""
    checklist_ids = [label_names.index(type_name) for type_name in checklist]
    true_missing = predicted_missing = correctly_missing = checks = 0
    present_outcomes = {"present": 0, "check": 0, "missing": 0}
    for contract in contracts:
        indices = contract["indices"]
        prediction = review(np.asarray(test_probs)[indices], label_names, checklist, threshold)
        true_types = set(int(test_labels[index]) for index in indices)
        for type_id, row in zip(checklist_ids, prediction["checklist"], strict=True):
            absent = type_id not in true_types
            flagged = row["status"] == "missing"
            true_missing += absent
            predicted_missing += flagged
            correctly_missing += absent and flagged
            checks += row["status"] == "check"
            if not absent:
                present_outcomes[row["status"]] += 1
    total = len(contracts) * len(checklist)
    present_total = sum(present_outcomes.values())
    return {"missing_precision": correctly_missing / predicted_missing if predicted_missing else 0.0,
            "missing_recall": correctly_missing / true_missing if true_missing else 0.0,
            "check_share": checks / total if total else 0.0,
            "truly_present": {key: count / present_total if present_total else 0.0
                              for key, count in present_outcomes.items()},
            "n_pairs": total}


def main(argv=None) -> None:
    """Evaluate missing-clause flags using saved probabilities and simulated contracts."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--runs", nargs="+", type=Path, required=True)
    parser.add_argument("--n-contracts", type=int, default=500)
    parser.add_argument("--keep-prob", type=float, default=0.7)
    parser.add_argument("--threshold-from", type=Path)
    parser.add_argument("--out", type=Path, default=Path("reports/audit"))
    args = parser.parse_args(argv)
    if args.n_contracts <= 0 or not 0 <= args.keep_prob <= 1:
        parser.error("n-contracts must be positive and keep-prob must be in [0, 1]")
    set_seed(42)
    from src.data import load_ledgar

    dataset = load_ledgar()
    train_labels = np.asarray(dataset["train"]["label"])
    label_names = list(dataset["train"].features["label"].names)
    checklist = checklist_from_train(train_labels, label_names, DEFAULT_CHECKLIST_SIZE)
    checklist_ids = [label_names.index(name) for name in checklist]
    runs = []
    for run_path in args.runs:
        run = load_run(run_path)
        if run["metrics"]["label_names"] != label_names:
            raise ValueError(f"Label names differ for {run_path}")
        calibration_path = (resolve_path(args.threshold_from) if args.threshold_from else
                            resolve_path(args.out) / run_path.name / "calibration.json")
        calibration = load_json(calibration_path) if calibration_path.is_file() else None
        threshold = float(calibration["abstention"]["threshold"]) if calibration else 0.0
        temperature = float(calibration["temperature"]) if calibration else 1.0
        probs = (_scale_temperature(run["test_probs"], temperature)
                 if temperature != 1.0 else run["test_probs"])
        contracts = simulate_contracts(run["test_labels"], checklist_ids, args.n_contracts,
                                       args.keep_prob, seed=42)
        metrics = evaluate_simulation(contracts, probs, run["test_labels"], label_names,
                                      checklist, threshold)
        runs.append({"run": run_path.name, "threshold": threshold, "temperature": temperature, **metrics})
    payload = {"checklist": checklist, "settings": {"n_contracts": args.n_contracts,
               "keep_prob": args.keep_prob, "n_other": 10, "seed": 42}, "runs": runs,
               "limit": "Simulated contracts are sets of real test clauses; splitting a real contract into "
                        "clauses is not evaluated."}
    output = ensure_dir(args.out)
    save_json(payload, output / "missing_clauses.json")
    lines = ["# Missing clause review", "", "Checklist: " + ", ".join(checklist) + ".", "",
             f"Simulation: {args.n_contracts} contracts; checklist keep probability {args.keep_prob:.2f}; "
             "10 other clauses per contract; seed 42.", ""]
    for result in runs:
        present = result["truly_present"]
        lines.extend([f"## {result['run']}", "",
                      f"Temperature: {result['temperature']:.3f}; confidence threshold: "
                      f"{result['threshold']:.3f}.", "",
                      "| Missing precision | Missing recall | Sent to check | Truly present: present | "
                      "Truly present: check | Truly present: missing |",
                      "| ---: | ---: | ---: | ---: | ---: | ---: |",
                      f"| {result['missing_precision']:.3f} | {result['missing_recall']:.3f} | "
                      f"{result['check_share']:.3f} | {present['present']:.3f} | "
                      f"{present['check']:.3f} | {present['missing']:.3f} |", ""])
    lines.extend([payload["limit"], ""])
    markdown = "\n".join(lines)
    (output / "missing_clauses.md").write_text(markdown, encoding="utf-8")
    print(markdown, end="")


if __name__ == "__main__":
    main()
