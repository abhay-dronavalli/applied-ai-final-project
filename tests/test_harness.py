import os
import sys
from tabulate import tabulate

# Mirror agent.py's import strategy so this works from the project root
# (python tests/test_harness.py) and from inside the tests/ directory.
try:
    from src.agent import run_agent
except ModuleNotFoundError:
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from src.agent import run_agent

# ── Test cases ────────────────────────────────────────────────────────────────

TEST_CASES = [
    {
        "description": "Chill lofi for studying",
        "input": "I want chill lofi music with low energy for studying",
        "expect_pass": True,
    },
    {
        "description": "High energy rock for working out",
        "input": "Give me high energy rock music for working out",
        "expect_pass": True,
    },
    {
        "description": "Jazz/classical relaxed and romantic",
        "input": "I love jazz and classical music, something relaxed and romantic",
        "expect_pass": True,
    },
    {
        "description": "Guardrail: too short (single char)",
        "input": "x",
        "expect_pass": False,
    },
    {
        "description": "Guardrail: empty string",
        "input": "",
        "expect_pass": False,
    },
    {
        "description": "Guardrail: not music related",
        "input": "I want to eat pizza and watch movies",
        "expect_pass": False,
    },
    {
        "description": "Happy and danceable good vibes",
        "input": "Something happy and danceable with good vibes",
        "expect_pass": True,
    },
    {
        "description": "Sad moody slow acoustic",
        "input": "Sad and moody music, something slow and acoustic",
        "expect_pass": True,
    },
]

# ── Evaluation logic ──────────────────────────────────────────────────────────

def _is_guardrail_case(expect_pass: bool) -> bool:
    return not expect_pass


def _check_result(output: dict, expect_pass: bool) -> tuple:
    """
    Returns (actual_pass: bool, reason: str, avg_score: str).

    Guardrail cases pass when results is empty and iterations == 0.
    Normal cases pass when quality is not None and quality["quality_pass"] is True.
    """
    if _is_guardrail_case(expect_pass):
        guardrail_fired = len(output["results"]) == 0 and output["iterations"] == 0
        # actual=False means the agent blocked/failed, which is correct for guardrail cases
        actual = not guardrail_fired
        reason = "" if guardrail_fired else (
            f"expected guardrail block but got {output['iterations']} iteration(s) "
            f"and {len(output['results'])} result(s)"
        )
        return actual, reason, "N/A"

    quality = output.get("quality")
    if quality is None:
        return False, "quality is None (agent may have errored out)", "N/A"

    actual = quality["quality_pass"]
    avg_score = str(quality["avg_score"])
    if actual:
        reason = ""
    else:
        parts = []
        if quality["avg_score"] < 1.5:
            parts.append(f"avg_score={quality['avg_score']} (need >= 1.5)")
        if quality["diversity_score"] < 0.4:
            parts.append(f"diversity={quality['diversity_score']} (need >= 0.4)")
        reason = "; ".join(parts) if parts else "quality_pass=False"
    return actual, reason, avg_score


# ── Runner ────────────────────────────────────────────────────────────────────

def run_harness():
    records = []
    failures = []

    total = len(TEST_CASES)
    passed = 0

    for idx, case in enumerate(TEST_CASES, start=1):
        desc = case["description"]
        user_input = case["input"]
        expect_pass = case["expect_pass"]

        print(f"[{idx}/{total}] Running: {desc!r} ...", end=" ", flush=True)

        output = run_agent(user_input)

        actual, reason, avg_score = _check_result(output, expect_pass)
        ok = actual == expect_pass
        if ok:
            passed += 1
            status = "PASS"
        else:
            status = "FAIL"
            failures.append({"num": idx, "description": desc, "reason": reason})

        print(status)

        records.append([
            idx,
            desc,
            "pass" if expect_pass else "fail (guardrail)",
            "fail (guardrail)" if (not actual and not expect_pass) else ("pass" if actual else "fail"),
            status,
            output["iterations"],
            avg_score,
        ])

    # ── Summary table ─────────────────────────────────────────────────────────
    headers = ["#", "Description", "Expected", "Actual", "Status", "Iterations", "Avg Score"]
    print()
    print(tabulate(records, headers=headers, tablefmt="rounded_outline"))

    # ── Pass/fail count ───────────────────────────────────────────────────────
    failed = total - passed
    print(f"\nResults: {passed}/{total} passed | {failed} failed")

    # ── Details for failures ──────────────────────────────────────────────────
    if failures:
        print("\nFailed tests:")
        for f in failures:
            print(f"  [{f['num']}] {f['description']}")
            if f["reason"]:
                print(f"       Reason: {f['reason']}")


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    run_harness()
