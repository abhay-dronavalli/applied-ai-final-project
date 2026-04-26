import os
import sys
import json
import anthropic
from tabulate import tabulate

# Support both `python src/agent.py` (project root on sys.path) and direct import
try:
    from src.recommender import load_songs, recommend_songs
    from src.rag import retrieve_context
except ModuleNotFoundError:
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from src.recommender import load_songs, recommend_songs
    from src.rag import retrieve_context

_DATA_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "data", "songs.csv",
)

# ── Valid vocabulary ──────────────────────────────────────────────────────────

VALID_GENRES = {
    "pop", "lofi", "rock", "ambient", "jazz", "synthwave",
    "indie pop", "hip hop", "classical", "country", "r&b",
}
VALID_MOODS = {
    "happy", "chill", "intense", "relaxed", "focused",
    "moody", "energetic", "sad", "romantic",
}
VALID_MODES = {"genre_first", "energy_focused", "mood_first"}

PERSONALITY_PROMPTS = {
    "hype_coach": (
        "You are an aggressive hype coach building a workout playlist. "
        "Prioritize maximum energy, intensity, and motivation. "
        "Always pick energy_focused mode. Push energy targets above 0.8. "
        "Your reasoning should sound like a coach firing someone up."
    ),
    "late_night_dj": (
        "You are a late night DJ curating a midnight session. "
        "Favor moody, atmospheric, and hypnotic tracks. "
        "Prefer synthwave, lofi, ambient, or r&b genres. "
        "Keep energy between 0.3 and 0.6. Use mood_first mode. "
        "Your reasoning should sound like a DJ setting the vibe."
    ),
    "study_guide": (
        "You are a focus coach building a distraction-free study playlist. "
        "Prioritize low energy, non-vocal genres like lofi, ambient, classical, or jazz. "
        "Keep energy below 0.4. Use genre_first mode. "
        "Your reasoning should explain why each choice minimizes distraction."
    ),
}

MUSIC_KEYWORDS = VALID_GENRES | VALID_MOODS | {
    "music", "song", "songs", "beat", "beats", "vibe", "vibes",
    "artist", "energy", "acoustic", "tempo", "genre", "mood",
    "playlist", "track", "tracks", "bpm", "listen", "play",
    "recommend", "sound", "tune", "tunes",
}

# ── LLM system prompt ─────────────────────────────────────────────────────────

_PLAN_SYSTEM = """You are a music preference parser. Given a natural language music request, extract the user's preferences and return ONLY a valid JSON object with exactly these fields:

- favorite_genre (string): one of: pop, lofi, rock, ambient, jazz, synthwave, indie pop, hip hop, classical, country, r&b
- favorite_mood (string): one of: happy, chill, intense, relaxed, focused, moody, energetic, sad, romantic
- target_energy (float): 0.0 to 1.0
- likes_acoustic (boolean): true or false
- scoring_mode (string): one of: genre_first, energy_focused, mood_first
- reasoning (string): brief explanation of why you chose these settings

Return ONLY the JSON object. No markdown fences, no explanation, no extra text.
You will be given retrieved knowledge base context about genres and moods. Use this context to make more informed decisions about the user profile."""


# ── Internal helpers ──────────────────────────────────────────────────────────

def _check_guardrails(user_input: str):
    """Return an error string if input fails guardrails, else None."""
    if not user_input or not user_input.strip():
        return "Error: Input cannot be empty."
    if len(user_input.strip()) < 5:
        return "Error: Input is too short. Please describe the kind of music you want."
    lowered = user_input.lower()
    if not any(kw in lowered for kw in MUSIC_KEYWORDS):
        return (
            "Error: Input does not appear to be music-related. "
            "Try describing a genre, mood, energy level, or type of song."
        )
    return None


def _call_llm(
    prompt: str,
    client: anthropic.Anthropic,
    context: str = "",
    system_prompt: str = _PLAN_SYSTEM,
) -> dict:
    """Call the LLM and return the parsed JSON profile dict."""
    if context:
        user_content = f"[Retrieved Context]\n{context}\n\n[User Request]\n{prompt}"
    else:
        user_content = prompt
    response = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=512,
        system=system_prompt,
        messages=[{"role": "user", "content": user_content}],
    )
    raw = response.content[0].text.strip()
    # Strip markdown code fences if the model adds them anyway
    if raw.startswith("```"):
        parts = raw.split("```")
        raw = parts[1]
        if raw.startswith("json"):
            raw = raw[4:]
        raw = raw.strip()
    return json.loads(raw)


def _build_user_prefs(profile: dict) -> dict:
    """Map LLM profile fields to the dict shape expected by recommend_songs."""
    genre = str(profile.get("favorite_genre", "pop")).lower()
    mood = str(profile.get("favorite_mood", "happy")).lower()
    if genre not in VALID_GENRES:
        genre = "pop"
    if mood not in VALID_MOODS:
        mood = "happy"
    target_energy = float(profile.get("target_energy", 0.5))
    target_energy = max(0.0, min(1.0, target_energy))
    return {
        "genre": genre,
        "mood": mood,
        "target_energy": target_energy,
        # Provide neutral defaults for fields not requested from the LLM
        # so score_song() has all required keys.
        "target_valence": 0.5,
        "target_danceability": 0.5,
    }


def _evaluate(results: list) -> dict:
    """
    Score the quality of a top-5 result set.

    diversity_score = unique genres / 5
    avg_score       = mean recommendation score
    quality_pass    = True if avg_score >= 1.2 AND diversity_score >= 0.4
    """
    if not results:
        return {"diversity_score": 0.0, "avg_score": 0.0, "quality_pass": False}
    unique_genres = len({song["genre"] for song, _, _ in results})
    diversity_score = unique_genres / 5
    avg_score = sum(sc for _, sc, _ in results) / len(results)
    quality_pass = avg_score >= 1.2 and diversity_score >= 0.4
    return {
        "diversity_score": round(diversity_score, 3),
        "avg_score": round(avg_score, 3),
        "quality_pass": quality_pass,
    }


# ── Public entry point ────────────────────────────────────────────────────────

def run_agent(user_input: str, personality: str = None) -> dict:
    """
    Run the plan → act → evaluate → revise loop (max 3 iterations).

    Returns:
        results      – final top-5 recommendation tuples (song, score, explanation)
        log          – list of step dicts recording every action taken
        iterations   – number of loops completed
        final_profile– last user_prefs dict + scoring_mode + reasoning
        quality      – final evaluation dict (or None on early exit)
    """
    # ── Guardrails ────────────────────────────────────────────────────────────
    # Personality provides sufficient musical context, so skip the guardrail.
    if not (personality and personality in PERSONALITY_PROMPTS):
        guard_error = _check_guardrails(user_input)
        if guard_error:
            return {
                "results": [],
                "log": [{"step": "guardrail", "message": guard_error}],
                "iterations": 0,
                "final_profile": None,
                "quality": None,
            }

    # ── Personality ───────────────────────────────────────────────────────────
    active_system = _PLAN_SYSTEM
    if personality and personality in PERSONALITY_PROMPTS:
        active_system = _PLAN_SYSTEM + "\n\n" + PERSONALITY_PROMPTS[personality]

    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        return {
            "results": [],
            "log": [{"step": "error", "message": "ANTHROPIC_API_KEY environment variable is not set."}],
            "iterations": 0,
            "final_profile": None,
            "quality": None,
        }

    client = anthropic.Anthropic(api_key=api_key)
    songs = load_songs(_DATA_PATH)

    rag_context = retrieve_context(user_input)

    agent_log = []
    agent_log.append({
        "iteration": 0,
        "step": "retrieve",
        "context_preview": rag_context[:200],
    })
    if personality and personality in PERSONALITY_PROMPTS:
        agent_log.append({"step": "personality", "mode": personality})
    iterations = 0
    results = []
    final_profile = None
    quality = None
    current_prompt = user_input

    while iterations < 3:
        iterations += 1

        # ── STEP 1: PLAN ──────────────────────────────────────────────────────
        plan_entry = {"iteration": iterations, "step": "plan", "prompt": current_prompt}
        try:
            profile = _call_llm(current_prompt, client, context=rag_context, system_prompt=active_system)
        except (json.JSONDecodeError, Exception) as exc:
            plan_entry["error"] = f"LLM parse error: {exc}"
            agent_log.append(plan_entry)
            break
        plan_entry["profile"] = profile
        agent_log.append(plan_entry)

        mode = profile.get("scoring_mode", "genre_first")
        if mode not in VALID_MODES:
            mode = "genre_first"
        user_prefs = _build_user_prefs(profile)
        final_profile = {
            **user_prefs,
            "scoring_mode": mode,
            "reasoning": profile.get("reasoning", ""),
        }

        # ── STEP 2: ACT ───────────────────────────────────────────────────────
        results = recommend_songs(user_prefs, songs, k=5, mode=mode)
        agent_log.append({
            "iteration": iterations,
            "step": "act",
            "mode": mode,
            "user_prefs": user_prefs,
            "num_results": len(results),
        })

        # ── STEP 3: EVALUATE ──────────────────────────────────────────────────
        quality = _evaluate(results)
        agent_log.append({"iteration": iterations, "step": "evaluate", **quality})

        if quality["quality_pass"]:
            break

        if iterations >= 3:
            break

        # ── STEP 4: REVISE ────────────────────────────────────────────────────
        issues = []
        if quality["avg_score"] < 1.5:
            issues.append(
                f"the average recommendation score was too low "
                f"({quality['avg_score']:.2f}, threshold >= 1.5)"
            )
        if quality["diversity_score"] < 0.4:
            issues.append(
                f"genre diversity was too low "
                f"({quality['diversity_score']:.2f}, threshold >= 0.4)"
            )
        revise_note = (
            "The previous profile did not meet quality requirements: "
            + "; ".join(issues)
            + ". Please adjust the genre, mood, energy, and scoring_mode to improve results."
        )
        current_prompt = f"{user_input}\n\n[Revision needed — {revise_note}]"
        agent_log.append({
            "iteration": iterations,
            "step": "revise",
            "issues": issues,
            "revised_prompt": current_prompt,
        })

    return {
        "results": results,
        "log": agent_log,
        "iterations": iterations,
        "final_profile": final_profile,
        "quality": quality,
    }


def run_baseline(user_input: str) -> dict:
    """Call run_agent with no personality. Used by the test harness for baseline comparison."""
    return run_agent(user_input)


# ── CLI entry point ───────────────────────────────────────────────────────────

if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    print("=== VibeFinder Agent ===")
    print("Personality modes:")
    print("  1. hype_coach    - High energy workout hype")
    print("  2. late_night_dj - Moody atmospheric midnight session")
    print("  3. study_guide   - Distraction-free focus playlist")
    print("  0. Default (no personality)")
    _MENU = {"1": "hype_coach", "2": "late_night_dj", "3": "study_guide"}
    personality_input = input("Choose a mode (0-3): ").strip()
    personality = _MENU.get(personality_input)
    user_input = input("Describe the music you want: ").strip()

    output = run_agent(user_input, personality=personality)

    print(f"\n--- Agent ran {output['iterations']} iteration(s) ---")
    if personality:
        print(f"\n[Personality Mode: {personality}]")

    # Print the step-by-step log
    print("\n[Agent Log]")
    for entry in output["log"]:
        step = entry.get("step", "?")
        it = entry.get("iteration", "-")
        if step == "guardrail":
            print(f"  GUARDRAIL : {entry['message']}")
        elif step == "error":
            print(f"  ERROR     : {entry['message']}")
        elif step == "plan":
            p = entry.get("profile", {})
            err = entry.get("error")
            if err:
                print(f"  [{it}] PLAN   ERROR : {err}")
            else:
                print(
                    f"  [{it}] PLAN   -> genre={p.get('favorite_genre')}  "
                    f"mood={p.get('favorite_mood')}  "
                    f"energy={p.get('target_energy')}  "
                    f"mode={p.get('scoring_mode')}"
                )
                print(f"         Reasoning : {p.get('reasoning', '')}")
        elif step == "act":
            print(
                f"  [{it}] ACT    -> mode={entry['mode']}  "
                f"returned {entry['num_results']} songs"
            )
        elif step == "evaluate":
            status = "PASS" if entry["quality_pass"] else "FAIL"
            print(
                f"  [{it}] EVAL   -> avg_score={entry['avg_score']}  "
                f"diversity={entry['diversity_score']}  [{status}]"
            )
        elif step == "revise":
            print(f"  [{it}] REVISE -> {'; '.join(entry['issues'])}")

    retrieve_entry = next((e for e in output["log"] if e.get("step") == "retrieve"), None)
    if retrieve_entry:
        print("\n[Retrieved Context Preview]")
        print(retrieve_entry["context_preview"])

    # Print the final song table
    if output["results"]:
        print("\n[Final Recommendations]")
        table_rows = [
            [s["title"], s["artist"], s["genre"], round(sc, 2), ex]
            for s, sc, ex in output["results"]
        ]
        headers = ["Title", "Artist", "Genre", "Score", "Reasons"]
        print(tabulate(table_rows, headers=headers, tablefmt="rounded_outline"))
    else:
        print("\nNo recommendations returned.")

    # Print quality summary
    if output["quality"]:
        q = output["quality"]
        print(
            f"\n[Quality]  avg_score={q['avg_score']}  "
            f"diversity={q['diversity_score']}  "
            f"pass={q['quality_pass']}"
        )

    # Print the final resolved profile
    if output["final_profile"]:
        fp = output["final_profile"]
        print(
            f"\n[Final Profile]  genre={fp['genre']}  mood={fp['mood']}  "
            f"energy={fp['target_energy']}  mode={fp['scoring_mode']}"
        )
        print(f"  Reasoning : {fp.get('reasoning', '')}")
