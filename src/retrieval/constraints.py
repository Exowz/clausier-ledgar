"""Day duration extraction and filtering for clause retrieval."""

import re

_ONES = ("one", "two", "three", "four", "five", "six", "seven", "eight", "nine")
_TEENS = ("ten", "eleven", "twelve", "thirteen", "fourteen", "fifteen", "sixteen", "seventeen", "eighteen", "nineteen")
_TENS = ("twenty", "thirty", "forty", "fifty", "sixty", "seventy", "eighty", "ninety")
_WORDS = {word: value for value, word in enumerate(_ONES, 1)}
_WORDS.update({word: value for value, word in enumerate(_TEENS, 10)})
for _tens_value, _tens_word in enumerate(_TENS, 2):
    _WORDS[_tens_word] = _tens_value * 10
    for _one_value, _one_word in enumerate(_ONES, 1):
        _WORDS[f"{_tens_word} {_one_word}"] = _tens_value * 10 + _one_value
        _WORDS[f"{_tens_word}-{_one_word}"] = _tens_value * 10 + _one_value
_WORDS.update({"one hundred twenty": 120, "one hundred eighty": 180, "three hundred sixty-five": 365,
               "three hundred sixty five": 365})
_NUMBER = "|".join(re.escape(word) for word in sorted(_WORDS, key=len, reverse=True))
_DAYS_RE = re.compile(
    rf"\b(?P<number>\d+|{_NUMBER})\b(?:\s*\(\d+\))?\s*(?:-|\s)\s*(?:calendar\s+|business\s+)?days?\b",
    re.IGNORECASE,
)


def extract_days(text: str) -> set[int]:
    """Return numeric or written day durations, excluding months and years."""
    return {int(value) if value.isdigit() else _WORDS[value.lower()]
            for value in (match.group("number") for match in _DAYS_RE.finditer(text))}


def keep_days(indices: list[int], texts: list[str], days: set[int]) -> list[int]:
    """Keep ranked indices whose clause mentions at least one requested day duration."""
    if not days:
        return indices
    return [index for index in indices if extract_days(texts[index]) & days]
