import os
from typing import Optional

import requests
from tabulate import tabulate

_TOKEN_URL = "https://accounts.spotify.com/api/token"
_SEARCH_URL = "https://api.spotify.com/v1/search"


def get_spotify_token() -> str:
    """
    Fetch a Spotify access token using the Client Credentials flow.
    Reads SPOTIFY_CLIENT_ID and SPOTIFY_CLIENT_SECRET from environment variables.
    Raises EnvironmentError if either variable is missing.
    Raises RuntimeError if the token request fails.
    """
    client_id = os.environ.get("SPOTIFY_CLIENT_ID")
    client_secret = os.environ.get("SPOTIFY_CLIENT_SECRET")

    missing = [v for v, val in [
        ("SPOTIFY_CLIENT_ID", client_id),
        ("SPOTIFY_CLIENT_SECRET", client_secret),
    ] if not val]
    if missing:
        raise EnvironmentError(
            f"Missing required environment variable(s): {', '.join(missing)}. "
            "Register an app at https://developer.spotify.com/dashboard and set them before running."
        )

    try:
        response = requests.post(
            _TOKEN_URL,
            data={"grant_type": "client_credentials"},
            auth=(client_id, client_secret),
            timeout=10,
        )
        response.raise_for_status()
    except requests.exceptions.RequestException as exc:
        raise RuntimeError(f"Spotify token request failed: {exc}") from exc

    return response.json()["access_token"]


def search_track(token: str, title: str, artist: str) -> Optional[dict]:
    """
    Search Spotify for a track by title and artist.
    Returns a dict with track metadata, or None if no match is found or
    the request fails.
    """
    headers = {"Authorization": f"Bearer {token}"}
    params = {"q": f"{title} {artist}", "type": "track", "limit": 1}

    try:
        response = requests.get(
            _SEARCH_URL,
            headers=headers,
            params=params,
            timeout=10,
        )
        response.raise_for_status()
        data = response.json()
    except requests.exceptions.RequestException:
        return None

    items = data.get("tracks", {}).get("items", [])
    if not items:
        return None

    track = items[0]
    artists = track.get("artists") or []

    return {
        "spotify_title": track.get("name"),
        "spotify_artist": artists[0]["name"] if artists else None,
        "spotify_album": track.get("album", {}).get("name"),
        "spotify_url": track.get("external_urls", {}).get("spotify"),
        "preview_url": track.get("preview_url"),
        "popularity": track.get("popularity"),
    }


def build_spotify_playlist(recommendations: list) -> list:
    """
    Match each recommendation against Spotify using the track title and artist.

    Takes the agent's results list: List[Tuple[song_dict, score, explanation]].
    Returns a list of dicts with local metadata and the Spotify match (or None).
    If the token cannot be fetched, all entries have spotify_match=None.
    """
    try:
        token = get_spotify_token()
    except (EnvironmentError, RuntimeError) as exc:
        print(f"[spotify] Could not obtain token: {exc}")
        return [
            {
                "local_title": song["title"],
                "local_artist": song["artist"],
                "local_score": score,
                "spotify_match": None,
            }
            for song, score, _ in recommendations
        ]

    playlist = []
    for song, score, _ in recommendations:
        match = search_track(token, song["title"], song["artist"])
        playlist.append({
            "local_title": song["title"],
            "local_artist": song["artist"],
            "local_score": score,
            "spotify_match": match,
        })
    return playlist


def display_playlist(playlist: list) -> None:
    """
    Print a formatted playlist table with Spotify metadata.
    Columns: #, Title, Artist, Our Score, Spotify Popularity, Spotify URL
    """
    rows = []
    matched = 0

    for idx, item in enumerate(playlist, start=1):
        match = item["spotify_match"]
        if match is not None:
            matched += 1
            pop_raw = match.get("popularity")
            popularity = pop_raw if pop_raw is not None else "N/A"
            url = match.get("spotify_url") or "N/A"
        else:
            popularity = "Not found"
            url = "Not found"

        rows.append([
            idx,
            item["local_title"],
            item["local_artist"],
            round(item["local_score"], 2),
            popularity,
            url,
        ])

    headers = ["#", "Title", "Artist", "Our Score", "Spotify Popularity", "Spotify URL"]
    print(tabulate(rows, headers=headers, tablefmt="rounded_outline"))
    print(f"\nSpotify matches: {matched}/{len(playlist)} tracks found")
