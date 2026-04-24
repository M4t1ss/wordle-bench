# Wordle — Spanish (wordle_es)

A five-letter word-guessing game for evaluating language models, run with the [clemcore framework](https://github.com/clp-research/clemcore).

## Game

The LLM plays as the guesser. A five-letter Spanish target word is selected, and the model has six attempts to guess it. After each guess, the model receives feedback:

- 🟩 Green — correct letter in the correct position
- 🟨 Yellow — correct letter in the wrong position
- ⬜ Red — letter not in the target word

The model must respond in a structured format, providing both an explanation of its reasoning and its next guess.

## What This Evaluates

- **Rule comprehension** — can the model generate valid five-letter words in the correct format?
- **Feedback utilisation** — does the model effectively use colour-coded feedback to narrow down possibilities?
- **Speed** — how few guesses does it take to solve the word?

## Dataset

50 high-frequency Spanish words. Standard Latin alphabet plus accented vowels (á, í, ú). No ñ in the current word list.

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

Spanish has a more phonetic writing system than English, which means letter patterns are more predictable — a known vowel position is more reliably informative. However, the vocabulary relies heavily on a small set of grammatical particles and prepositions ("sobre", "entre", "desde", "hasta"), making strategic elimination trickier. Accented vowels (á, í, ú) add a layer of complexity: models may fail to distinguish between accented and unaccented forms, and the feedback system must treat them as distinct characters.
