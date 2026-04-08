"""
TravelValidatorEnvironment — core environment logic.

Implements reset() / step() / state for the Travel Itinerary Validator.

Reward breakdown per itinerary (total 0.0–1.0):
  - Issue detection F1   50%  (precision + recall on issue_type + segment overlap)
  - Severity accuracy    15%  (correct severity on matched issues)
  - Overall status       20%  (exact match: valid / needs_revision / reject)
  - Cost accuracy        15%  (proportional to how close estimated_total_cost is)
"""

from __future__ import annotations

import sys
import os
from typing import List
from uuid import uuid4

# Allow imports from project root when running directly
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models import (
    ItineraryObservation,
    ValidatorAction,
    ValidatorState,
    ItineraryData,
    Issue,
    GroundTruth,
)
from data.tasks import TASKS, VALIDATION_RULES, VISA_REQUIREMENTS, CLARIFICATIONS


# ---------------------------------------------------------------------------
# Query cost: each clarification query deducts from the itinerary reward
# ---------------------------------------------------------------------------
QUERY_COST = 0.05
MAX_QUERIES_PER_ITINERARY = 2


class TravelValidatorEnvironment:
    """
    OpenEnv-compatible environment for travel itinerary validation.

    Each episode = one task (basic_validation / connection_logic / complex_trips).
    Each step    = one itinerary for the agent to review and report issues on.
    Episode ends when all itineraries in the task have been processed.
    """

    def __init__(self) -> None:
        self._state = ValidatorState()
        self._task_data: List[ItineraryData] = []
        self._current_index: int = 0
        self._rewards: List[float] = []
        self._queries_this_itinerary: int = 0
        self._total_query_cost: float = 0.0

    # ------------------------------------------------------------------
    # OpenEnv interface
    # ------------------------------------------------------------------

    def reset(self, seed: int | None = None, episode_id: str | None = None,
              **kwargs) -> ItineraryObservation:
        task_name: str = kwargs.get("task_name", "basic_validation")

        if task_name not in TASKS:
            task_name = "basic_validation"

        self._task_data = TASKS[task_name]
        self._current_index = 0
        self._rewards = []
        self._queries_this_itinerary = 0
        self._total_query_cost = 0.0
        self._state = ValidatorState(
            episode_id=episode_id or str(uuid4()),
            step_count=0,
            task_name=task_name,
            total_reward=0.0,
            itineraries_remaining=len(self._task_data),
        )

        return self._make_observation(index=0, done=False, reward=0.0)

    def step(self, action: ValidatorAction,
             **kwargs) -> ItineraryObservation:
        if not self._task_data:
            # Called without reset — return done immediately
            return ItineraryObservation(done=True, reward=0.0)

        # --- Handle query actions ---
        if action.action_type == "query":
            return self._handle_query(action)

        # Grade the action against current itinerary ground truth
        current = self._task_data[self._current_index]
        reward = self._grade(action, current.ground_truth)

        # Apply query cost for this itinerary
        query_penalty = self._queries_this_itinerary * QUERY_COST
        reward = max(0.0, reward - query_penalty)

        self._rewards.append(reward)

        # Advance state
        self._current_index += 1
        self._queries_this_itinerary = 0  # Reset for next itinerary
        self._state.step_count += 1
        self._state.total_reward += reward
        self._state.itineraries_remaining = max(
            0, len(self._task_data) - self._current_index
        )

        done = self._current_index >= len(self._task_data)

        if done:
            # Episode over — return final observation with average episode score
            episode_score = sum(self._rewards) / len(self._rewards)
            obs = ItineraryObservation(
                done=True,
                reward=episode_score,
                metadata={"episode_score": episode_score, "step_rewards": self._rewards},
                itineraries_checked=len(self._rewards),
                total_itineraries=len(self._task_data),
                validation_rules=VALIDATION_RULES,
                visa_requirements=VISA_REQUIREMENTS,
            )
        else:
            obs = self._make_observation(
                index=self._current_index,
                done=False,
                reward=reward,
            )

        return obs

    @property
    def state(self) -> ValidatorState:
        return self._state

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _handle_query(self, action: ValidatorAction) -> ItineraryObservation:
        """Handle a clarification query without advancing the itinerary."""
        if self._queries_this_itinerary >= MAX_QUERIES_PER_ITINERARY:
            clarification = (
                "Query limit reached for this itinerary. "
                "Please submit your validation action."
            )
        else:
            self._queries_this_itinerary += 1
            self._state.step_count += 1
            clarification = self._match_clarification(action.query_text)

        return self._make_observation(
            index=self._current_index,
            done=False,
            reward=0.0,
            clarification=clarification,
        )

    @staticmethod
    def _match_clarification(query_text: str) -> str:
        """Match a free-text query to the best clarification response."""
        query_lower = query_text.lower()
        for keyword, response in CLARIFICATIONS.items():
            if keyword in query_lower:
                return response
        return (
            "No specific clarification available for that question. "
            "Review the validation rules and visa requirements provided "
            "with the itinerary."
        )

    def _make_observation(self, index: int, done: bool,
                          reward: float,
                          clarification: str = "") -> ItineraryObservation:
        itin = self._task_data[index]
        return ItineraryObservation(
            done=done,
            reward=reward,
            metadata={},
            itinerary_id=itin.itinerary_id,
            traveler_name=itin.traveler_name,
            trip_purpose=itin.trip_purpose,
            segments=itin.segments,
            budget_limit=itin.budget_limit,
            traveler_nationality=itin.traveler_nationality,
            validation_rules=VALIDATION_RULES,
            visa_requirements=VISA_REQUIREMENTS,
            unstructured_context=itin.unstructured_context,
            clarification=clarification,
            queries_used=self._queries_this_itinerary,
            max_queries=MAX_QUERIES_PER_ITINERARY,
            itineraries_checked=self._current_index,
            total_itineraries=len(self._task_data),
        )

    def _grade(self, action: ValidatorAction,
               truth: GroundTruth) -> float:
        """
        Score an agent's action against ground truth for one itinerary.

        Returns a float in [0.0, 1.0].
        """
        score = 0.0

        # --- 1. Issue detection: F1 on (issue_type, overlapping segment_ids) ---
        # Weight: 50%
        predicted = action.issues_found or []
        expected = truth.issues

        true_positives: List[tuple[Issue, Issue]] = []  # (predicted, expected)

        matched_expected = set()
        matched_predicted = set()

        for i, pred in enumerate(predicted):
            for j, exp in enumerate(expected):
                if j in matched_expected:
                    continue
                if pred.issue_type == exp.issue_type and _segments_overlap(
                    pred.segment_ids, exp.segment_ids
                ):
                    true_positives.append((pred, exp))
                    matched_expected.add(j)
                    matched_predicted.add(i)
                    break

        tp = len(true_positives)
        fp = len(predicted) - tp
        fn = len(expected) - tp

        if tp == 0 and len(expected) == 0 and len(predicted) == 0:
            # Perfect: no issues expected, none predicted
            issue_f1 = 1.0
        elif tp == 0:
            issue_f1 = 0.0
        else:
            precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
            recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
            issue_f1 = (
                2 * precision * recall / (precision + recall)
                if (precision + recall) > 0
                else 0.0
            )

        score += issue_f1 * 0.50

        # --- 2. Severity accuracy on matched issues ---
        # Weight: 15%
        if true_positives:
            correct_severities = sum(
                1 for pred, exp in true_positives
                if pred.severity == exp.severity
            )
            severity_score = correct_severities / len(true_positives)
        else:
            # No matches — only give credit if there were also no expected issues
            severity_score = 1.0 if len(expected) == 0 else 0.0

        score += severity_score * 0.15

        # --- 3. Overall status ---
        # Weight: 20%
        if action.overall_status == truth.overall_status:
            score += 0.20

        # --- 4. Cost accuracy ---
        # Weight: 15%
        correct_cost = truth.correct_total_cost
        if correct_cost > 0:
            error_ratio = abs(action.estimated_total_cost - correct_cost) / correct_cost
            cost_score = max(0.0, 1.0 - error_ratio)
        else:
            cost_score = 1.0 if action.estimated_total_cost == 0 else 0.0

        score += cost_score * 0.15

        return round(min(1.0, max(0.0, score)), 4)


def _segments_overlap(predicted_ids: List[str],
                      expected_ids: List[str]) -> bool:
    """True if the two segment ID lists share at least one ID."""
    return bool(set(predicted_ids) & set(expected_ids))
