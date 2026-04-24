# Wordle — French (wordle_fr)

A five-letter word-guessing game for evaluating language models, run with the [clemcore framework](https://github.com/clp-research/clemcore).

## Game

The LLM plays as the guesser. A five-letter French target word is selected, and the model has six attempts to guess it. After each guess, the model receives feedback:

- 🟩 Green — correct letter in the correct position
- 🟨 Yellow — correct letter in the wrong position
- ⬜ Red — letter not in the target word

The model must respond in a structured format, providing both an explanation of its reasoning and its next guess.

## What This Evaluates

- **Rule comprehension** — can the model generate valid five-letter words in the correct format?
- **Feedback utilisation** — does the model effectively use colour-coded feedback to narrow down possibilities?
- **Speed** — how few guesses does it take to solve the word?

## Dataset

50 high-frequency French words. Latin alphabet with special characters: â, ç, è, é.

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

French has a notoriously inconsistent spelling-to-sound correspondence. Five-letter French words often contain silent letters, making phonological reasoning less useful than in more phonetic languages. The vocabulary is rich in articles, prepositions, and pronouns ("votre", "cette", "comme", "était"), which are structurally important but offer limited semantic context for guessing. Accented characters (â, ç, è, é) must be treated as distinct letters — a model that confuses "e" and "é" will systematically fail. French is moderately well-represented in LLM training data, but five-letter word constraints interact with French morphology in ways that make naive strategies unreliable.
