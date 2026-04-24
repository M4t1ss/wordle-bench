# Wordle — Lithuanian (wordle_lt)

A five-letter word-guessing game for evaluating language models, run with the [clemcore framework](https://github.com/clp-research/clemcore).

## Game

The LLM plays as the guesser. A five-letter Lithuanian target word is selected, and the model has six attempts to guess it. After each guess, the model receives feedback:

- 🟩 Green — correct letter in the correct position
- 🟨 Yellow — correct letter in the wrong position
- ⬜ Red — letter not in the target word

The model must respond in a structured format, providing both an explanation of its reasoning and its next guess.

## What This Evaluates

- **Rule comprehension** — can the model generate valid five-letter words in the correct format?
- **Feedback utilisation** — does the model effectively use colour-coded feedback to narrow down possibilities?
- **Speed** — how few guesses does it take to solve the word?

## Dataset

50 high-frequency Lithuanian words. Latin alphabet with special characters: ą, ė, ę, š, ū, ų, ž.

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

Lithuanian is one of the most conservative Indo-European languages, preserving features lost in most other branches. The alphabet includes 7 special characters (ą, ė, ę, š, ū, ų, ž) that are phonemically distinct — nasal vowels (ą, ę) and long vowels (ū, ų) must not be confused with their non-diacritic counterparts. Lithuanian has a rich system of noun and adjective declensions (7 cases), so many five-letter words appear in inflected forms, making the valid word set morphologically complex. Lithuanian is severely underrepresented in LLM training data, making this a strong test of a model's true multilingual capability rather than training data memorisation.
