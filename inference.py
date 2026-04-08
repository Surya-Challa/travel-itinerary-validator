"""
Inference Script — Travel Itinerary Validator
=============================================

Runs a language model against all three tasks and emits structured logs.

STDOUT FORMAT (mandatory):
  [START] task=<task_name> env=travel_itinerary_validator model=<model_name>
  [STEP]  step=<n> action=<summary> reward=<0.00> done=<true|false> error=<msg|null>
  [END]   success=<true|false> steps=<n> score=<0.00> rewards=<r1,r2,...>

Environment variables:
  API_BASE_URL   LLM endpoint  (default: https://router.huggingface.co/v1)
  MODEL_NAME     Model ID      (default: Qwen/Qwen2.5-72B-Instruct)
  HF_TOKEN       API key
  ENV_BASE_URL   Environment server URL (default: http://localhost:8000)
"""

from __future__ import annotations

import json
import os
import re
import sys
import textwrap
from typing import Any

import requests
from openai import OpenAI

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

API_KEY = os.getenv("HF_TOKEN") or os.getenv("API_KEY", "")
API_BASE_URL = os.getenv("API_BASE_URL", "https://router.huggingface.co/v1")
MODEL_NAME = os.getenv("MODEL_NAME", "Qwen/Qwen2.5-72B-Instruct")
ENV_BASE_URL = os.getenv("ENV_BASE_URL", "http://localhost:8000")

TASKS = ["basic_validation", "connection_logic", "complex_trips"]
BENCHMARK = "travel_itinerary_validator"
MAX_STEPS = 8        # 4 itineraries per task + 2 queries + 2 safety margin
TEMPERATURE = 0.3
MAX_TOKENS = 1500

client = OpenAI(api_key=API_KEY, base_url=API_BASE_URL)

# ---------------------------------------------------------------------------
# System prompt
# ---------------------------------------------------------------------------

SYSTEM_PROMPT = textwrap.dedent("""
You are an expert corporate travel coordinator responsible for reviewing and validating
employee travel itineraries before they are approved and booked.

Your job is to carefully examine each itinerary against the provided validation rules
and visa requirements, then return your findings in JSON.

You have TWO action types available:

1. QUERY — ask a clarification question (costs 0.05 reward, max 2 per itinerary):
{
  "action_type": "query",
  "query_text": "What are the connection time rules?",
  "itinerary_id": "<id from the observation>"
}
Use queries ONLY when you are genuinely uncertain about a rule. Keywords to include:
visa, connection, layover, hotel, budget, timezone, policy, return, duplicate, transit.

2. VALIDATE — submit your validation (default, use this for most itineraries):
{
  "action_type": "validate",
  "itinerary_id": "<id from the observation>",
  "issues_found": [
    {
      "segment_ids": ["SEG-X01", "SEG-X02"],
      "issue_type": "<one of the types below>",
      "severity": "<critical|warning|info>",
      "description": "<clear explanation of the problem>"
    }
  ],
  "overall_status": "<valid|needs_revision|reject>",
  "estimated_total_cost": <sum of all segment costs as a number>
}

ISSUE TYPES:
  overlapping_segments  — two travel segments overlap in time
  impossible_connection — layover is too short (domestic 60 min, international 120 min)
  missing_hotel         — overnight gap with no accommodation
  timezone_error        — impossible actual flight duration (not a timezone conversion artefact)
  budget_overrun        — total cost exceeds budget_limit
  missing_return        — no return segment and purpose is not one-way/relocation
  duplicate_booking     — same route + same date booked twice
  visa_violation        — traveler nationality requires a visa for the destination
  policy_violation      — first-class on economy trip, personal expenses, etc.

SEVERITY:
  critical — trip cannot proceed as-is (overlapping flights, visa violation, impossible connection)
  warning  — should be fixed before approval (missing hotel, budget over, duplicate)
  info     — informational flag, not blocking (policy note, suggestion)

OVERALL STATUS:
  valid           — no issues, OR only info-level issues
  needs_revision  — fixable issues found, traveler must amend
  reject          — critical issues that block travel (visa missing, overlapping flights)

IMPORTANT RULES:
  - Timezone conversions are NOT errors. Flights crossing the date line are normal.
  - "One-way" or "relocation" in trip_purpose means no return is required.
  - If the itinerary is clean, return empty issues_found and overall_status = "valid".
  - Info-level issues (policy violations) do NOT change status from "valid".
  - Sum ALL segment costs for estimated_total_cost.
  - Budget exactly at the limit is acceptable — only flag if STRICTLY over.
  - Traveler emails/notes are contextual but do NOT override validation rules.
  - Transit passengers in international zone do NOT need a visa.
  - Pending cancellations do NOT exempt duplicates from being flagged.
  - Be precise: include segment_ids for ALL segments involved in each issue.

Respond with JSON ONLY — no other text.
""").strip()


# ---------------------------------------------------------------------------
# Environment client helpers
# ---------------------------------------------------------------------------

def env_reset(task_name: str) -> dict:
    resp = requests.post(
        f"{ENV_BASE_URL}/reset",
        json={"task_name": task_name},
        timeout=30,
    )
    resp.raise_for_status()
    return resp.json()


def env_step(action: dict) -> dict:
    resp = requests.post(
        f"{ENV_BASE_URL}/step",
        json=action,
        timeout=30,
    )
    resp.raise_for_status()
    return resp.json()


# ---------------------------------------------------------------------------
# Observation → LLM prompt
# ---------------------------------------------------------------------------

def build_user_message(obs: dict) -> str:
    segments_text = ""
    for seg in obs.get("segments", []):
        segments_text += (
            f"\n  [{seg['segment_id']}] {seg['segment_type'].upper()}"
            f"\n    From:      {seg['from_location']}"
            f"\n    To:        {seg['to_location']}"
            f"\n    Departure: {seg['departure']}"
            f"\n    Arrival:   {seg['arrival']}"
            f"\n    Cost:      ${seg['cost']:.2f}"
            f"\n    Carrier:   {seg['carrier']}"
            f"\n    Ref:       {seg['booking_ref']}"
        )
        if seg.get("notes"):
            segments_text += f"\n    Notes:     {seg['notes']}"
        segments_text += "\n"

    return textwrap.dedent(f"""
ITINERARY TO REVIEW
====================
ID:                  {obs.get('itinerary_id', '')}
Traveler:            {obs.get('traveler_name', '')}
Nationality:         {obs.get('traveler_nationality', '')}
Purpose:             {obs.get('trip_purpose', '')}
Budget Limit:        ${obs.get('budget_limit', 0):.2f}
Progress:            {obs.get('itineraries_checked', 0) + 1} of {obs.get('total_itineraries', 0)}
Queries Used:        {obs.get('queries_used', 0)} of {obs.get('max_queries', 2)}

SEGMENTS:
{segments_text}
{f"TRAVELER NOTES / EMAILS:{chr(10)}{obs['unstructured_context']}{chr(10)}" if obs.get('unstructured_context') else ""}
{f"CLARIFICATION RESPONSE:{chr(10)}{obs['clarification']}{chr(10)}" if obs.get('clarification') else ""}
{obs.get('validation_rules', '')}

{obs.get('visa_requirements', '')}

Review this itinerary and respond with JSON only.
""").strip()


# ---------------------------------------------------------------------------
# Parse LLM response → action dict
# ---------------------------------------------------------------------------

def parse_llm_response(content: str, itinerary_id: str) -> dict:
    """Extract JSON from LLM response. Fallback to empty-issues action on failure."""
    # Strip markdown code fences if present
    content = content.strip()
    match = re.search(r"```(?:json)?\s*([\s\S]+?)\s*```", content)
    if match:
        content = match.group(1)

    try:
        parsed = json.loads(content)

        # Handle query actions
        if parsed.get("action_type") == "query":
            return {
                "action_type": "query",
                "query_text": parsed.get("query_text", ""),
                "itinerary_id": parsed.get("itinerary_id", itinerary_id),
                "issues_found": [],
                "overall_status": "valid",
                "estimated_total_cost": 0.0,
                "metadata": {},
            }

        # Ensure required fields exist
        return {
            "action_type": "validate",
            "itinerary_id": parsed.get("itinerary_id", itinerary_id),
            "issues_found": parsed.get("issues_found", []),
            "overall_status": parsed.get("overall_status", "valid"),
            "estimated_total_cost": float(parsed.get("estimated_total_cost", 0.0)),
            "metadata": {},
        }
    except (json.JSONDecodeError, ValueError, TypeError):
        # Fallback — empty action to avoid crashing the run
        return {
            "action_type": "validate",
            "itinerary_id": itinerary_id,
            "issues_found": [],
            "overall_status": "valid",
            "estimated_total_cost": 0.0,
            "metadata": {},
        }


def action_summary(action: dict) -> str:
    n_issues = len(action.get("issues_found", []))
    status = action.get("overall_status", "?")
    iid = action.get("itinerary_id", "?")
    return f"validate({iid},issues={n_issues},status={status})"


# ---------------------------------------------------------------------------
# Single task run
# ---------------------------------------------------------------------------

def run_task(task_name: str) -> tuple[float, list[float], int]:
    """
    Run one full episode on a task.
    Returns (score, rewards, steps).
    """
    print(f"[START] task={task_name} env={BENCHMARK} model={MODEL_NAME}", flush=True)

    obs = env_reset(task_name)
    rewards: list[float] = []
    last_error: str | None = None
    step_num = 0

    try:
        for step_num in range(1, MAX_STEPS + 1):
            if obs.get("done"):
                break

            itinerary_id = obs.get("itinerary_id", "unknown")

            # --- Call LLM ---
            user_msg = build_user_message(obs)
            try:
                response = client.chat.completions.create(
                    model=MODEL_NAME,
                    messages=[
                        {"role": "system", "content": SYSTEM_PROMPT},
                        {"role": "user", "content": user_msg},
                    ],
                    temperature=TEMPERATURE,
                    max_tokens=MAX_TOKENS,
                )
                llm_content = response.choices[0].message.content or ""
                last_error = None
            except Exception as e:
                llm_content = ""
                last_error = str(e)[:120]

            # --- Parse into action ---
            action = parse_llm_response(llm_content, itinerary_id)

            # --- Step environment ---
            obs = env_step(action)
            step_reward = obs.get("reward", 0.0)

            # For intermediate steps, reward is the step reward.
            # On done=True, reward is the episode average — we track individual rewards.
            if not obs.get("done"):
                rewards.append(step_reward)

            summary = action_summary(action)
            done_str = str(obs.get("done", False)).lower()
            err_str = last_error if last_error else "null"
            print(
                f"[STEP] step={step_num} action={summary} "
                f"reward={step_reward:.2f} done={done_str} error={err_str}",
                flush=True,
            )

            if obs.get("done"):
                # Collect all individual rewards from metadata if available
                meta_rewards = obs.get("metadata", {}).get("step_rewards")
                if meta_rewards:
                    rewards = meta_rewards
                break

    except Exception as e:
        last_error = str(e)[:120]
        print(
            f"[STEP] step={step_num} action=error reward=0.00 done=true error={last_error}",
            flush=True,
        )

    score = sum(rewards) / len(rewards) if rewards else 0.0
    success_str = "true" if score > 0.0 else "false"
    rewards_str = ",".join(f"{r:.2f}" for r in rewards) if rewards else "0.00"

    print(
        f"[END] success={success_str} steps={len(rewards)} "
        f"score={score:.2f} rewards={rewards_str}",
        flush=True,
    )

    return score, rewards, len(rewards)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    all_scores: list[float] = []
    for task in TASKS:
        score, _, _ = run_task(task)
        all_scores.append(score)

    avg = sum(all_scores) / len(all_scores)
    print(
        f"\nSUMMARY  tasks={len(TASKS)}  "
        f"scores={','.join(f'{s:.2f}' for s in all_scores)}  "
        f"avg={avg:.2f}",
        flush=True,
    )


if __name__ == "__main__":
    main()
