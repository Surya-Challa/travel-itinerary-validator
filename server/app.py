"""
FastAPI application for the Travel Itinerary Validator environment.

Endpoints:
  POST /reset   — start a new episode
  POST /step    — submit an action, receive next observation + reward
  GET  /state   — get current episode state
  GET  /health  — liveness probe
  GET  /tasks   — list available tasks
"""

from __future__ import annotations

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi import FastAPI, HTTPException, Body
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional

from models import ItineraryObservation, ValidatorAction, ValidatorState
from server.travel_validator_environment import TravelValidatorEnvironment
from data.tasks import TASKS

# ---------------------------------------------------------------------------
# App setup
# ---------------------------------------------------------------------------

app = FastAPI(
    title="Travel Itinerary Validator",
    description=(
        "OpenEnv environment: AI agent reviews travel itineraries and identifies "
        "constraint violations (overlapping flights, impossible connections, visa "
        "issues, budget overruns, missing hotels, duplicate bookings)."
    ),
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# One shared environment instance (stateful per session)
_env = TravelValidatorEnvironment()


# ---------------------------------------------------------------------------
# Request / response models
# ---------------------------------------------------------------------------

class ResetRequest(BaseModel):
    task_name: Optional[str] = "basic_validation"
    seed: Optional[int] = None
    episode_id: Optional[str] = None


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@app.get("/health")
def health():
    return {"status": "ok", "env": "travel_itinerary_validator", "version": "0.1.0"}


@app.get("/")
def root(logs: Optional[str] = None):
    """Root endpoint — handles HuggingFace Spaces log requests."""
    if logs:
        # HuggingFace probes for /?logs=build and /?logs=container
        return {"message": f"Log request for {logs}", "status": "ok"}
    return {"message": "Travel Itinerary Validator", "status": "ok"}


@app.get("/tasks")
def list_tasks():
    return {
        "tasks": [
            {
                "name": "basic_validation",
                "difficulty": "easy",
                "itineraries": 4,
                "description": "Clear violations — overlapping flights, clean trips, missing hotel, budget overrun",
            },
            {
                "name": "connection_logic",
                "difficulty": "medium",
                "itineraries": 4,
                "description": "Timezone traps, impossible connections, tight-but-valid layovers, duplicate bookings",
            },
            {
                "name": "complex_trips",
                "difficulty": "hard",
                "itineraries": 4,
                "description": "Multi-issue itineraries, visa violations, compound errors, relocation traps",
            },
        ]
    }


@app.post("/reset", response_model=ItineraryObservation)
def reset(request: ResetRequest = Body(default=ResetRequest())):
    task_name = request.task_name or "basic_validation"
    if task_name not in TASKS:
        raise HTTPException(
            status_code=400,
            detail=f"Unknown task '{task_name}'. Valid tasks: {list(TASKS.keys())}",
        )
    obs = _env.reset(
        seed=request.seed,
        episode_id=request.episode_id,
        task_name=task_name,
    )
    return obs


@app.post("/step", response_model=ItineraryObservation)
def step(action: ValidatorAction):
    obs = _env.step(action)
    return obs


@app.get("/state", response_model=ValidatorState)
def get_state():
    return _env.state


# ---------------------------------------------------------------------------
# Entry point for local dev and Docker CMD
# ---------------------------------------------------------------------------

def main():
    import uvicorn
    port = int(os.environ.get("PORT", 7860))
    uvicorn.run("server.app:app", host="0.0.0.0", port=port, reload=False)


if __name__ == "__main__":
    main()
