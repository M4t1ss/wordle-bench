# Word Bench

A multilingual Wordle benchmark for evaluating language model reasoning, built on the [clemcore framework](https://github.com/clp-research/clemcore).

## Overview

Word Bench evaluates how well language models play Wordle across **9 languages** and **3 word frequency tiers**. Each model plays 150 games per language (50 words × 3 difficulty levels), receiving color-coded feedback (green/yellow/red) after each guess and having up to 6 attempts to find the target word.

The benchmark measures rule comprehension, feedback utilization, strategic reasoning, and robustness across languages with varying morphological complexity and script diversity.

## Languages

| Language | Code | Script | Alphabet |
|----------|------|--------|----------|
| English | `wordle` (en) | Latin | 26 letters |
| German | `wordle_de` (de) | Latin | 26 letters |
| Spanish | `wordle_es` (es) | Latin | 27 letters |
| French | `wordle_fr` (fr) | Latin | 26 letters (+ diacritics) |
| Portuguese | `wordle_pt` (pt) | Latin | 23 letters (+ diacritics) |
| Latvian | `wordle_lv` (lv) | Latin | 33 letters (+ diacritics) |
| Lithuanian | `wordle_lt` (lt) | Latin | 32 letters (+ diacritics) |
| Estonian | `wordle_et` (et) | Latin | 27 letters (+ diacritics) |
| Japanese | `wordle_ja` (ja) | Hiragana | 46 letters |

## Word Frequency Tiers

Each language includes 150 words split into three frequency-based difficulty levels (50 words each):

| Difficulty | Experiment Name | Description |
|------------|-----------------|-------------|
| **High frequency** | `high_frequency_words_no_clue_no_critic` | Common function words and short content words; most LLMs have extensive training data for these |
| **Medium frequency** | `medium_frequency_words_no_clue_no_critic` | Less common words requiring deeper vocabulary knowledge |
| **Low frequency** | `low_frequency_words_no_clue_no_critic` | Rare words that test genuine reasoning over memorization |

All experiments use the `no_clue_no_critic` configuration: models receive only the standard color-coded feedback with no additional hints or corrective prompts beyond the retry system.

## Framework Features

### Structured Response Format

Models must respond in a structured format providing both an explanation of their reasoning and their next guess. This allows tracking of strategic thinking, not just final outcomes.

### Abort Mechanism with Retry Budgets

The framework includes a retry system to handle model errors gracefully before aborting:

| Error Type | Retry Budget | Description |
|------------|--------------|-------------|
| `INVALID_FORMAT` | 3 retries | Response doesn't follow expected format (missing keyword, wrong structure, multiple guesses, non-alpha chars) |
| `INVALID_WORD_LENGTH` | 5 retries | Guess not exactly 5 letters/characters |
| `NOT_VALID_WORD_FOR_GAME` | 10 retries | Word not in the language's dictionary |

After exhausting retries for a given error, the game is marked as **aborted** (protocol failure). This distinguishes between models that genuinely can't reason vs. those that produce valid guesses but struggle with format compliance.

### Metrics

| Metric | Description |
|--------|-------------|
| **Success** (binary) | Word guessed within 6 attempts |
| **Aborted** (binary) | Game ended due to repeated rule violations |
| **Speed** (0–100) | Fewer guesses → higher score |
| **Closeness** (0–25 per turn) | How effectively feedback is used per turn |
| **Repetition** (count) | How often the model repeats a guess |
| **Strategy** (per turn) | Quality of letter-elimination strategy |
| **Alphabet Coverage** | Percentage of language's alphabet letters used across all guesses |
| **First-Guess Consistency** | Whether model's opening guess varies across games |

### Japanese (Hiragana) Support

Japanese is a special case: 5-letter words are composed of hiragana characters (46-letter alphabet). This tests models' ability to handle non-Latin scripts, where tokenization issues and training data scarcity create significant challenges.

## Installation

Requires **Python 3.10+** and the clemcore framework.

```bash
# Setup
./setup.sh <basic|hf|vllm>
#   basic  — remote API backends only (OpenAI, Anthropic, Google, etc.)
#   hf     — adds HuggingFace transformers for local models
#   vllm   — adds vLLM for optimized local inference

# Add API keys
cp key.json.template ~/.clemcore/key.json   # or place in workspace
# Edit key.json with your API credentials
```

## Usage

```bash
# Run a single game on a single model
./run.sh wordle_lv gpt-oss-20b-t1.0

# Run all games in a language
clem run -g wordle_lv -m gpt-oss-20b-t1.0

# Score results
clem score -g wordle_lv

# Generate HTML transcripts
clem transcribe -g wordle_lv
```

### Custom Models

Add models via `model_registry.json` (see `model_registry.json.template`):

```json
{
  "model_name": "my-model",
  "backend": "my-backend"
}
```

### Custom Backend

Create `<backend_name>_api.py` implementing `generate_response()`. The backend module filename must match the `"backend"` key in the model registry.

## Repository Structure

```
wordle-bench/
├── wordle/              # English (baseline)
├── wordle_de/           # German
├── wordle_es/           # Spanish
├── wordle_fr/           # French
├── wordle_pt/           # Portuguese
├── wordle_lv/           # Latvian
├── wordle_lt/           # Lithuanian
├── wordle_et/           # Estonian
├── wordle_ja/           # Japanese (hiragana)
│   ├── clemgame.json    # Game config
│   ├── master.py        # Game logic (localized)
│   ├── in/
│   │   └── instances.json  # Word list + difficulty tiers
│   └── utils/           # Language-specific utilities
├── scripts/             # Word generation, evaluation helpers
├── setup.sh             # Environment setup
├── run.sh               # Run + score + transcribe
└── requirements.txt
```

Each language directory is self-contained with localized prompts, error messages, and dictionary validation.

## Contributing

We welcome contributions — new language variants, model additions, or framework improvements. Open a pull request.

See the clemcore documentation for details on [adding games](docs/howto_add_games.md) and [adding models](docs/howto_add_models.md).

## License

[See LICENSE](LICENSE)
