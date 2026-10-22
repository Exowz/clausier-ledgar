"""Adapters between saved project artifacts and the demo's JSON responses."""

import json
import threading
from difflib import SequenceMatcher
from pathlib import Path

import numpy as np

from src.utils import PROJECT_ROOT

NOT_AVAILABLE = "not available"


class Services:
    """Load saved models and the clause bank once per app instance."""

    def __init__(self, root: Path = PROJECT_ROOT) -> None:
        """Set the artifact root without loading models or data."""
        self.root = Path(root)
        self._lock = threading.Lock()
        self._classifiers: dict = {}
        self._label_names: list[str] | None = None
        self._bank: tuple[list[str], np.ndarray] | None = None
        self._indexes: dict = {}
        self._minilm = None
        self._checklist: list[str] | None = None

    def models(self) -> list[dict]:
        """List classifier artifacts that are present on disk."""
        rows = []
        if (self.root / "outputs/tfidf/model.joblib").is_file():
            rows.append({"id": "tfidf", "name": "TF-IDF + logistic regression", "recommended": True})
        if (self.root / "outputs/legal_bert_long/model").is_dir():
            rows.append({"id": "legal_bert_long", "name": "Legal-BERT (long)", "recommended": False})
        return rows

    def _classifier(self, model: str):
        if model not in self._classifiers:
            with self._lock:
                if model not in self._classifiers:
                    from src.classification.predict import load_classifier

                    self._classifiers[model] = load_classifier(self.root / "outputs" / model)
        return self._classifiers[model]

    def _labels(self) -> list[str]:
        if self._label_names is None:
            with self._lock:
                if self._label_names is None:
                    from src.data import get_label_names

                    self._label_names = get_label_names()
        return self._label_names

    def _training_bank(self) -> tuple[list[str], np.ndarray]:
        if self._bank is None:
            with self._lock:
                if self._bank is None:
                    from src.data import load_split

                    self._bank = load_split("train")
        return self._bank

    def _calibration(self, model: str) -> dict:
        data = self._read_json(f"reports/audit/{model}/calibration.json")
        return data if isinstance(data, dict) else {}

    def _read_json(self, path: str):
        file = self.root / path
        if not file.is_file():
            return NOT_AVAILABLE
        return json.loads(file.read_text(encoding="utf-8"))

    def _prediction(self, text: str, model: str) -> tuple[np.ndarray, int]:
        from src.audit.calibration import apply_temperature

        raw = np.asarray(self._classifier(model).predict_proba([text]))
        temperature = float(self._calibration(model).get("temperature", 1.0))
        probabilities = apply_temperature(raw, temperature)[0]
        return probabilities, int(probabilities.argmax())

    def classify(self, text: str, model: str, explain: bool = True) -> dict:
        """Predict a clause type with calibration, abstention, and word importance."""
        from src.audit.calibration import prediction_sets

        names = self._labels()
        probabilities, label = self._prediction(text, model)
        calibration = self._calibration(model)
        abstention = calibration.get("abstention", {})
        threshold = float(abstention.get("threshold", 0.0))
        q_hat = calibration.get("conformal", {}).get("q_hat")
        members = (prediction_sets(probabilities[None, :], float(q_hat))[0].tolist()
                   if q_hat is not None else [])
        top = np.argsort(-probabilities)[:3]
        result = {
            "text": text, "model": model, "type": names[label],
            "confidence": float(probabilities[label]), "threshold": threshold,
            "target_accuracy": abstention.get("target_accuracy"),
            "status": "handled" if probabilities[label] >= threshold else "check",
            "conformal_set": [names[index] for index in members],
            "top_types": [{"type": names[index], "probability": float(probabilities[index])}
                          for index in top],
            "explanation": [],
        }
        if explain:
            from src.audit.occlusion import explain as occlusion_explain

            result["explanation"] = occlusion_explain(
                self._classifier(model), text, label=label, max_words=200,
            )["words"]
        return result

    def _index(self, method: str):
        if method not in self._indexes:
            with self._lock:
                if method not in self._indexes:
                    from src.retrieval.index import DenseIndex, OverlapIndex, TfidfIndex, embed, load_model

                    texts, _ = self._training_bank_unlocked()
                    if method == "dense":
                        if self._minilm is None:
                            self._minilm = load_model()
                        vectors = embed(texts, self._minilm,
                                        self.root / "outputs/retrieval/bank_embeddings_all.npy")
                        self._indexes[method] = DenseIndex(vectors, self._minilm)
                    elif method == "tfidf":
                        self._indexes[method] = TfidfIndex(texts)
                    else:
                        self._indexes[method] = OverlapIndex(texts)
        return self._indexes[method]

    def _training_bank_unlocked(self) -> tuple[list[str], np.ndarray]:
        if self._bank is None:
            from src.data import load_split

            self._bank = load_split("train")
        return self._bank

    def search(self, query: str, method: str = "dense", k: int = 5) -> dict:
        """Search the training clause bank, respecting day durations in the query."""
        from src.retrieval.index import search_with_days

        index = self._index(method)
        texts, labels = self._training_bank()
        names = self._labels()
        matches, days = search_with_days(index, query, texts, k=k)
        return {"method": method, "filtered_days": sorted(days), "results": [
            {"rank": rank, "score": score, "type": names[int(labels[position])],
             "text": texts[position]}
            for rank, (position, score) in enumerate(matches, 1)
        ]}

    def review(self, text: str, model: str) -> dict:
        """Review a contract against the standard training clause checklist."""
        from src.review.checklist import checklist_from_train, review_contract

        names = self._labels()
        if self._checklist is None:
            with self._lock:
                if self._checklist is None:
                    self._checklist = checklist_from_train(self._training_bank_unlocked()[1], names)
        calibration = self._calibration(model)
        result = review_contract(
            text, self._classifier(model), names, self._checklist,
            float(calibration.get("abstention", {}).get("threshold", 0.0)),
            float(calibration.get("temperature", 1.0)),
        )
        missing = [row["type"] for row in result["checklist"] if row["status"] == "missing"]
        found = sum(row["status"] != "missing" for row in result["checklist"])
        result["summary"] = {"clauses": len(result["clauses"]), "found": found,
                             "missing": missing}
        return result

    @staticmethod
    def _changed_words(original: str, edited: str) -> list[int]:
        before, after = original.split(), edited.split()
        matcher = SequenceMatcher(a=before, b=after)
        return [index for operation, _, _, start, end in matcher.get_opcodes()
                if operation != "equal" for index in range(start, end)]

    def stress(self, text: str, model: str) -> dict:
        """Compare each applicable audit edit and its control with the original."""
        from src.audit.perturbations import EDITS

        names = self._labels()
        classifier = self._classifier(model)
        cases = [(name, edit(text), control(text)) for name, (edit, control) in EDITS.items()]
        variants = [text] + [variant for _, edited, controlled in cases
                             if edited is not None and edited != text
                             for variant in (edited, controlled or text)]
        predictions = np.asarray(classifier.predict_proba(variants)).argmax(axis=1)
        original = names[int(predictions[0])]
        rows = []
        offset = 1
        for name, edited, controlled in cases:
            applies = edited is not None and edited != text
            row = {"name": name, "applies": applies}
            if applies:
                after = names[int(predictions[offset])]
                control = names[int(predictions[offset + 1])]
                row.update({"edited_text": edited, "control_text": controlled or text,
                            "changed_words": self._changed_words(text, edited),
                            "before": original, "after": after, "control": control,
                            "edit_status": "unchanged" if after == original else "changed",
                            "control_status": "unchanged" if control == original else "changed"})
                offset += 2
            rows.append(row)
        return {"original": text, "prediction": original, "edits": rows}

    def evidence(self) -> dict:
        """Read existing evidence files, leaving missing sections available to the page."""
        results = self._read_json("reports/results.json")
        retrieval = self._read_json("outputs/retrieval/metrics.json")
        cost = self._read_json("reports/cost.json")
        paired = (next((row for row in results.get("pairs", [])
                        if row.get("question") == "main comparison"), NOT_AVAILABLE)
                  if isinstance(results, dict) else NOT_AVAILABLE)
        return {
            "results": results.get("results_table", NOT_AVAILABLE)
            if isinstance(results, dict) else NOT_AVAILABLE,
            "paired_test": paired,
            "calibration": {run: self._read_json(f"reports/audit/{run}/calibration.json")
                            for run in ("tfidf", "legal_bert_long")},
            "retrieval": retrieval.get("results", NOT_AVAILABLE)
            if isinstance(retrieval, dict) else NOT_AVAILABLE,
            "cost": cost.get("configurations", NOT_AVAILABLE)
            if isinstance(cost, dict) else NOT_AVAILABLE,
        }

    def sample_contract(self) -> str:
        """Return the bundled sample contract text."""
        path = self.root / "data/sample_contract.txt"
        return path.read_text(encoding="utf-8") if path.is_file() else ""

    def preload(self) -> None:
        """Warm the classifiers, labels, clause bank, and dense retrieval index."""
        self._labels()
        self._training_bank()
        self._classifier("tfidf")
        self._index("dense")
        if any(row["id"] == "legal_bert_long" for row in self.models()):
            self._classifier("legal_bert_long")
