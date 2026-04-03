"""
Command line runner for the Music Recommender Simulation.

This file helps you quickly run and test your recommender.

You will implement the functions in recommender.py:
- load_songs
- score_song
- recommend_songs
"""

from recommender import load_songs, recommend_songs


def main() -> None:
    songs = load_songs("data/songs.csv") 

    pop_fan = {"genre": "pop", "mood": "happy", "target_energy": 0.8, "target_valence": 0.85, "target_danceability": 0.8}
    lofi_listener = {"genre": "lofi", "mood": "chill", "target_energy": 0.35, "target_valence": 0.6, "target_danceability": 0.55}
    rock_head = {"genre": "rock", "mood": "intense", "target_energy": 0.9, "target_valence": 0.45, "target_danceability": 0.65}

    recommendations = recommend_songs(pop_fan, songs, k=5)

    print("\nTop recommendations:\n")
    for rec in recommendations:
        # You decide the structure of each returned item.
        # A common pattern is: (song, score, explanation)
        song, score, explanation = rec
        print(f"{song['title']} - Score: {score:.2f}")
        print(f"Because: {explanation}")
        print()


if __name__ == "__main__":
    main()
