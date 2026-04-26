# Model Card: VibeFinder Agent

## Intended Use

VibeFinder is a music recommendation agent built for an AI course final project. It takes a natural language description of what someone wants to listen to, retrieves relevant genre and mood context from a local knowledge base using RAG, translates that into a structured taste profile using an LLM, and returns a ranked list of songs from a curated catalog. Users can also select from three personality modes (hype_coach, late_night_dj, study_guide) that bias the LLM toward specific energy ranges, genres, and scoring strategies. The intended audience is students and educators exploring how agentic AI systems work in practice. It is not designed for production use or real user data.

---

## Base Model

**claude-haiku-4-5-20251001** via the Anthropic API.

Haiku handles the natural language parsing step: it receives the user's input and returns a JSON object with fields for genre, mood, target energy, acoustic preference, scoring mode, and a brief reasoning string. It is called again during the revise step if the first result set does not meet quality thresholds. All other logic (scoring, diversity filtering, evaluation) is deterministic Python code in `src/recommender.py` and `src/agent.py`.

---

## AI Collaboration

Claude Code was used during development as a coding assistant. Two examples stand out.

One genuinely helpful suggestion was the try/except import pattern used in both `src/agent.py` and `tests/test_harness.py`. When Python runs a file directly, the working directory affects how module imports resolve. The try/except block that falls back to inserting the project root into `sys.path` was suggested by Claude Code and solved an import error that would have made the CLI and test harness fragile depending on where the user ran the command from.

A second helpful suggestion was the numbered menu for personality selection in the CLI. The original implementation required users to type the full mode name (hype_coach, late_night_dj, study_guide), which is easy to mistype. Claude Code suggested mapping number keys to mode names with a dict lookup, which made the interface cleaner and eliminated invalid-input errors with no extra validation code needed.

One suggestion that needed correction was the initial `avg_score` quality threshold of 1.5. Claude Code proposed this as a reasonable bar for "good" recommendations, but after running the test harness against the actual 18-song dataset it turned out to be too strict. Several clearly reasonable result sets for cross-genre or mood-first requests scored between 1.2 and 1.5 because the catalog is too small to produce strong matches outside a user's primary genre. The threshold was lowered to 1.2 after testing, which better fits the dataset's actual score distribution.

---

## Limitations and Biases

**Small dataset.** The catalog has 18 songs. For underrepresented genres, the agent runs out of strong matches quickly and fills the bottom of the top-5 with songs that are only loosely relevant. This is a dataset problem, not a model problem, but it directly affects output quality.

**Genre imbalance.** Rock has one song in the catalog. Any user who asks for rock music will get that one song as the top result and then a drop-off into unrelated genres at positions 2 through 5. The same applies to ambient, jazz, synthwave, and indie pop, each of which has only one representative.

**Hardcoded neutral defaults.** The agent fills `target_valence` and `target_danceability` with 0.5 because the LLM profile spec does not include those fields. This avoids key errors but means the scoring for those two features is the same for every user, regardless of what they actually described.

**Filter bubble risk.** The `genre_first` scoring mode boosts genre match to 3.0 points. When the LLM selects this mode for a single-genre request, the top results are almost entirely from that one genre. Users never see songs from other genres that might match their energy or mood well. This is the same filter bubble dynamic that real recommenders produce at scale.

**Personality modes amplify filter bubbles.** The hype_coach personality will almost always steer toward high-energy songs with energy_focused mode, regardless of what the catalog diversity looks like. A user who selects hype_coach and gets five high-energy tracks from three genres has no way to know they are being filtered into a narrow slice of the catalog. The personality provides a useful signal but it actively overrides the diversity logic that the evaluation step is supposed to catch.

---

## Guardrails and Reliability

Three input guardrails block requests before any API call is made:

1. Empty or whitespace-only input
2. Input shorter than 5 characters
3. Input with no recognizable music-related words (checked against a keyword list of all valid genres, moods, and general music terms)

The agent also runs a quality evaluation after every ACT step. If the result set's average score is below 1.2 or genre diversity is below 0.4 (fewer than 2 unique genres in the top 5), the agent builds a revised prompt that describes the specific failure and calls the LLM again. This loop runs up to 3 times before the agent returns whatever it has. Every step is logged and included in the return value so the caller can inspect exactly what happened.

---

## Future Improvements

**Larger and more balanced dataset.** Adding 5 to 10 songs per genre would immediately improve result quality for underrepresented genres and make the diversity threshold more meaningful.

**User feedback loop.** Right now the agent has no way to learn which recommendations a user liked or skipped. Even a simple thumbs up/down signal per session could be used to adjust weights in a follow-up query.

**Expose valence and danceability to the LLM.** Including these two fields in the LLM profile spec would let users say things like "I want something you can dance to" or "something atmospheric and still" and have that actually affect the scoring. Right now those signals are ignored.

**RAG for artist and genre context.** This is now implemented via `src/rag.py` and a 12-document knowledge base. The next step would be expanding the knowledge base to include artist-level descriptions and cross-genre recommendation logic.

**Personality mode web UI.** Right now personality selection is a CLI numbered menu. Exposing it as a dropdown in a Streamlit or web interface would make the feature more accessible and easier to demonstrate.

**More personality types and custom personalities.** The current three modes cover workout, late night, and study use cases. Adding types like morning_commute, party_host, or wind_down would cover more listener situations. Allowing users to write their own personality description in a text field would make the system genuinely personalizable.

---

## Testing Results

The test harness at `tests/test_harness.py` defines 8 test cases: 5 normal music requests expected to pass quality checks and 3 guardrail edge cases expected to block. All 8 passed.

The avg_score threshold was originally set at 1.5 and was lowered to 1.2 during testing. The change was made after observing that cross-genre and mood-first requests on the small catalog produced reasonable recommendations that consistently fell below the stricter threshold. Lowering it brought the harness into alignment with what the dataset can actually deliver.
