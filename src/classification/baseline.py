"""TF-IDF and multinomial logistic regression baseline for LEDGAR."""

import argparse
from pathlib import Path
from time import perf_counter

import joblib
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression

from src.classification.metrics import evaluate
from src.classification.run_io import save_run
from src.data import get_label_names, load_split
from src.utils import ensure_dir, load_yaml, resolve_path, save_json, set_seed


class TfidfClassifier:
    """Word unigram and bigram TF-IDF followed by logistic regression."""

    def __init__(
        self, ngram_range: tuple[int, int] = (1, 2), min_df: int = 2, max_features: int = 200_000,
        sublinear_tf: bool = True, C: float = 10.0, max_iter: int = 1000,
        class_weight: str | None = None, n_classes: int = 100, seed: int = 42,
    ) -> None:
        """Configure the vectorizer and multinomial classifier."""
        self.n_classes = n_classes
        self.vectorizer = TfidfVectorizer(
            ngram_range=ngram_range, min_df=min_df, max_features=max_features, sublinear_tf=sublinear_tf,
        )
        self.classifier = LogisticRegression(
            C=C, max_iter=max_iter, class_weight=class_weight, random_state=seed,
            solver="saga", tol=0.01,
        )

    def fit(self, texts: list[str], labels: np.ndarray) -> "TfidfClassifier":
        """Fit TF-IDF on training texts and logistic regression on their labels."""
        features = self.vectorizer.fit_transform(texts)
        self.classifier.fit(features, labels)
        return self

    def predict_proba(self, texts: list[str]) -> np.ndarray:
        """Return float32 probabilities in numeric label order, including absent classes."""
        features = self.vectorizer.transform(texts)
        observed_probs = self.classifier.predict_proba(features)
        probs = np.zeros((len(texts), self.n_classes), dtype=np.float32)
        probs[:, self.classifier.classes_] = observed_probs
        return probs

    def save(self, path: str | Path) -> None:
        """Save the fitted vectorizer and classifier with joblib."""
        target = resolve_path(path)
        ensure_dir(target.parent)
        joblib.dump(self, target)

    @classmethod
    def load(cls, path: str | Path) -> "TfidfClassifier":
        """Load a fitted classifier from a joblib file."""
        return joblib.load(resolve_path(path))


def _make_model(config: dict, n_classes: int) -> TfidfClassifier:
    return TfidfClassifier(
        ngram_range=tuple(config["ngram_range"]), min_df=config["min_df"],
        max_features=config["max_features"], sublinear_tf=config["sublinear_tf"],
        C=config["C"], max_iter=config["max_iter"], class_weight=config["class_weight"],
        n_classes=n_classes, seed=config["seed"],
    )


def _fit_timed(model: TfidfClassifier, texts: list[str], labels: np.ndarray) -> float:
    start = perf_counter()
    model.fit(texts, labels)
    return perf_counter() - start


def main() -> None:
    """Fit the baseline, optionally tune on validation, and save a standard run."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", default="configs/tfidf.yaml")
    parser.add_argument("--tune", action="store_true")
    parser.add_argument("--output-dir", default="outputs")
    args = parser.parse_args()

    config = load_yaml(args.config)
    config = {**config, "solver": "saga", "tol": 0.01}
    set_seed(config["seed"])
    train_texts, train_labels = load_split("train")
    val_texts, val_labels = load_split("validation")
    test_texts, test_labels = load_split("test")
    label_names = get_label_names()
    run_dir = ensure_dir(Path(args.output_dir) / config["run_name"])

    if args.tune:
        rows = []
        for C in config.get("tune_C", [1, 10, 30]):
            for class_weight in (None, "balanced"):
                candidate_config = {**config, "C": C, "class_weight": class_weight}
                candidate = _make_model(candidate_config, len(label_names))
                fit_time_s = _fit_timed(candidate, train_texts, train_labels)
                val_probs = candidate.predict_proba(val_texts)
                val_macro_f1 = evaluate(val_probs, val_labels, label_names)["macro_f1"]
                rows.append({
                    "C": C, "class_weight": class_weight, "val_macro_f1": val_macro_f1,
                    "fit_time_s": fit_time_s,
                })
                print(
                    f"C={C}, class_weight={class_weight}: val macro-F1={val_macro_f1:.4f}, "
                    f"fit={fit_time_s:.1f}s", flush=True,
                )
        save_json(rows, run_dir / "tuning.json")
        best = max(rows, key=lambda row: row["val_macro_f1"])
        config = {**config, "C": best["C"], "class_weight": best["class_weight"]}

    model = _make_model(config, len(label_names))
    train_time_s = _fit_timed(model, train_texts, train_labels)
    val_probs = model.predict_proba(val_texts)
    test_probs = model.predict_proba(test_texts)
    metrics = save_run(
        run_dir, config, val_probs, val_labels, test_probs, test_labels,
        label_names, extra_metrics={"train_time_s": train_time_s},
    )
    model.save(run_dir / "model.joblib")
    for split in ("validation", "test"):
        result = metrics[split]
        print(
            f"{split}: accuracy={result['accuracy']:.4f}, macro-F1={result['macro_f1']:.4f}, "
            f"micro-F1={result['micro_f1']:.4f}",
        )
    if "test_dedup" in metrics:
        print(f"test_dedup: macro-F1={metrics['test_dedup']['macro_f1']:.4f}")


if __name__ == "__main__":
    # Run main from the package module so that joblib pickles TfidfClassifier as
    # src.classification.baseline.TfidfClassifier, not __main__.TfidfClassifier.
    from src.classification.baseline import main as package_main

    package_main()
