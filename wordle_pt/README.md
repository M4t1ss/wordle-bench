# Wordle — Portuguese (wordle_pt)

A five-letter word-guessing game for evaluating language models, run with the [clemcore framework](https://github.com/clp-research/clemcore).

## Game

The LLM plays as the guesser. A five-letter Portuguese target word is selected, and the model has six attempts to guess it. After each guess, the model receives feedback:

- 🟩 Green — correct letter in the correct position
- 🟨 Yellow — correct letter in the wrong position
- ⬜ Red — letter not in the target word

The model must respond in a structured format, providing both an explanation of its reasoning and its next guess.

## What This Evaluates

- **Rule comprehension** — can the model generate valid five-letter words in the correct format?
- **Feedback utilisation** — does the model effectively use colour-coded feedback to narrow down possibilities?
- **Speed** — how few guesses does it take to solve the word?

## Dataset

50 high-frequency Portuguese words. Latin alphabet with special characters: ã, á, á, ú.

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

Portuguese has a relatively complex orthography with nasal vowels (ã, õ) and various accent marks (á, à, é, ê, ó, ô, ú). The nasal tilde (ã, õ) is particularly distinctive — it represents a completely different sound from the base vowel and must be treated as a separate letter. Portuguese also shares significant vocabulary overlap with Spanish (false friends aside), which can lead models with strong Spanish training to confuse the two. The word list is rich in function words and grammatical particles ("sobre", "entre", "mesmo", "tempo"), offering limited semantic hooks for guessing. Portuguese is moderately represented in LLM training data, but Brazilian vs European variants can create additional noise.
