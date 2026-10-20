"""CLI for LEDGAR labels, token lengths, overlap, and slice summaries."""

import argparse

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402

from src.data import SPLITS, count_tokens, find_overlap, load_ledgar, slice_frame  # noqa: E402
from src.utils import ensure_dir, save_json, set_seed  # noqa: E402

LEGAL_BERT = "nlpaueb/legal-bert-base-uncased"
DEFAULT_TOKENIZERS = (LEGAL_BERT, "bert-base-uncased")


def _token_stats(counts: np.ndarray) -> dict:
    """Summarize raw counts, with the course rule that lengths above a limit truncate."""
    if len(counts) == 0:
        return {"median": None, "p90": None, "p95": None, "p99": None, "max": None,
                "share_truncated": {str(limit): None for limit in (128, 256, 512)}}
    return {
        "median": float(np.median(counts)),
        "p90": float(np.percentile(counts, 90)),
        "p95": float(np.percentile(counts, 95)),
        "p99": float(np.percentile(counts, 99)),
        "max": int(np.max(counts)),
        "share_truncated": {str(limit): float(np.mean(counts > limit)) for limit in (128, 256, 512)},
    }


def _plot_labels(counts: dict[str, int]) -> None:
    ordered = sorted(counts.items(), key=lambda item: item[1])
    names, values = zip(*ordered, strict=True)
    plt.rcParams.update({"font.size": 12})
    fig, ax = plt.subplots(figsize=(11, 20))
    ax.barh(names, values, color="#346885")
    ax.set_xscale("log")
    ax.set_xlim(left=0.8)
    ax.set_title("LEDGAR train: clauses per label (log scale)")
    ax.set_xlabel("Clauses (log scale)")
    ax.set_ylabel("Label")
    ax.tick_params(axis="y", labelsize=10)
    fig.tight_layout()
    fig.savefig(ensure_dir("reports/figures") / "label_distribution.png", dpi=180)
    plt.close(fig)


def _plot_lengths(counts: np.ndarray) -> None:
    plt.rcParams.update({"font.size": 12})
    fig, ax = plt.subplots(figsize=(10, 6))
    ax.hist(counts, bins=100, color="#346885", edgecolor="none")
    for limit, color in ((128, "#e69f00"), (256, "#d55e00"), (512, "#7b3294")):
        share = np.mean(counts > limit)
        ax.axvline(limit, color=color, linewidth=2, label=f">{limit}: {share:.1%} truncated")
    ax.set_xlim(0, max(600, float(np.percentile(counts, 99))))
    ax.set_title("LEDGAR train: legal BERT token lengths (through p99)")
    ax.set_xlabel("Tokens, including special tokens")
    ax.set_ylabel("Clauses")
    ax.legend()
    fig.tight_layout()
    fig.savefig(ensure_dir("reports/figures") / "token_lengths.png", dpi=180)
    plt.close(fig)


def main() -> None:
    """Generate the EDA JSON, CSV, mask, figures, and short console summary."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--tokenizers", nargs="+", default=list(DEFAULT_TOKENIZERS))
    parser.add_argument("--near-threshold", type=float, default=0.9)
    parser.add_argument("--sample", type=int, help="Seeded random sample size per split for a quick check")
    args = parser.parse_args()
    if args.sample is not None and args.sample <= 0:
        parser.error("--sample must be positive")
    set_seed(42)

    dataset = load_ledgar()
    label_names = list(dataset["train"].features["label"].names)
    split_data = {}
    for split in SPLITS:
        data = dataset[split]
        if args.sample is not None:
            data = data.shuffle(seed=42).select(range(min(args.sample, len(data))))
        split_data[split] = (list(data["text"]), np.asarray(data["label"], dtype=np.int64))

    label_counts = {}
    for split, (_, labels) in split_data.items():
        counts = np.bincount(labels, minlength=len(label_names))
        label_counts[split] = {name: int(counts[index]) for index, name in enumerate(label_names)}
    train_counts = label_counts["train"]
    ordered_labels = sorted(train_counts.items(), key=lambda item: (item[1], item[0]))
    positive_counts = [count for count in train_counts.values() if count > 0]
    imbalance_ratio = max(positive_counts) / min(positive_counts) if positive_counts else None

    train_texts = split_data["train"][0]
    test_texts = split_data["test"][0]
    tokenizers = list(dict.fromkeys([*args.tokenizers, LEGAL_BERT]))
    tokenizer_stats = {}
    legal_train_counts = None
    legal_test_counts = None
    for name in tokenizers:
        train_lengths = count_tokens(train_texts, name)
        test_lengths = count_tokens(test_texts, name)
        tokenizer_stats[name] = {"train": _token_stats(train_lengths), "test": _token_stats(test_lengths)}
        if name == LEGAL_BERT:
            legal_train_counts = train_lengths
            legal_test_counts = test_lengths

    overlap = find_overlap(train_texts, test_texts, near_threshold=args.near_threshold)
    overlap.insert(0, "test_idx", np.arange(len(overlap)))
    output_dir = ensure_dir("outputs/data")
    overlap.to_csv(output_dir / "test_overlap.csv", index=False)
    np.save(output_dir / "test_dedup_mask.npy", overlap["keep"].to_numpy(dtype=bool))

    slices = slice_frame(test_texts, n_tokens=legal_test_counts, max_len=256)
    stats = {
        "split_sizes": {split: len(texts) for split, (texts, _) in split_data.items()},
        "label_counts": label_counts,
        "train_labels": {
            "most_frequent": [{"label": name, "count": count} for name, count in reversed(ordered_labels[-5:])],
            "least_frequent": [{"label": name, "count": count} for name, count in ordered_labels[:5]],
            "imbalance_ratio": imbalance_ratio,
        },
        "tokenizers": tokenizer_stats,
        "overlap": {
            "exact_duplicates": int(overlap["exact_dup"].sum()),
            "near_duplicates": int(overlap["near_dup"].sum()),
            "kept": int(overlap["keep"].sum()),
            "near_threshold": args.near_threshold,
        },
        "test_slices": {
            column: {str(key): int(value) for key, value in slices[column].value_counts().items()}
            for column in slices.columns
        },
    }
    save_json(stats, output_dir / "eda_stats.json")
    _plot_labels(train_counts)
    _plot_lengths(legal_train_counts)

    truncation = tokenizer_stats[LEGAL_BERT]["train"]["share_truncated"]
    print("LEDGAR splits: " + ", ".join(f"{name}={size}" for name, size in stats["split_sizes"].items()))
    print(f"Train imbalance ratio: {imbalance_ratio:.2f}")
    print(f"Legal BERT train truncation: 256={truncation['256']:.1%}, 512={truncation['512']:.1%}")
    print(f"Test overlap: exact={stats['overlap']['exact_duplicates']}, "
          f"near={stats['overlap']['near_duplicates']}, kept={stats['overlap']['kept']}")


if __name__ == "__main__":
    main()
