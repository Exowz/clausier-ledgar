"""Fast checks for LEDGAR overlap and slice rules."""

import numpy as np

from src.data import contract_family, find_overlap, jurisdiction, length_bin, normalize_text, slice_frame
from src.eda import _token_stats


def test_normalize_text() -> None:
    assert normalize_text("  The Tenant, shall PAY!! ") == "the tenant shall pay"


def test_find_overlap() -> None:
    long_clause = " ".join(f"term{i}" for i in range(30))
    train = ["The tenant pays rent.", long_clause, "A separate indemnity applies.", "Arbitration is binding."]
    test = [" THE tenant, pays rent! ", long_clause.replace("term15", "replacement"), "unrelated vocabulary only"]

    overlap = find_overlap(train, test, near_threshold=0.8, chunk_size=2)

    assert overlap.columns.tolist() == ["exact_dup", "max_sim", "nearest_train_idx", "near_dup", "keep"]
    assert overlap["exact_dup"].tolist() == [True, False, False]
    assert overlap["near_dup"].tolist() == [False, True, False]
    assert overlap["keep"].tolist() == [False, False, True]
    assert overlap["nearest_train_idx"].iloc[:2].tolist() == [0, 1]
    assert overlap["max_sim"].iloc[1] >= 0.8


def test_exact_overlap_points_to_actual_twin_for_empty_tfidf_vector() -> None:
    overlap = find_overlap(["A", "The tenant pays rent."], ["a"], chunk_size=1)
    assert bool(overlap.loc[0, "exact_dup"])
    assert overlap.loc[0, "nearest_train_idx"] == 0


def test_contract_family() -> None:
    assert contract_family("The borrower shall pay the lender.") == "credit"
    assert contract_family("The landlord and tenant agree.") == "lease"
    assert contract_family("Licensee shall comply.") == "license"
    assert contract_family("The parties agree.") == "other"
    assert contract_family("The borrower and tenant agree.") == "credit"


def test_jurisdiction() -> None:
    assert jurisdiction("laws of the State of Delaware") == "delaware"
    assert jurisdiction("New York") == "new_york"
    assert jurisdiction("State of California") == "other_us"
    assert jurisdiction("laws of England and Wales") == "non_us"
    assert jurisdiction("the parties agree") == "none"
    assert jurisdiction("Delaware and England") == "delaware"
    assert jurisdiction("new york") == "none"


def test_length_bin() -> None:
    assert length_bin(10) == "<64"
    assert length_bin(64) == "64-127"
    assert length_bin(255) == "128-255"
    assert length_bin(256) == ">=256 (truncated)"
    assert length_bin(256, max_len=512) == "128-511"
    assert length_bin(512, max_len=512) == ">=512 (truncated)"


def test_slice_frame() -> None:
    frame = slice_frame(["The tenant in Delaware agrees.", "No markers."], np.array([35, 300]))
    assert frame.columns.tolist() == ["family", "jurisdiction", "length_bin"]
    assert frame.shape == (2, 3)
    assert frame.iloc[0].tolist() == ["lease", "delaware", "<64"]
    assert frame.iloc[1].tolist() == ["other", "none", ">=256 (truncated)"]
    assert slice_frame(["No markers."]).columns.tolist() == ["family", "jurisdiction"]


def test_token_stats_uses_course_truncation_rule() -> None:
    counts = np.array([127, 128, 129, 256, 257, 512, 513])
    stats = _token_stats(counts)
    assert stats["median"] == 256
    assert stats["max"] == 513
    assert stats["share_truncated"]["128"] == 5 / 7
    assert stats["share_truncated"]["256"] == 3 / 7
    assert stats["share_truncated"]["512"] == 1 / 7
