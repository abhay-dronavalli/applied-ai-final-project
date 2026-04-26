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
- **RAG retrieval**: before planning, the agent retrieves relevant genre and mood context from a local knowledge base of 12 documents and injects it into the LLM prompt
- **Personality modes**: three selectable modes (hype_coach, late_night_dj, study_guide) that measurably change genre selection, energy target, scoring mode, and reasoning tone
- **Demonstrated output difference**: the same input "give me something good" produced energy=0.9 with hype_coach vs energy=0.3 with study_guide

---

## System Architecture

```mermaid
flowchart TD
    A([User Input]) --> B{Guardrail Check}
    B -- "fails" --> C([Early Exit])
    B -- "passes" --> D[PLAN]
    D --> D1[Call LLM to parse profile and scoring mode]
    D1 --> E[ACT]
    E --> E1[Call recommend_songs and return top 5]
    E1 --> F[EVALUATE]
    F --> F1{Quality Pass?}
    F1 -- "Yes or max iterations reached" --> G([Final Output])
    F1 -- "No and iterations less than 3" --> H[REVISE]
    H --> H1[Build revised prompt with failure reason]
    H1 --> D
    style A fill:#4a90d9,color:#fff
    style C fill:#e05252,color:#fff
    style G fill:#4a90d9,color:#fff
    style D fill:#7b68ee,color:#fff
    style E fill:#5ba85b,color:#fff
    style F fill:#e0a030,color:#fff
    style H fill:#c47a20,color:#fff
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

   The agent will prompt you to select a personality mode before asking for your music request:

   ```
   Personality modes:
     1. hype_coach    - High energy workout hype
     2. late_night_dj - Moody atmospheric midnight session
     3. study_guide   - Distraction-free focus playlist
     0. Default (no personality)
   Choose a mode (0-3):
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

## Personality Modes

Three selectable personas each override the LLM's system prompt to bias genre, energy, and scoring mode in a specific direction. When a personality is selected, the guardrail check is also skipped since the persona itself provides musical context.

| Mode | Description | Typical Energy | Scoring Mode |
|---|---|---|---|
| `hype_coach` | Maximum energy workout fuel | ~0.9 | energy_focused |
| `late_night_dj` | Moody atmospheric midnight session | ~0.45 | mood_first |
| `study_guide` | Distraction-free focus playlist | ~0.3 | genre_first |

The same vague input ("give me something good") returned different results for each mode: hype_coach selected rock at energy=0.9, study_guide selected lofi at energy=0.3. The personality prompt is appended to the base system prompt so the JSON output format stays consistent across all modes.

---

## Design Decisions

**Why agentic over single-pass?** The original system required the developer to define user profiles in code. An agentic loop lets a user describe what they want in plain English and lets the LLM figure out the structured parameters. The evaluate-and-revise loop also means the system can catch low-quality outputs and try again, which a single-pass pipeline cannot do.

**Why Claude Haiku?** This task is structured extraction, not creative generation. Haiku handles JSON parsing from natural language accurately and runs fast. Using Opus or Sonnet for a task this constrained would add cost and latency without any meaningful improvement in output quality.

**Why these quality thresholds?** The initial avg_score threshold was 1.5 but that turned out to be too strict for a small 18-song dataset. With only one rock song and limited genre coverage, cross-genre requests frequently landed below that bar even when the recommendations were reasonable. Lowering it to 1.2 better reflects what "good enough" looks like given the dataset size. The diversity threshold of 0.4 requires at least 2 unique genres in the top 5, which is a meaningful but achievable bar.

**Why RAG before the plan step?** The LLM makes better genre and mode decisions when it has concrete facts about what a genre sounds like rather than relying purely on its training data. A request like "something for late night coding" is vague enough that the LLM could reasonably pick lofi, ambient, synthwave, or jazz. Injecting the knowledge base descriptions before the plan call narrows that ambiguity. In testing, adding RAG context raised the avg_score for the lofi studying request from 1.651 to 2.879 on the same input, a 74% improvement in recommendation score without changing any scoring weights.

**Neutral valence and danceability defaults.** The LLM profile only asks for genre, mood, energy, and scoring mode. The base `score_song()` function also requires `target_valence` and `target_danceability`. Rather than expand the LLM spec or leave those keys missing, the agent fills them with 0.5 (neutral midpoint). This avoids key errors and does not bias results in either direction since most songs cluster near the middle of those ranges anyway.

---

## Testing Summary

The test harness at `tests/test_harness.py` runs 8 predefined inputs covering normal music requests and three guardrail edge cases. The current result is 6/8 passing.

The 2 failures share the same root cause: the jazz/classical relaxed and romantic request and the sad/moody slow acoustic request both score below the 1.5 avg_score threshold. Both involve genres that are underrepresented in the 18-song dataset. Jazz, classical, country, and r&b each have only one or two songs, so requests that pull from those genres cannot produce enough strong matches to clear the threshold regardless of how many revisions the agent attempts.

All three guardrail cases (empty input, single character, non-music topic) correctly returned `results=[]` and `iterations=0` without making any API calls.

---

## Reflection

Building this made it clear how much scaffolding goes into making an LLM actually useful inside a larger system. The language model itself is only one piece. The guardrails, the evaluation logic, and the revise loop are what turn a single API call into something reliable enough to test. The gap between "the LLM returns a JSON object" and "the system behaves consistently" is where most of the real engineering work lives. It also showed that quality thresholds are not obvious up front. The first threshold I picked (1.5) looked reasonable until I ran it against the actual dataset and watched reasonable results get flagged as failures. That kind of calibration only happens through testing.

---

## Loom Walkthrough

Video walkthrough: https://youtu.be/VlUvnIydxqs
