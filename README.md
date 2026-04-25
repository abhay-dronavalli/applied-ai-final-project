# VibeFinder: Applied AI Music Recommender

## Base Project

This project extends the AI110 Module 3 Music Recommender Simulation. The original system built a content-based filtering pipeline in Python: it scored songs from an 18-song catalog against a hardcoded user taste profile using weighted features like genre, mood, energy, valence, and danceability. Users were represented as static dicts, the scoring ran once, and the top results were printed to the console. There was no language model involved and no feedback loop.

---

## What's New

- **Agentic loop** (plan, act, evaluate, revise) that runs up to 3 iterations before returning final results
- **LLM integration** via the Anthropic API: Claude Haiku parses a natural language music request into a structured user profile and picks the best scoring mode
- **Input guardrails** that block empty, too-short, or non-music-related requests before any API call is made
- **Structured logging** of every step taken, returned alongside the final recommendations
- **Test harness** (`tests/test_harness.py`) that runs 8 predefined inputs and reports pass/fail results with a summary table

---

## System Architecture

```mermaid
flowchart TD
    A([User Input]) --> B{Guardrail Check}

    B -- "empty / too short / not music-related" --> C([Early Exit: error message\nresults=[], iterations=0])

    B -- passes --> D[PLAN\ncall claude-haiku-4-5-20251001\nparse JSON profile + scoring_mode]

    D --> E[ACT\ncall recommend_songs\nfrom recommender.py\nreturn top 5 results]

    E --> F[EVALUATE\ndiversity_score = unique genres / 5\navg_score = mean of top-5 scores\nquality_pass = avg >= 1.2 AND diversity >= 0.4]

    F -- "quality_pass = True\nOR iterations = 3" --> G([Final Output\nresults + full agent_log\niterations count\nfinal_profile\nquality dict])

    F -- "quality_pass = False\nAND iterations < 3" --> H[REVISE\nbuild revised prompt with\nfailure reason appended]

    H -- "increment iteration counter" --> D

    style A fill:#4a90d9,color:#fff
    style C fill:#e05252,color:#fff
    style D fill:#7b68ee,color:#fff
    style E fill:#5ba85b,color:#fff
    style F fill:#e0a030,color:#fff
    style H fill:#c47a20,color:#fff
    style G fill:#4a90d9,color:#fff
```

---

## Setup Instructions

1. Clone the repository:

   ```bash
   git clone https://github.com/your-username/applied-ai-final-project.git
   cd applied-ai-final-project
   ```

2. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```

3. Set your Anthropic API key. On Windows (PowerShell):

   ```powershell
   $env:ANTHROPIC_API_KEY = "your-api-key-here"
   ```

4. Run the agent (interactive CLI):

   ```bash
   python src/agent.py
   ```

5. Run the test harness:

   ```bash
   python tests/test_harness.py
   ```

---

## Sample Interactions

**1. Chill lofi for studying**

```
$ python src/agent.py
=== VibeFinder Agent ===
Describe the music you want: I want chill lofi music with low energy for studying

--- Agent ran 1 iteration(s) ---

[Agent Log]
  [1] PLAN   -> genre=lofi  mood=chill  energy=0.2  mode=mood_first
         Reasoning : User explicitly requested chill lofi music for studying, indicating
                     preference for relaxed atmosphere with minimal energy and
                     focus-friendly characteristics
  [1] ACT    -> mode=mood_first, returned 5 songs
  [1] EVAL   -> avg_score=1.651  diversity=0.6  [PASS]

[Final Recommendations]
╭──────────────────────────────────┬────────────────┬───────────┬───────╮
│ Title                            │ Artist         │ Genre     │ Score │
├──────────────────────────────────┼────────────────┼───────────┼───────┤
│ Spacewalk Thoughts               │ Orbit Bloom    │ ambient   │  2.46 │
│ Library Rain                     │ Paper Lanterns │ lofi      │  2.42 │
│ Midnight Coding                  │ LoRoom         │ lofi      │  2.39 │
│ Rainy Day Letters                │ Solenne        │ classical │  0.49 │
│ Moonlight Sonata Reimagined      │ Clara Voss     │ classical │  0.49 │
╰──────────────────────────────────┴────────────────┴───────────┴───────╯

[Quality]  avg_score=1.651  diversity=0.6  pass=True
[Final Profile]  genre=lofi  mood=chill  energy=0.2  mode=mood_first
```

**2. High energy rock for working out**

```
$ python src/agent.py
=== VibeFinder Agent ===
Describe the music you want: high energy rock music for working out

--- Agent ran 1 iteration(s) ---

[Agent Log]
  [1] PLAN   -> genre=rock  mood=energetic  energy=0.9  mode=energy_focused
         Reasoning : User explicitly wants high energy rock for working out, so rock
                     genre with energetic mood and maximum energy level (0.9) is appropriate.
  [1] ACT    -> mode=energy_focused, returned 5 songs
  [1] EVAL   -> avg_score=5.136  diversity=0.8  [PASS]

[Final Recommendations]
╭──────────────────────────┬──────────────┬───────────┬───────╮
│ Title                    │ Artist       │ Genre     │ Score │
├──────────────────────────┼──────────────┼───────────┼───────┤
│ Storm Runner             │ Voltline     │ rock      │  5.70 │
│ Night Drive Loop         │ Neon Echo    │ synthwave │  5.19 │
│ Concrete Sunrise         │ K-Flows      │ hip hop   │  4.98 │
│ Gym Hero                 │ Max Pulse    │ pop       │  4.93 │
│ Block Party Anthem       │ Crest Wave   │ hip hop   │  4.88 │
╰──────────────────────────┴──────────────┴───────────┴───────╯

[Quality]  avg_score=5.136  diversity=0.8  pass=True
[Final Profile]  genre=rock  mood=energetic  energy=0.9  mode=energy_focused
```

**3. Sad moody slow acoustic (agent revised once)**

```
$ python src/agent.py
=== VibeFinder Agent ===
Describe the music you want: sad and moody music, something slow and acoustic

--- Agent ran 2 iteration(s) ---

[Agent Log]
  [1] PLAN   -> genre=indie pop  mood=moody  energy=0.2  mode=mood_first
         Reasoning : Moody indie pop with low energy fits sad and slow acoustic requests.
  [1] ACT    -> mode=mood_first, returned 5 songs
  [1] EVAL   -> avg_score=1.198  diversity=0.8  [FAIL]
  [1] REVISE -> the average recommendation score was too low (1.20, threshold >= 1.2)
  [2] PLAN   -> genre=indie pop  mood=moody  energy=0.3  mode=mood_first
         Reasoning : Slightly raising energy to 0.3 to broaden proximity matches
                     while keeping the mood-first strategy.
  [2] ACT    -> mode=mood_first, returned 5 songs
  [2] EVAL   -> avg_score=1.216  diversity=1.0  [PASS]

[Final Recommendations]
╭──────────────────────────┬────────────────┬───────────┬───────╮
│ Title                    │ Artist         │ Genre     │ Score │
├──────────────────────────┼────────────────┼───────────┼───────┤
│ Late Night Feelings      │ Solenne        │ r&b       │  2.38 │
│ Night Drive Loop         │ Neon Echo      │ synthwave │  2.27 │
│ Spacewalk Thoughts       │ Orbit Bloom    │ ambient   │  0.49 │
│ Library Rain             │ Paper Lanterns │ lofi      │  0.47 │
│ Coffee Shop Stories      │ Slow Stereo    │ jazz      │  0.46 │
╰──────────────────────────┴────────────────┴───────────┴───────╯

[Quality]  avg_score=1.216  diversity=1.0  pass=True
[Final Profile]  genre=indie pop  mood=moody  energy=0.3  mode=mood_first
```

---

## Design Decisions

**Why agentic over single-pass?** The original system required the developer to define user profiles in code. An agentic loop lets a user describe what they want in plain English and lets the LLM figure out the structured parameters. The evaluate-and-revise loop also means the system can catch low-quality outputs and try again, which a single-pass pipeline cannot do.

**Why Claude Haiku?** This task is structured extraction, not creative generation. Haiku handles JSON parsing from natural language accurately and runs fast. Using Opus or Sonnet for a task this constrained would add cost and latency without any meaningful improvement in output quality.

**Why these quality thresholds?** The initial avg_score threshold was 1.5 but that turned out to be too strict for a small 18-song dataset. With only one rock song and limited genre coverage, cross-genre requests frequently landed below that bar even when the recommendations were reasonable. Lowering it to 1.2 better reflects what "good enough" looks like given the dataset size. The diversity threshold of 0.4 requires at least 2 unique genres in the top 5, which is a meaningful but achievable bar.

**Neutral valence and danceability defaults.** The LLM profile only asks for genre, mood, energy, and scoring mode. The base `score_song()` function also requires `target_valence` and `target_danceability`. Rather than expand the LLM spec or leave those keys missing, the agent fills them with 0.5 (neutral midpoint). This avoids key errors and does not bias results in either direction since most songs cluster near the middle of those ranges anyway.

---

## Testing Summary

The test harness at `tests/test_harness.py` runs 8 predefined inputs covering normal music requests and three guardrail edge cases. All 8 tests passed.

The avg_score threshold was originally 1.5 and was lowered to 1.2 after observing that genre-diverse requests on a small catalog consistently produced reasonable results that still fell below the stricter cutoff. The fix was applied in `src/agent.py` and the harness was updated to match.

All three guardrail cases (empty input, single character, non-music topic) correctly returned `results=[]` and `iterations=0` without making any API calls.

---

## Reflection

Building this made it clear how much scaffolding goes into making an LLM actually useful inside a larger system. The language model itself is only one piece. The guardrails, the evaluation logic, and the revise loop are what turn a single API call into something reliable enough to test. The gap between "the LLM returns a JSON object" and "the system behaves consistently" is where most of the real engineering work lives. It also showed that quality thresholds are not obvious up front. The first threshold I picked (1.5) looked reasonable until I ran it against the actual dataset and watched reasonable results get flagged as failures. That kind of calibration only happens through testing.

---

## Loom Walkthrough

Video walkthrough: [INSERT LOOM LINK]
