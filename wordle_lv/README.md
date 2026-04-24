# Wordle — Latvian (wordle_lv)

A five-letter word-guessing game for evaluating language models, run with the [clemcore framework](https://github.com/clp-research/clemcore).

## Game

The LLM plays as the guesser. A five-letter Latvian target word is selected, and the model has six attempts to guess it. After each guess, the model receives feedback:

- 🟩 Green — correct letter in the correct position
- 🟨 Yellow — correct letter in the wrong position
- ⬜ Red — letter not in the target word

The model must respond in a structured format, providing both an explanation of its reasoning and its next guess.

## What This Evaluates

- **Rule comprehension** — can the model generate valid five-letter words in the correct format?
- **Feedback utilisation** — does the model effectively use colour-coded feedback to narrow down possibilities?
- **Speed** — how few guesses does it take to solve the word?

## Dataset

50 high-frequency Latvian words. Latin alphabet with special characters: ā, ē, ī, ņ, š, ū, ž, ķ, ģ, ļ.

## Metrics

| Metric | Range | Description |
|--------|-------|-------------|
| Success | binary | Word guessed within 6 attempts |
| Aborted | binary | Game ended due to repeated rule violations |
| Speed | 0–100 | Fewer guesses → higher score |
| Closeness | 0–25 per turn | How effectively feedback is used per turn |
| Repetition | count | How often the model repeats a guess |
| Strategy | per turn | Quality of letter-elimination strategy |

## Language-Specific Challenges

Latvian uses 10 special characters (ā, ē, ī, ņ, š, ū, ž, ķ, ģ, ļ) that are phonemically distinct from their Latin counterparts. Long vowels (ā, ē, ī, ū) are particularly important — "laiks" and "laikā" are different forms of the same word in different cases, and a model must treat diacritics as meaningful, not decorative. Latvian is a highly inflected language with 6 noun cases, so the valid word set includes many grammatically inflected forms. Like Lithuanian, Latvian is severely underrepresented in LLM training data, making this one of the most discriminating variants in the benchmark for true multilingual capability.
