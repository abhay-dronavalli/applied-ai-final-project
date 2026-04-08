# 🎵 Music Recommender Simulation

## Project Summary

In this project you will build and explain a small music recommender system.

Your goal is to:

- Represent songs and a user "taste profile" as data
- Design a scoring rule that turns that data into recommendations
- Evaluate what your system gets right and wrong
- Reflect on how this mirrors real world AI recommenders

This project simulates a content-based music recommender in Python. It scores songs from an 18-song catalog against a user taste profile using genre, mood, energy, valence, and danceability. The goal is to understand how simple scoring rules turn raw data into ranked suggestions and where those rules can go wrong.

---

## How The System Works

Real-world music recommenders like Spotify use two main approaches working together. Collaborative filtering looks at what other users with similar taste have listened to and assumes you might like the same things. Content-based filtering looks at the actual properties of songs, like tempo, mood, or energy, and finds songs that are similar to ones you already enjoy. Most production systems blend both approaches to get better results. One known challenge is the cold start problem, where a brand new user has no listening history, so the system has to rely on content-based signals alone until enough data is collected.

**Song features used in this simulation:**

- genre (categorical)
- mood (categorical)
- energy (0.0 to 1.0)
- valence (0.0 to 1.0)
- danceability (0.0 to 1.0)

**UserProfile stores:**

- favorite_genre
- favorite_mood
- target_energy
- target_valence
- target_danceability

**Algorithm recipe:**

The recommender scores each song by comparing it to the user's profile. A genre match adds 2.0 points and a mood match adds 1.0 point. For the numerical features, each one uses proximity scoring: the score is 1 minus the absolute difference between the song's value and the user's target, so songs closer to the user's preference score higher. Energy uses its full proximity score, while valence and danceability are each weighted at 0.5. All of these are summed into a single score for each song, and then songs are ranked from highest to lowest. The top k songs are returned as the final recommendations.

---

## Getting Started

### Setup

1. Create a virtual environment (optional but recommended):

   ```bash
   python -m venv .venv
   source .venv/bin/activate      # Mac or Linux
   .venv\Scripts\activate         # Windows

2. Install dependencies

```bash
pip install -r requirements.txt
```

3. Run the app:

```bash
python -m src.main
```

### Running Tests

Run the starter tests with:

```bash
pytest
```

You can add more tests in `tests/test_recommender.py`.

---

## Experiments You Tried

- Halving the genre match bonus from 2.0 to 1.0 and doubling the energy proximity weight caused Rooftop Lights (indie pop) to rank above Gym Hero (pop) for the Pop Fan profile. A song without a genre match but with stronger energy alignment overtook one that had the genre match. The original weights were restored after the experiment.
- Running the same catalog against three different profiles (Pop Fan, Lofi Listener, Rock Head) showed that the system works best when the user's preferred genre has multiple songs in the catalog. Rock Head had a near-perfect top result but weak options at positions 2 through 5 because only one rock song exists in the dataset.

---

## Limitations and Risks

- The catalog has only 18 songs so results for underrepresented genres fall back to energy and mood proximity quickly.
- The genre bonus of 2.0 points is large enough to dominate the score. Songs without a genre match rarely break into the top 2.
- No diversity logic exists so the same artist can appear multiple times in the top results.
- The system does not consider tempo, acousticness, or lyrics at all.

---

## Reflection

Read and complete `model_card.md`:

[**Model Card**](model_card.md)

Building this showed how directly scoring weights shape what a user sees. The genre bonus alone was enough to determine the top result in almost every case. Adjusting it by a single point changed the ranking in ways that felt surprising but made complete sense once the math was traced through. Real recommenders are doing the same thing at a much larger scale, which means the biases baked into their weights are just harder to see.

The filter bubble problem is more obvious in a small system like this. When a user's genre dominates the top results, they never see songs from other genres even if those songs match their energy and mood almost perfectly. A real platform running this logic at scale would quietly push users deeper into whatever genre they started with, which is exactly how filter bubbles form.


---

## 7. `model_card_template.md`

Combines reflection and model card framing from the Module 3 guidance. :contentReference[oaicite:2]{index=2}  

```markdown
# 🎧 Model Card - Music Recommender Simulation

## 1. Model Name

Give your recommender a name, for example:

> VibeFinder 1.0

---

## 2. Intended Use

- What is this system trying to do
- Who is it for

Example:

> This model suggests 3 to 5 songs from a small catalog based on a user's preferred genre, mood, and energy level. It is for classroom exploration only, not for real users.

---

## 3. How It Works (Short Explanation)

Describe your scoring logic in plain language.

- What features of each song does it consider
- What information about the user does it use
- How does it turn those into a number

Try to avoid code in this section, treat it like an explanation to a non programmer.

---

## 4. Data

Describe your dataset.

- How many songs are in `data/songs.csv`
- Did you add or remove any songs
- What kinds of genres or moods are represented
- Whose taste does this data mostly reflect

---

## 5. Strengths

Where does your recommender work well

You can think about:
- Situations where the top results "felt right"
- Particular user profiles it served well
- Simplicity or transparency benefits

---

## 6. Limitations and Bias

Where does your recommender struggle

Some prompts:
- Does it ignore some genres or moods
- Does it treat all users as if they have the same taste shape
- Is it biased toward high energy or one genre by default
- How could this be unfair if used in a real product

---

## 7. Evaluation

How did you check your system

Examples:
- You tried multiple user profiles and wrote down whether the results matched your expectations
- You compared your simulation to what a real app like Spotify or YouTube tends to recommend
- You wrote tests for your scoring logic

You do not need a numeric metric, but if you used one, explain what it measures.

---

## 8. Future Work

If you had more time, how would you improve this recommender

Examples:

- Add support for multiple users and "group vibe" recommendations
- Balance diversity of songs instead of always picking the closest match
- Use more features, like tempo ranges or lyric themes

---

## 9. Personal Reflection

A few sentences about what you learned:

- What surprised you about how your system behaved
- How did building this change how you think about real music recommenders
- Where do you think human judgment still matters, even if the model seems "smart"

