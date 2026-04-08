# 🎧 Model Card: Music Recommender Simulation

## 1. Model Name  

VibeFinder 1.0

---

## 2. Intended Use  

This system suggests up to 5 songs from an 18-song catalog based on a user's preferred genre, mood, energy level, valence, and danceability. It is built for classroom exploration to understand how content-based filtering works. It is not designed for real users or production use.

---

## 3. How the Model Works  

The recommender compares each song in the catalog to a user profile using five features. Genre and mood are categorical so they either match or they do not. A genre match adds 2.0 points and a mood match adds 1.0 point. Energy, valence, and danceability use proximity scoring where a song closer to the user's target value scores higher. Energy uses its full proximity score (max 1.0), while valence and danceability are each weighted at 0.5. All five components are summed into a final score and songs are ranked highest to lowest.

---

## 4. Data  

The catalog has 18 songs covering pop, lofi, rock, ambient, jazz, synthwave, indie pop, hip hop, classical, country, and R&B. Moods include happy, chill, intense, relaxed, focused, moody, energetic, sad, and romantic. The dataset was manually created for this simulation and does not reflect real listening data or user behavior. Sad and melancholic moods are slightly overrepresented in the expanded songs.

---

## 5. Strengths  

The system works well when a user's preferred genre is present in the catalog and their numerical preferences align with at least one song. Profiles like Lofi Listener and Rock Head get near-perfect top matches because their genres are represented and the song features align closely. The scoring is fully transparent since every recommendation includes a breakdown of exactly why each song scored the way it did.

---

## 6. Limitations and Bias 

The genre match bonus of 2.0 points dominates the scoring. A song with a perfect genre match will almost always outrank songs without one regardless of how well the other features align. The catalog only has one rock song so Rock Head gets a strong first result but weak fallback options. The system also has no diversity logic so it can surface multiple songs from the same artist back to back. Users whose preferred genre is not in the catalog get no genre bonus at all and the results feel generic.

---

## 7. Evaluation  

Three user profiles were tested: Pop Fan, Lofi Listener, and Rock Head. All three returned intuitive top results. One experiment was run where the genre bonus was halved to 1.0 and energy proximity was doubled. This caused Rooftop Lights (indie pop) to jump above Gym Hero (pop) for the Pop Fan profile because its energy alignment was stronger than Gym Hero's genre match under the new weights. The experiment showed how sensitive the ranking order is to weight choices.

---

## 8. Future Work  

Adding more songs per genre would reduce the fallback problem for underrepresented genres like rock. A diversity penalty that limits how many songs from the same artist can appear in the top results would make recommendations feel less repetitive. Supporting multi-feature mood tags instead of a single mood string would let the system handle more nuanced taste profiles.

---

## 9. Personal Reflection  

Building this made it clear how much a simple number like a genre bonus shapes everything downstream. Changing one weight by 1.0 point reshuffled the rankings in ways that felt arbitrary but were completely logical given the math. Real recommenders like Spotify are doing something structurally similar but with thousands of features and millions of data points, which makes it harder to see why any single recommendation happened. The most surprising thing was how confident the system feels even with only 18 songs and 5 features. It always returns an answer, even when that answer is not actually a good match.
