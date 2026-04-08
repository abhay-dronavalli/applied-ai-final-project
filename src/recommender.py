import csv
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass

@dataclass
class Song:
    """
    Represents a song and its attributes.
    Required by tests/test_recommender.py
    """
    id: int
    title: str
    artist: str
    genre: str
    mood: str
    energy: float
    tempo_bpm: float
    valence: float
    danceability: float
    acousticness: float

@dataclass
class UserProfile:
    """
    Represents a user's taste preferences.
    Required by tests/test_recommender.py
    """
    favorite_genre: str
    favorite_mood: str
    target_energy: float
    likes_acoustic: bool

class Recommender:
    """
    OOP implementation of the recommendation logic.
    Required by tests/test_recommender.py
    """
    def __init__(self, songs: List[Song]):
        self.songs = songs

    def recommend(self, user: UserProfile, k: int = 5) -> List[Song]:
        # TODO: Implement recommendation logic
        return self.songs[:k]

    def explain_recommendation(self, user: UserProfile, song: Song) -> str:
        # TODO: Implement explanation logic
        return "Explanation placeholder"

def load_songs(csv_path: str) -> List[Dict]:
    """
    Loads songs from a CSV file.
    Required by src/main.py
    """
    songs = []
    with open(csv_path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            row["id"] = int(row["id"])
            row["popularity"] = int(row["popularity"])
            row["release_decade"] = int(row["release_decade"])
            for field in ("energy", "tempo_bpm", "valence", "danceability", "acousticness"):
                row[field] = float(row[field])
            songs.append(row)
    return songs

def score_song(user_prefs: Dict, song: Dict) -> Tuple[float, List[str]]:
    """
    Scores a single song against user preferences.
    Required by recommend_songs() and src/main.py
    """
    score = 0.0
    reasons = []

    if song["genre"] == user_prefs["genre"]:
        score += 2.0
        reasons.append("genre match (+2.0)")

    if song["mood"] == user_prefs["mood"]:
        score += 1.0
        reasons.append("mood match (+1.0)")

    energy_value = 1.0 - abs(song["energy"] - user_prefs["target_energy"])
    score += energy_value
    reasons.append(f"energy proximity (+{energy_value:.2f})")

    valence_value = (1.0 - abs(song["valence"] - user_prefs["target_valence"])) * 0.5
    score += valence_value
    reasons.append(f"valence proximity (+{valence_value:.2f})")

    danceability_value = (1.0 - abs(song["danceability"] - user_prefs["target_danceability"])) * 0.5
    score += danceability_value
    reasons.append(f"danceability proximity (+{danceability_value:.2f})")

    popularity_value = (float(song["popularity"]) / 100) * 0.5
    score += popularity_value
    reasons.append(f"popularity bonus (+{popularity_value:.2f})")

    if int(song["release_decade"]) == user_prefs.get("preferred_decade", 2020):
        score += 0.5
        reasons.append("decade match (+0.5)")

    if song["mood_tag"] == user_prefs.get("preferred_mood_tag", ""):
        score += 0.75
        reasons.append("mood tag match (+0.75)")

    return (score, reasons)

def score_song_by_mode(user_prefs: Dict, song: Dict, mode: str) -> Tuple[float, List[str]]:
    """
    Scores a single song using one of three named scoring strategies.
    Falls back to score_song if mode is unrecognized.
    """
    score = 0.0
    reasons = []

    if mode == "genre_first":
        if song["genre"] == user_prefs["genre"]:
            score += 3.0
            reasons.append("genre match (+3.0)")

        if song["mood"] == user_prefs["mood"]:
            score += 1.0
            reasons.append("mood match (+1.0)")

        energy_value = (1.0 - abs(song["energy"] - user_prefs["target_energy"])) * 0.5
        score += energy_value
        reasons.append(f"energy proximity (+{energy_value:.2f})")

        return (score, reasons)

    elif mode == "energy_focused":
        energy_value = (1.0 - abs(song["energy"] - user_prefs["target_energy"])) * 3.0
        score += energy_value
        reasons.append(f"energy proximity (+{energy_value:.2f})")

        valence_value = (1.0 - abs(song["valence"] - user_prefs["target_valence"])) * 1.5
        score += valence_value
        reasons.append(f"valence proximity (+{valence_value:.2f})")

        danceability_value = (1.0 - abs(song["danceability"] - user_prefs["target_danceability"])) * 1.5
        score += danceability_value
        reasons.append(f"danceability proximity (+{danceability_value:.2f})")

        return (score, reasons)

    elif mode == "mood_first":
        if song["mood"] == user_prefs["mood"]:
            score += 2.0
            reasons.append("mood match (+2.0)")

        if song["mood_tag"] == user_prefs.get("preferred_mood_tag", ""):
            score += 1.5
            reasons.append("mood tag match (+1.5)")

        energy_value = (1.0 - abs(song["energy"] - user_prefs["target_energy"])) * 0.5
        score += energy_value
        reasons.append(f"energy proximity (+{energy_value:.2f})")

        return (score, reasons)

    else:
        return score_song(user_prefs, song)


def apply_diversity_penalty(ranked_results: List[Tuple[Dict, float, str]], max_per_artist: int = 2) -> List[Tuple[Dict, float, str]]:
    """
    Filters ranked results to limit how many songs from the same artist appear.
    """
    artist_counts = {}
    filtered = []

    for result in ranked_results:
        song, score, explanation = result
        artist = song["artist"]

        if artist not in artist_counts:
            artist_counts[artist] = 0

        if artist_counts[artist] < max_per_artist:
            filtered.append(result)
            artist_counts[artist] = artist_counts[artist] + 1

    return filtered


def recommend_songs(user_prefs: Dict, songs: List[Dict], k: int = 5, mode: Optional[str] = None) -> List[Tuple[Dict, float, str]]:
    """
    Functional implementation of the recommendation logic.
    Required by src/main.py
    """
    scored_songs = []

    for song in songs:
        if mode is None:
            score, reasons = score_song(user_prefs, song)
        else:
            score, reasons = score_song_by_mode(user_prefs, song, mode)
        explanation = ", ".join(reasons)
        scored_songs.append((song, score, explanation))

    ranked = sorted(scored_songs, key=lambda x: x[1], reverse=True)

    diverse = apply_diversity_penalty(ranked)

    return diverse[:k]
