"""Scoring metrics: letter distribution analysis and cross-language difficulty.

Provides:
  - letter_distribution(): character frequency stats for a word list
  - alphabet_stats(): alphabet size, diacritic count, etc.
  - difficulty_score(): composite difficulty metric for a language variant
  - compare_languages(): cross-language difficulty comparison report
"""
import json
import math
import os
from collections import Counter
from pathlib import Path
from typing import Any, Dict, List, Tuple

# ---------------------------------------------------------------------------
# Character classification
# ---------------------------------------------------------------------------

BASE_LATIN = set("abcdefghijklmnopqrstuvwxyz")

# Common extended Latin used in European languages
EXTENDED_LATIN = {
    "àáâãäåæçèéêëìíîïðñòóôõöøùúûüýþÿ",
    "ÀÁÂÃÄÅÆÇÈÉÊËÌÍÎÏÐÑÒÓÔÕÖØÙÚÛÜÝÞ",
}


def _classify_charset(words: List[str]) -> Dict[str, Any]:
    """Classify the character set used by a word list."""
    all_chars = set()
    for w in words:
        all_chars.update(w)

    base_latin = set("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ")
    upper = all_chars & set("ABCDEFGHIJKLMNOPQRSTUVWXYZ")

    # Detect non-Latin scripts (CJK, etc.)
    non_latin = set()
    for c in all_chars:
        cp = ord(c)
        # Hiragana / Katakana / Kanji ranges (rough)
        if 0x3040 <= cp <= 0x30FF or 0x4E00 <= cp <= 0x9FFF or cp == 0x30FC:
            non_latin.add(c)

    # Extended Latin = chars that are NOT base Latin and NOT non-Latin
    extended = all_chars - base_latin - non_latin

    return {
        "total_unique": len(all_chars),
        "base_latin": len(all_chars & base_latin),
        "uppercase": len(upper),
        "extended_latin": len(extended),
        "non_latin": len(non_latin),
        "all_chars_sorted": sorted(all_chars),
    }


# ---------------------------------------------------------------------------
# Letter distribution
# ---------------------------------------------------------------------------


def letter_distribution(words: List[str]) -> Dict[str, Any]:
    """Compute character frequency distribution for a word list.

    Returns a dict with:
      - char_freqs: dict of character -> count (across all words, positions summed)
      - char_freq_pct: same as percentage of total character slots
      - position_freqs: dict of position (0-4) -> char -> count
      - unique_ratio: fraction of character slots that are unique chars
      - vowel_ratio: approximate vowel-to-consonant ratio (Latin only)
    """
    if not words:
        return {}

    total_chars = sum(len(w) for w in words)
    char_counter: Counter = Counter()
    position_counters: Dict[int, Counter] = {}

    for w in words:
        for i, c in enumerate(w):
            char_counter[c] += 1
            if i not in position_counters:
                position_counters[i] = Counter()
            position_counters[i][c] += 1

    char_freq_pct = {c: round(cnt / total_chars * 100, 2) for c, cnt in char_counter.most_common()}

    # Approximate vowel detection (Latin only)
    vowels = set("aeiouAEIOUáéíóúÁÉÍÓÚàèìòùÀÈÌÒÙäëïöüÄËÏÖÜâêîôûÂÊÎÔÛãõÃÕâÂôÔ")
    vowel_count = sum(char_counter.get(v, 0) for v in vowels)
    vowel_ratio = round(vowel_count / total_chars, 3) if total_chars else 0

    return {
        "char_freqs": dict(char_counter.most_common()),
        "char_freq_pct": char_freq_pct,
        "position_freqs": {pos: dict(cnt.most_common()) for pos, cnt in sorted(position_counters.items())},
        "unique_ratio": round(len(char_counter) / total_chars, 4) if total_chars else 0,
        "vowel_ratio": vowel_ratio,
        "total_chars": total_chars,
        "word_count": len(words),
    }


# ---------------------------------------------------------------------------
# Difficulty scoring
# ---------------------------------------------------------------------------


def _search_space_size(charset_size: int, word_length: int) -> int:
    """Theoretical search space (charset_size ^ word_length)."""
    return charset_size ** word_length


def _character_redundancy(words: List[str]) -> float:
    """How redundant the character set is (lower = more redundant = harder).

    Measured as the average number of distinct characters per word position.
    """
    if not words:
        return 0.0
    word_length = len(words[0])
    position_diversity = []
    for pos in range(word_length):
        unique_at_pos = len({w[pos] for w in words if pos < len(w)})
        position_diversity.append(unique_at_pos)
    return sum(position_diversity) / word_length if word_length else 0


def _pattern_uniqueness(words: List[str]) -> float:
    """Fraction of words with a unique character pattern.

    Pattern = frozenset of characters in the word.
    Higher = easier (less ambiguity from feedback).
    """
    patterns = [frozenset(w) for w in words]
    pattern_counts = Counter(patterns)
    unique_patterns = sum(1 for p, cnt in pattern_counts.items() if cnt == 1)
    return unique_patterns / len(words) if words else 0


def difficulty_score(words: List[str], lang_code: str = "") -> Dict[str, Any]:
    """Compute a composite difficulty score for a language word list.

    Metrics:
      - charset_size: number of unique characters in the word list
      - search_space: theoretical charset_size ^ word_length
      - char_redundancy: avg distinct chars per position (lower = harder)
      - pattern_uniqueness: fraction of words with unique char patterns (lower = harder)
      - avg_word_length: mean word length
      - diacritic_ratio: fraction of chars that are extended/non-base Latin
      - difficulty_index: composite 0-100 score (higher = harder)
    """
    if not words:
        return {}

    charset = _classify_charset(words)
    word_length = len(words[0]) if words else 5
    charset_size = charset["total_unique"]

    search_space = _search_space_size(charset_size, word_length)
    redundancy = _character_redundancy(words)
    uniqueness = _pattern_uniqueness(words)

    # Diacritic ratio (extended + non-latin chars as fraction of unique charset)
    charset_size = charset["total_unique"]
    non_base = charset["extended_latin"] + charset["non_latin"]
    diacritic_ratio = round(non_base / charset_size, 3) if charset_size else 0

    # Composite difficulty index (0-100, higher = harder)
    # Factors: larger charset, lower redundancy, lower pattern uniqueness, more diacritics
    charset_factor = min(charset_size / 50, 1.0)  # normalise: 50+ chars = max
    redundancy_factor = max(0, 1 - (redundancy / charset_size)) if charset_size else 0
    uniqueness_factor = 1 - uniqueness
    diacritic_factor = min(diacritic_ratio * 2, 1.0)

    difficulty_index = round(
        (charset_factor * 0.3 + redundancy_factor * 0.25 + uniqueness_factor * 0.25 + diacritic_factor * 0.2) * 100,
        1,
    )

    return {
        "lang_code": lang_code,
        "word_count": len(words),
        "word_length": word_length,
        "charset_size": charset_size,
        "search_space": search_space,
        "char_redundancy": round(redundancy, 2),
        "pattern_uniqueness": round(uniqueness, 3),
        "diacritic_ratio": diacritic_ratio,
        "charset_details": charset,
        "difficulty_index": difficulty_index,
    }


# ---------------------------------------------------------------------------
# Cross-language comparison
# ---------------------------------------------------------------------------


def compare_languages(bench_root: str) -> List[Dict[str, Any]]:
    """Load all language variants and compute difficulty scores.

    Returns a sorted list of difficulty dicts (hardest first).
    """
    results = []
    root = Path(bench_root)

    for lang_dir in sorted(root.iterdir()):
        if not lang_dir.is_dir() or not lang_dir.name.startswith("wordle"):
            continue

        instances = lang_dir / "in" / "instances.json"
        if not instances.exists():
            continue

        with open(instances) as f:
            data = json.load(f)

        words = []
        for exp in data.get("experiments", []):
            for gi in exp.get("game_instances", []):
                words.append(gi["target_word"])
        words = list(dict.fromkeys(words))  # deduplicate, preserving order

        if not words:
            continue

        # Derive lang code from directory name
        lang_code = lang_dir.name.replace("wordle_", "").replace("wordle", "en")

        score = difficulty_score(words, lang_code=lang_code)
        results.append(score)

    # Sort by difficulty index descending
    results.sort(key=lambda r: r.get("difficulty_index", 0), reverse=True)
    return results


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def _format_report(results: List[Dict[str, Any]]) -> str:
    """Format a human-readable comparison report."""
    lines = []
    lines.append("# Cross-Language Difficulty Comparison")
    lines.append("")
    lines.append("| Language | Words | Charset | Search Space | Redundancy | Uniqueness | Special % | Difficulty |")
    lines.append("|----------|-------|---------|-------------|------------|------------|-----------|------------|")

    for r in results:
        special_pct = round(r.get("diacritic_ratio", 0) * 100, 1)
        search = f"{r.get('search_space', 0):,}" if r.get("search_space", 0) < 1e12 else f"{r.get('search_space', 0):.2e}"
        lines.append(
            f"| {r['lang_code'].upper()} | {r['word_count']} | {r['charset_size']} "
            f"| {search} | {r['char_redundancy']} "
            f"| {r['pattern_uniqueness']} | {special_pct}% | {r['difficulty_index']} |"
        )

    lines.append("")
    lines.append("## Notes")
    lines.append("")
    lines.append("- **Charset**: number of unique characters in the word list.")
    lines.append("- **Search Space**: theoretical max (charset_size ^ word_length).")
    lines.append("- **Redundancy**: average distinct characters per position (lower = harder to eliminate).")
    lines.append("- **Uniqueness**: fraction of words with unique character sets (lower = more ambiguity).")
    lines.append("- **Special %**: fraction of unique characters that are non-base-Latin (diacritics, CJK, etc.).")
    lines.append("- **Difficulty Index**: composite 0-100 score (weighted average of normalised factors).")

    return "\n".join(lines)


if __name__ == "__main__":
    import sys

    bench_root = sys.argv[1] if len(sys.argv) > 1 else "."
    results = compare_languages(bench_root)
    print(_format_report(results))
