from __future__ import annotations

from typing import List, Optional
from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Raw data types (internal, never sent to agent as ground truth)
# ---------------------------------------------------------------------------

class TravelSegment(BaseModel):
    """A single leg of a travel itinerary."""
    segment_id: str
    segment_type: str  # "flight" | "hotel" | "car_rental" | "train"
    from_location: str
    to_location: str
    departure: str  # ISO 8601 with UTC offset, e.g. "2026-06-15T08:00:00-04:00"
    arrival: str    # ISO 8601 with UTC offset
    cost: float
    booking_ref: str
    carrier: str
    notes: str = ""


class Issue(BaseModel):
    """A constraint violation found in an itinerary."""
    segment_ids: List[str]
    issue_type: str  # overlapping_segments | impossible_connection | missing_hotel |
                     # timezone_error | budget_overrun | missing_return |
                     # duplicate_booking | visa_violation | policy_violation
    severity: str    # "critical" | "warning" | "info"
    description: str


class GroundTruth(BaseModel):
    """Internal ground truth labels, never exposed to the agent."""
    issues: List[Issue]
    overall_status: str  # "valid" | "needs_revision" | "reject"
    correct_total_cost: float


class ItineraryData(BaseModel):
    """Full itinerary including hidden ground truth."""
    itinerary_id: str
    traveler_name: str
    trip_purpose: str
    segments: List[TravelSegment]
    budget_limit: float
    traveler_nationality: str  # "US" | "Indian" | "UK" | "German" | "Chinese" | "Australian"
    unstructured_context: str = ""  # traveler emails, notes, policy exceptions
    ground_truth: GroundTruth


# ---------------------------------------------------------------------------
# OpenEnv interface types
# ---------------------------------------------------------------------------

class ItineraryObservation(BaseModel):
    """What the agent sees at each step."""
    # OpenEnv required fields
    done: bool = False
    reward: float = 0.0
    metadata: dict = Field(default_factory=dict)

    # Itinerary content
    itinerary_id: str = ""
    traveler_name: str = ""
    trip_purpose: str = ""
    segments: List[TravelSegment] = Field(default_factory=list)
    budget_limit: float = 0.0
    traveler_nationality: str = ""

    # Constant rule text shown every step
    validation_rules: str = ""
    visa_requirements: str = ""

    # Unstructured context and clarifications
    unstructured_context: str = ""
    clarification: str = ""
    queries_used: int = 0
    max_queries: int = 2

    # Episode progress
    itineraries_checked: int = 0
    total_itineraries: int = 0


class ValidatorAction(BaseModel):
    """What the agent submits for each itinerary."""
    # OpenEnv required fields
    metadata: dict = Field(default_factory=dict)

    # Action type: "validate" (grade the itinerary) or "query" (ask a clarification)
    action_type: str = "validate"
    query_text: str = ""

    # Agent decision
    itinerary_id: str
    issues_found: List[Issue] = Field(default_factory=list)
    overall_status: str = "valid"  # "valid" | "needs_revision" | "reject"
    estimated_total_cost: float = 0.0


class ValidatorState(BaseModel):
    """Internal episode state."""
    # OpenEnv required fields
    episode_id: str = ""
    step_count: int = 0

    # Environment-specific
    task_name: str = ""
    total_reward: float = 0.0
    itineraries_remaining: int = 0
