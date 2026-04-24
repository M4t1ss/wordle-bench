# Wordle — Japanese (wordle_ja)

A five-character word-guessing game for evaluating language models, run with the [clemcore framework](https://github.com/clp-research/clemcore).

## Game

The LLM plays as the guesser. A five-character hiragana target word is selected, and the model has six attempts to guess it. After each guess, the model receives feedback:

- 🟩 Green — correct character in the correct position
- 🟨 Yellow — correct character in the wrong position
- ⬜ Red — character not in the target word

The model must respond in a structured format, providing both an explanation of its reasoning and its next guess.

## What This Evaluates

- **Script comprehension** — can the model generate valid hiragana sequences?
- **Feedback utilisation** — does the model effectively use position feedback to narrow down possibilities?
- **Speed** — how few guesses does it take to solve the word?

## Dataset

50 high-frequency Japanese words written in hiragana. Includes characters with dakuten (voicing marks), handaku (labialisation), and the long-vowel mark (ー).

## Metrics

| Metric | Range | Description |
|--------|-------|-------------|
| Success | binary | Word guessed within 6 attempts |
| Aborted | binary | Game ended due to repeated rule violations |
| Speed | 0–100 | Fewer guesses → higher score |
| Closeness | 0–25 per turn | How effectively feedback is used per turn |
| Repetition | count | How often the model repeats a guess |
| Strategy | per turn | Quality of character-elimination strategy |

## Language-Specific Challenges

Japanese is fundamentally different from alphabetic languages. The hiragana syllabary has ~46 base characters (plus dakuten/handaku variants and the long-vowel mark ー), making the character space much larger than a 26-letter alphabet. Each "letter" is actually a mora (syllable unit), so the game operates at a different linguistic level. Many common Japanese words are written in kanja in real usage, so five-hiragana words are a restricted subset. The long-vowel mark (ー) appears frequently in loanwords and must be treated as a distinct character. Japanese LLM performance here tests both script fluency and the ability to do positional reasoning over a non-alphabetic writing system.
