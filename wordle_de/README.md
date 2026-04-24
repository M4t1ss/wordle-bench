# Wordle — German (wordle_de)

A five-letter word-guessing game for evaluating language models, run with the [clemcore framework](https://github.com/clp-research/clemcore).

## Game

The LLM plays as the guesser. A five-letter German target word is selected, and the model has six attempts to guess it. After each guess, the model receives feedback:

- 🟩 Green — correct letter in the correct position
- 🟨 Yellow — correct letter in the wrong position
- ⬜ Red — letter not in the target word

The model must respond in a structured format, providing both an explanation of its reasoning and its next guess.

## What This Evaluates

- **Rule comprehension** — can the model generate valid five-letter words in the correct format?
- **Feedback utilisation** — does the model effectively use colour-coded feedback to narrow down possibilities?
- **Speed** — how few guesses does it take to solve the word?

## Dataset

50 high-frequency German words. Standard Latin alphabet, no umlauts or special characters in the current word list.

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

German uses a standard Latin alphabet without umlauts in the current word list. The vocabulary consists mainly of high-frequency grammatical words (prepositions, adverbs, pronouns) — words like "durch", "immer", "schon". These are functionally essential but offer limited semantic hooks for guessing, making strategic elimination harder. German also has a higher consonant-to-vowel ratio than English, which changes the dynamics of letter feedback.
