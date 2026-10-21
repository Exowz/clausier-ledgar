"""Counterfactual edits and controls for saved classifiers."""

import argparse
import re
from collections.abc import Callable
from pathlib import Path

import numpy as np

from src.classification.predict import load_classifier
from src.data import get_label_names, load_split
from src.utils import ensure_dir, resolve_path, save_json, set_seed

_ROLE_SWAPS = {
    "buyer": "seller", "seller": "buyer",
    "licensor": "licensee", "licensee": "licensor",
    "landlord": "tenant", "tenant": "landlord",
    "borrower": "lender", "lender": "borrower",
    "employer": "employee", "employee": "employer",
}
_ROLE_RENAMES = {
    "buyer": "purchaser", "seller": "vendor",
    "licensor": "grantor", "licensee": "grantee",
    "landlord": "lessor", "tenant": "lessee",
    "borrower": "obligor", "lender": "creditor",
    "employer": "company", "employee": "staff member",
}
_ROLE_PATTERN = re.compile(r"\b(?P<role>" + "|".join(_ROLE_SWAPS) + r")(?P<plural>s?)\b", re.IGNORECASE)
_STATE_PATTERN = re.compile(r"\b(?:(?P<the>[Tt]he)\s+)?State\s+of\s+(?:New York|Delaware)\b")
_PLACE_PATTERN = re.compile(r"\b(?:New York|Delaware)\b")

_ONES = ("", "one", "two", "three", "four", "five", "six", "seven", "eight", "nine")
_TEENS = ("ten", "eleven", "twelve", "thirteen", "fourteen", "fifteen", "sixteen", "seventeen",
          "eighteen", "nineteen")
_TENS = ("", "", "twenty", "thirty", "forty", "fifty", "sixty", "seventy", "eighty", "ninety")
_ONE_WORD = "(?:" + "|".join(_ONES[1:]) + ")"
_SMALL_WORD = rf"(?:{'|'.join(_TEENS)}|(?:{'|'.join(_TENS[2:])})(?:-{_ONE_WORD})?|{_ONE_WORD})"
_NUMBER_WORD = rf"(?:{_ONE_WORD} hundred(?: {_SMALL_WORD})?|{_SMALL_WORD})"
_UNIT = r"(?:business\s+days?|days?|months?|years?)"
_DURATION_PATTERN = re.compile(
    rf"\b(?P<words>{_NUMBER_WORD})\s*\((?P<paired_digits>[1-9]\d{{0,2}})\)\s+"
    rf"(?P<paired_unit>{_UNIT})\b|\b(?P<bare_digits>[1-9]\d{{0,2}})\s+(?P<bare_unit>{_UNIT})\b",
    re.IGNORECASE,
)


def _match_case(source: str, replacement: str) -> str:
    if source.isupper():
        return replacement.upper()
    if source[0].isupper():
        return replacement.title()
    return replacement


def _replace_roles(text: str, mapping: dict[str, str]) -> str | None:
    def replace(match: re.Match[str]) -> str:
        role = match.group("role")
        plural = match.group("plural")
        replacement = mapping[role.lower()] + ("s" if plural else "")
        return _match_case(role, replacement)

    edited, count = _ROLE_PATTERN.subn(replace, text)
    return edited if count else None


def swap_roles(text: str) -> str | None:
    """Swap each paired party role in a single regex pass."""
    return _replace_roles(text, _ROLE_SWAPS)


def rename_roles(text: str) -> str | None:
    """Rename each party with its same-role control term."""
    return _replace_roles(text, _ROLE_RENAMES)


def _replace_jurisdiction(text: str, non_us: bool) -> str | None:
    state_replacement = "England and Wales" if non_us else "State of Illinois"
    place_replacement = "England and Wales" if non_us else "Illinois"
    edited, state_count = _STATE_PATTERN.subn(
        lambda match: (match.group("the") + " " if match.group("the") and not non_us else "") + state_replacement,
        text,
    )
    edited, place_count = _PLACE_PATTERN.subn(place_replacement, edited)
    return edited if state_count or place_count else None


def jurisdiction_non_us(text: str) -> str | None:
    """Replace New York and Delaware references with England and Wales."""
    return _replace_jurisdiction(text, non_us=True)


def jurisdiction_us(text: str) -> str | None:
    """Replace New York and Delaware references with Illinois controls."""
    return _replace_jurisdiction(text, non_us=False)


def number_to_words(n: int) -> str:
    """Write an integer from 1 to 999 in US contract style."""
    if not 1 <= n <= 999:
        raise ValueError("number_to_words accepts integers from 1 to 999")
    if n >= 100:
        hundreds, remainder = divmod(n, 100)
        return _ONES[hundreds] + " hundred" + (" " + number_to_words(remainder) if remainder else "")
    if n >= 20:
        tens, ones = divmod(n, 10)
        return _TENS[tens] + ("-" + _ONES[ones] if ones else "")
    if n >= 10:
        return _TEENS[n - 10]
    return _ONES[n]


_WORDS_TO_NUMBER = {number_to_words(n): n for n in range(1, 1000)}


def _replace_numbers(text: str, change_value: bool) -> str | None:
    changed = False

    def replace(match: re.Match[str]) -> str:
        nonlocal changed
        words = match.group("words")
        paired = words is not None
        digits = match.group("paired_digits" if paired else "bare_digits")
        unit = match.group("paired_unit" if paired else "bare_unit")
        value = int(digits)
        if paired and _WORDS_TO_NUMBER.get(words.lower()) != value:
            return match.group()
        if change_value and value + 15 > 999:
            return match.group()
        changed = True
        if change_value:
            new_value = value + 15
            if paired:
                return f"{_match_case(words, number_to_words(new_value))} ({new_value}) {unit}"
            return f"{new_value} {unit}"
        if paired:
            return f"{digits} {unit}"
        return f"{number_to_words(value)} ({digits}) {unit}"

    edited = _DURATION_PATTERN.sub(replace, text)
    return edited if changed else None


def number_format(text: str) -> str | None:
    """Switch eligible durations between digits and words with digits."""
    return _replace_numbers(text, change_value=False)


def number_value(text: str) -> str | None:
    """Increase eligible duration values by 15 without changing their format."""
    return _replace_numbers(text, change_value=True)


EDITS: dict[str, tuple[Callable[[str], str | None], Callable[[str], str | None]]] = {
    "party_roles": (swap_roles, rename_roles),
    "jurisdiction": (jurisdiction_non_us, jurisdiction_us),
    "number_format": (number_format, number_value),
}


def build_cases(texts: list[str], name: str, max_n: int = 1000, seed: int = 42) -> dict:
    """Sample sorted test indices where both the edit and its control apply."""
    if max_n < 0:
        raise ValueError("max_n must be nonnegative")
    edit, control = EDITS[name]
    eligible = []
    for index, text in enumerate(texts):
        edited = edit(text)
        controlled = control(text)
        if edited is not None and controlled is not None:
            eligible.append((index, edited, controlled))
    if len(eligible) > max_n:
        chosen = np.random.default_rng(seed).choice(len(eligible), size=max_n, replace=False)
        eligible = [eligible[index] for index in sorted(chosen)]
    return {
        "idx": [row[0] for row in eligible],
        "edited": [row[1] for row in eligible],
        "control": [row[2] for row in eligible],
    }


def flip_stats(pred_orig, pred_edit, pred_ctrl, y_true, n_boot: int = 1000, seed: int = 42) -> dict:
    """Measure edit and control flips with shared-index bootstrap intervals."""
    original, edited, control, truth = map(np.asarray, (pred_orig, pred_edit, pred_ctrl, y_true))
    if original.ndim != 1 or any(array.shape != original.shape for array in (edited, control, truth)):
        raise ValueError("Predictions and labels must be one-dimensional arrays of equal length")
    if n_boot <= 0:
        raise ValueError("n_boot must be positive")
    n = len(original)
    if n == 0:
        return dict.fromkeys(
            ("n", "flip_rate", "flip_low", "flip_high", "ctrl_flip_rate", "ctrl_low", "ctrl_high",
             "diff", "diff_low", "diff_high", "acc_orig", "acc_orig_low", "acc_orig_high",
             "acc_edit", "acc_edit_low", "acc_edit_high", "acc_ctrl", "acc_ctrl_low", "acc_ctrl_high"), 0,
        )
    edit_flip = edited != original
    ctrl_flip = control != original
    diff_flip = edit_flip.astype(float) - ctrl_flip.astype(float)
    correct_orig = original == truth
    correct_edit = edited == truth
    correct_ctrl = control == truth
    samples = np.empty((n_boot, 6), dtype=float)
    rng = np.random.default_rng(seed)
    for start in range(0, n_boot, 100):
        end = min(start + 100, n_boot)
        indices = rng.integers(0, n, size=(end - start, n))
        samples[start:end, 0] = edit_flip[indices].mean(axis=1)
        samples[start:end, 1] = ctrl_flip[indices].mean(axis=1)
        samples[start:end, 2] = diff_flip[indices].mean(axis=1)
        samples[start:end, 3] = correct_orig[indices].mean(axis=1)
        samples[start:end, 4] = correct_edit[indices].mean(axis=1)
        samples[start:end, 5] = correct_ctrl[indices].mean(axis=1)
    lows, highs = np.percentile(samples, [2.5, 97.5], axis=0)
    return {
        "n": n,
        "flip_rate": float(edit_flip.mean()), "flip_low": float(lows[0]), "flip_high": float(highs[0]),
        "ctrl_flip_rate": float(ctrl_flip.mean()), "ctrl_low": float(lows[1]), "ctrl_high": float(highs[1]),
        "diff": float(diff_flip.mean()), "diff_low": float(lows[2]), "diff_high": float(highs[2]),
        "acc_orig": float(correct_orig.mean()), "acc_orig_low": float(lows[3]), "acc_orig_high": float(highs[3]),
        "acc_edit": float(correct_edit.mean()), "acc_edit_low": float(lows[4]), "acc_edit_high": float(highs[4]),
        "acc_ctrl": float(correct_ctrl.mean()), "acc_ctrl_low": float(lows[5]), "acc_ctrl_high": float(highs[5]),
    }


def decide(stats: dict, threshold: float = 0.02) -> str:
    """Fail when the edit flips over threshold and exceeds its control interval."""
    return "fail" if stats["flip_rate"] > threshold and stats["diff_low"] > 0 else "pass"


def _snippet(text: str, position: int, limit: int = 300) -> str:
    start = max(0, position - limit // 2)
    return text[start:start + limit].replace("\n", " ")


def _first_difference(original: str, edited: str) -> int:
    for index, (left, right) in enumerate(zip(original, edited, strict=False)):
        if left != right:
            return index
    return min(len(original), len(edited))


def _interval(stats: dict, value: str, low: str, high: str) -> str:
    return f"{stats[value]:.3f} [{stats[low]:.3f}, {stats[high]:.3f}]"


def run_counterfactual(
    run_dir, max_n: int = 1000, n_boot: int = 1000, seed: int = 42, out_dir="reports/audit",
) -> dict:
    """Predict original and changed clauses, then save statistics and flipped examples."""
    set_seed(seed)
    run_path = resolve_path(run_dir)
    classifier = load_classifier(run_path)
    texts, labels = load_split("test")
    label_names = get_label_names()
    results = {}
    names = {"party_roles": "Party roles", "jurisdiction": "Jurisdiction", "number_format": "Number format"}
    lines = [f"# Counterfactual tests: {run_path.name}", "",
             "Each row uses test clauses where both edits apply. Intervals are 95% bootstrap percentiles.",
             "The difference interval resamples edit and control flips at the same clause indices.", "",
             "| Test | n | Flip rate [95% interval] | Control flip rate [95% interval] | "
             "Difference [95% interval] | Accuracy before / edit / control [95% intervals] | Decision |",
             "|---|---:|---:|---:|---:|---:|---|" ]
    for name in EDITS:
        cases = build_cases(texts, name, max_n=max_n, seed=seed)
        indices = cases["idx"]
        if indices:
            original_texts = [texts[index] for index in indices]
            pred_orig = classifier.predict_proba(original_texts).argmax(1)
            pred_edit = classifier.predict_proba(cases["edited"]).argmax(1)
            pred_ctrl = classifier.predict_proba(cases["control"]).argmax(1)
        else:
            pred_orig = pred_edit = pred_ctrl = np.array([], dtype=int)
        stats = flip_stats(pred_orig, pred_edit, pred_ctrl, labels[indices], n_boot=n_boot, seed=seed)
        stats["decision"] = decide(stats)
        flipped = np.flatnonzero(pred_orig != pred_edit)
        if len(flipped) > 5:
            flipped = np.sort(np.random.default_rng(seed).choice(flipped, size=5, replace=False))
        examples = []
        for local_index in flipped:
            original = texts[indices[local_index]]
            changed = cases["edited"][local_index]
            position = _first_difference(original, changed)
            examples.append({
                "idx": indices[local_index],
                "original": _snippet(original, position),
                "edited": _snippet(changed, position),
                "label_before": label_names[pred_orig[local_index]],
                "label_after": label_names[pred_edit[local_index]],
            })
        stats["examples"] = examples
        results[name] = stats
        lines.append(
            f"| {names[name]} | {stats['n']} | "
            f"{_interval(stats, 'flip_rate', 'flip_low', 'flip_high')} | "
            f"{_interval(stats, 'ctrl_flip_rate', 'ctrl_low', 'ctrl_high')} | "
            f"{_interval(stats, 'diff', 'diff_low', 'diff_high')} | "
            f"{_interval(stats, 'acc_orig', 'acc_orig_low', 'acc_orig_high')} / "
            f"{_interval(stats, 'acc_edit', 'acc_edit_low', 'acc_edit_high')} / "
            f"{_interval(stats, 'acc_ctrl', 'acc_ctrl_low', 'acc_ctrl_high')} | "
            f"{stats['decision']} |"
        )
    lines += ["", "A test fails when its flip rate exceeds 2% and the paired difference interval is above 0.", ""]
    for name, stats in results.items():
        lines += [f"## {names[name]}: flipped examples", ""]
        if not stats["examples"]:
            lines += ["No flipped clauses in the selected sample.", ""]
        for example in stats["examples"]:
            lines += [f"### Test index {example['idx']}", "",
                      f"Prediction: {example['label_before']} to {example['label_after']}", "",
                      f"Original: {example['original']}", "",
                      f"Edited: {example['edited']}", ""]
    output = ensure_dir(Path(out_dir) / run_path.name)
    save_json(results, output / "counterfactual.json")
    (output / "counterfactual.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    return results


def main(argv=None) -> None:
    """Run counterfactual tests on one saved classifier."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run", required=True)
    parser.add_argument("--max-n", type=int, default=1000)
    parser.add_argument("--n-boot", type=int, default=1000)
    parser.add_argument("--out", default="reports/audit")
    args = parser.parse_args(argv)
    results = run_counterfactual(args.run, max_n=args.max_n, n_boot=args.n_boot, out_dir=args.out)
    for name, stats in results.items():
        print(f"{name}: n={stats['n']}, flip={stats['flip_rate']:.3f}, "
              f"control={stats['ctrl_flip_rate']:.3f}, decision={stats['decision']}")


if __name__ == "__main__":
    main()
