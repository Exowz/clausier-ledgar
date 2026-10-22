"""Explain clause predictions by erasing words and measure comprehensiveness."""

import argparse
import re
from pathlib import Path

import numpy as np

from src.classification.predict import load_classifier
from src.data import load_ledgar
from src.utils import ensure_dir, save_json, set_seed


def words_with_spans(text: str) -> list[tuple[str, int, int]]:
    """Return whitespace-separated words and their character offsets."""
    return [(match.group(), match.start(), match.end()) for match in re.finditer(r"\S+", text)]


def explain(classifier, text: str, label: int | None = None, max_words: int = 200,
            batch_size: int = 64) -> dict:
    """Return probability drops when each of the first max_words words is erased.

    The classifier handles prediction batches. All variants are passed to it in one call.
    """
    if max_words < 0 or batch_size <= 0:
        raise ValueError("max_words must be nonnegative and batch_size must be positive")
    spans = words_with_spans(text)
    words = [word for word, _, _ in spans]
    variants = [" ".join(words)]
    variants.extend(" ".join(words[:index] + words[index + 1:])
                    for index in range(min(max_words, len(words))))
    probs = np.asarray(classifier.predict_proba(variants))
    selected = int(probs[0].argmax()) if label is None else int(label)
    probability = float(probs[0, selected])
    rows = [{"word": word, "start": int(start), "end": int(end),
             "importance": probability - float(probs[index + 1, selected])}
            for index, (word, start, end) in enumerate(spans[:max_words])]
    return {"label": selected, "probability": probability, "words": rows}


def comprehensiveness(classifier, texts: list[str], k: int = 3, seed: int = 42) -> dict:
    """Compare probability drops and prediction changes after top-k and random erasure."""
    if k < 0:
        raise ValueError("k must be nonnegative")
    rng = np.random.default_rng(seed)
    explanations = [explain(classifier, text) for text in texts]
    variants = []
    for text, result in zip(texts, explanations, strict=True):
        words = [word for word, _, _ in words_with_spans(text)]
        count = min(k, len(result["words"]))
        ranked = sorted(range(len(result["words"])),
                        key=lambda index: result["words"][index]["importance"], reverse=True)
        top = set(ranked[:count])
        random = set(int(index) for index in rng.choice(len(words), size=count, replace=False))
        variants.extend([" ".join(word for index, word in enumerate(words) if index not in removed)
                         for removed in (top, random)])
    changed = np.asarray(classifier.predict_proba(variants)) if variants else np.empty((0, 0))
    top_drops, random_drops = [], []
    top_changed, random_changed = [], []
    for index, result in enumerate(explanations):
        label = result["label"]
        top_probs, random_probs = changed[2 * index:2 * index + 2]
        top_drops.append(float(result["probability"] - top_probs[label]))
        random_drops.append(float(result["probability"] - random_probs[label]))
        top_changed.append(bool(top_probs.argmax() != label))
        random_changed.append(bool(random_probs.argmax() != label))
    return {"mean_top_k_drop": float(np.mean(top_drops)) if top_drops else 0.0,
            "mean_random_drop": float(np.mean(random_drops)) if random_drops else 0.0,
            "top_k_changed_share": float(np.mean(top_changed)) if top_changed else 0.0,
            "random_changed_share": float(np.mean(random_changed)) if random_changed else 0.0,
            "top_k_drops": top_drops, "random_drops": random_drops,
            "top_k_changed": top_changed, "random_changed": random_changed}


def _bold_words(text: str, selected: set[int]) -> str:
    pieces = []
    cursor = 0
    for index, (_, start, end) in enumerate(words_with_spans(text)):
        pieces.append(text[cursor:start])
        piece = text[start:end]
        pieces.append(f"**{piece}**" if index in selected else piece)
        cursor = end
    pieces.append(text[cursor:])
    return "".join(pieces)


def main(argv=None) -> None:
    """Write word-erasure explanations and comprehensiveness for sampled test clauses."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run", type=Path, required=True)
    parser.add_argument("--n", type=int, default=200)
    parser.add_argument("--k", type=int, default=3)
    parser.add_argument("--examples", type=int, default=5)
    parser.add_argument("--out", type=Path, default=Path("reports/audit"))
    args = parser.parse_args(argv)
    if not 0 < args.n <= 10_000 or args.k < 0 or args.examples < 0:
        parser.error("n must be in 1..10000; k and examples must be nonnegative")
    set_seed(42)
    dataset = load_ledgar()
    test = dataset["test"]
    if len(test) != 10_000:
        raise ValueError("Expected 10,000 LEDGAR test clauses")
    label_names = dataset["train"].features["label"].names
    indices = np.sort(np.random.default_rng(42).choice(10_000, args.n, replace=False))
    texts = [test[int(index)]["text"] for index in indices]
    classifier = load_classifier(args.run)
    faithfulness = comprehensiveness(classifier, texts, k=args.k)
    examples = []
    for index, text in zip(indices[:args.examples], texts[:args.examples], strict=True):
        result = explain(classifier, text)
        ranked = sorted(enumerate(result["words"]), key=lambda pair: pair[1]["importance"], reverse=True)[:8]
        examples.append({"test_index": int(index), "text": text, "label": result["label"],
                         "type": label_names[result["label"]], "probability": result["probability"],
                         "top_words": [word for _, word in ranked],
                         "highlighted_clause": _bold_words(text, {position for position, _ in ranked})})
    payload = {"run": args.run.name, "n": args.n, "k": args.k, "seed": 42,
               "test_indices": [int(index) for index in indices], "comprehensiveness": faithfulness,
               "examples": examples}
    output = ensure_dir(args.out / args.run.name)
    save_json(payload, output / "occlusion.json")
    lines = [f"# Word erasure: {args.run.name}", "",
             f"Sample: {args.n} test clauses; k = {args.k}; seed = 42.", "",
             "Importance is the predicted type probability before erasure minus its probability after erasure.", "",
             "| Removal | Mean probability drop | Share with changed prediction |",
             "| --- | ---: | ---: |",
             f"| Top {args.k} words | {faithfulness['mean_top_k_drop']:.3f} | "
             f"{faithfulness['top_k_changed_share']:.3f} |",
             f"| {args.k} random words | {faithfulness['mean_random_drop']:.3f} | "
             f"{faithfulness['random_changed_share']:.3f} |", ""]
    for number, example in enumerate(examples, 1):
        lines.extend([f"## Example {number} (test index {example['test_index']})", "",
                      f"Predicted type: {example['type']} (probability {example['probability']:.3f}).", "",
                      "| Word | Importance |", "| --- | ---: |"])
        lines.extend(f"| {word['word']} | {word['importance']:.3f} |" for word in example["top_words"])
        lines.extend(["", example["highlighted_clause"], ""])
    (output / "occlusion.md").write_text("\n".join(lines), encoding="utf-8")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
