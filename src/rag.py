import os
from pathlib import Path

_KB_PATH = Path(__file__).resolve().parent.parent / "knowledge_base"

# Ordered longest-first so multi-word genres ("indie pop", "hip hop") are
# matched before their single-word components could be.
_GENRE_FILE_MAP = {
    "indie pop":  "indie-pop.txt",
    "hip hop":    "hip-hop.txt",
    "r&b":        "r-and-b.txt",
    "synthwave":  "synthwave.txt",
    "classical":  "classical.txt",
    "ambient":    "ambient.txt",
    "country":    "country.txt",
    "lofi":       "lofi.txt",
    "jazz":       "jazz.txt",
    "rock":       "rock.txt",
    "pop":        "pop.txt",
}

_VALID_MOODS = {
    "happy", "chill", "intense", "relaxed", "focused",
    "moody", "energetic", "sad", "romantic",
}

_DEFAULT_GENRES = ["lofi.txt", "pop.txt", "ambient.txt"]


def _detect_genres(text: str) -> list:
    """Return file names for every genre keyword found in text, ordered by position in text."""
    matches = []
    seen_files = set()
    for genre_name, filename in _GENRE_FILE_MAP.items():
        pos = text.find(genre_name)
        if pos != -1 and filename not in seen_files:
            matches.append((pos, filename))
            seen_files.add(filename)
    matches.sort(key=lambda x: x[0])
    return [filename for _, filename in matches]


def _detect_mood(text: str) -> str:
    """Return the first mood keyword found in text, or empty string."""
    for mood in _VALID_MOODS:
        if mood in text:
            return mood
    return ""


def _load_genre_file(filename: str) -> str:
    """Read and return the content of a genre file, or empty string if missing."""
    path = _KB_PATH / filename
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8").strip()


def _extract_mood_paragraph(mood: str) -> str:
    """
    Read moods.txt and return only the paragraph for the requested mood.
    Paragraphs are delimited by [mood_name] markers.
    Returns empty string if mood not found or file missing.
    """
    moods_path = _KB_PATH / "moods.txt"
    if not moods_path.exists():
        return ""

    content = moods_path.read_text(encoding="utf-8")
    marker = f"[{mood}]"
    start = content.find(marker)
    if start == -1:
        return ""

    # Text starts after the marker line
    body_start = content.find("\n", start) + 1
    # End is either the next "[" marker or end of file
    next_marker = content.find("[", body_start)
    body = content[body_start:next_marker] if next_marker != -1 else content[body_start:]
    return body.strip()


def _rank_genres_by_frequency(text: str, top_k: int) -> list:
    """
    Count how many times each genre name appears as a substring in text.
    Returns up to top_k file names for the genres with the highest counts.
    Falls back to _DEFAULT_GENRES if nothing scores above zero.
    """
    counts = {}
    for genre_name, filename in _GENRE_FILE_MAP.items():
        count = text.count(genre_name)
        if count > 0:
            counts[filename] = counts.get(filename, 0) + count

    if not counts:
        return _DEFAULT_GENRES[:top_k]

    ranked = sorted(counts, key=lambda f: counts[f], reverse=True)
    return ranked[:top_k]


def retrieve_context(user_input: str, top_k: int = 3) -> str:
    """
    Build a RAG context string from the knowledge base for the given user input.

    Steps:
    1. Detect genre keywords and load their .txt files.
    2. If no genres are detected, rank genres by substring frequency and load
       the top_k most relevant, falling back to lofi, pop, and ambient.
    3. Detect a mood keyword and extract its paragraph from moods.txt.
    4. Return all retrieved text concatenated with section headers.
    """
    lowered = user_input.lower()

    genre_files = _detect_genres(lowered)
    if not genre_files:
        genre_files = _rank_genres_by_frequency(lowered, top_k)

    sections = []

    for filename in genre_files:
        genre_label = filename.replace(".txt", "").replace("-", " ").replace("and ", "").strip()
        # Restore "r&b" label (stored as "r-and-b")
        if filename == "r-and-b.txt":
            genre_label = "r&b"
        content = _load_genre_file(filename)
        if content:
            sections.append(f"=== Genre: {genre_label} ===\n{content}")

    mood = _detect_mood(lowered)
    if mood:
        mood_text = _extract_mood_paragraph(mood)
        if mood_text:
            sections.append(f"=== Mood Context: {mood} ===\n{mood_text}")

    if not sections:
        return ""

    return "\n\n".join(sections)


def list_knowledge_base() -> list:
    """Return the names of all .txt files in the knowledge_base/ folder."""
    if not _KB_PATH.exists():
        return []
    return sorted(p.name for p in _KB_PATH.iterdir() if p.suffix == ".txt")
