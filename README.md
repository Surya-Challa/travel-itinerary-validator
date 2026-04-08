---
title: Travel Itinerary Validator
colorFrom: blue
colorTo: green
sdk: docker
app_file: server/app.py
pinned: false
---
# Travel Itinerary Validator

An [OpenEnv](https://huggingface.co/openenv) benchmark environment where an AI agent reviews corporate travel itineraries and identifies constraint violations — overlapping flights, impossible connections, visa requirements, budget overruns, missing hotel nights, and duplicate bookings.

## Motivation

Every company that sends employees on business travel reviews itineraries before approval. A skilled agent must reason about **timezones**, **visa policy**, **connection times**, **budget limits**, and **corporate policy** simultaneously — making this a rich multi-constraint reasoning benchmark.

What makes this environment challenging:
- **False-positive traps**: ~40% of itineraries are valid but designed to look suspicious
- **Multi-signal grading**: 4-component reward function provides fine-grained feedback
- **Query mechanism**: Agents can ask for clarifications at a reward cost
- **3 nationalities × 9 rules**: Meaningful combinatorial space of potential violations

## Environment Statistics

| Metric | Value |
|---|---|
| Total itineraries | 12 |
| Tasks | 3 (easy → hard) |
| Itineraries per task | 4 |
| Nationalities | 3 (US, Indian, UK) |
| Validation rules | 9 |
| Issue types | 9 |
| False-positive traps | 5 of 12 (~40%) |
| Max queries per itinerary | 2 (at 0.05 reward cost each) |

## Action Space

The agent can submit two types of actions:

### 1. Validate Action (default)

| Field | Type | Description |
|---|---|---|
| `action_type` | `str` | `"validate"` |
| `itinerary_id` | `str` | ID of the itinerary being reviewed |
| `issues_found` | `List[Issue]` | List of constraint violations found |
| `overall_status` | `str` | `valid` / `needs_revision` / `reject` |
| `estimated_total_cost` | `float` | Sum of all segment costs |

### 2. Query Action (clarification request)

| Field | Type | Description |
|---|---|---|
| `action_type` | `str` | `"query"` |
| `query_text` | `str` | Free-text question about rules/policy |
| `itinerary_id` | `str` | Current itinerary ID |

Each query costs **0.05 reward** and returns a clarification response. Max 2 queries per itinerary.

**Query topics**: `visa`, `connection`, `hotel`, `budget`

### Issue Schema

Each `Issue` contains: `segment_ids`, `issue_type`, `severity`, `description`.

**Issue types:** `overlapping_segments`, `impossible_connection`, `missing_hotel`, `timezone_error`, `budget_overrun`, `missing_return`, `duplicate_booking`, `visa_violation`, `policy_violation`

**Severities:** `critical` (blocks travel), `warning` (must fix), `info` (note only)

## Observation Space

The agent receives an `ItineraryObservation` at each step:

| Field | Description |
|---|---|
| `itinerary_id` | Unique ID |
| `traveler_name` | Employee name |
| `trip_purpose` | Purpose of travel |
| `segments` | List of flights, hotels, car rentals, trains |
| `budget_limit` | Maximum allowed spend |
| `traveler_nationality` | For visa checks |
| `validation_rules` | Full text of all 9 validation rules |
| `visa_requirements` | Visa rules for 3 nationalities |
| `clarification` | Response to previous query (if any) |
| `queries_used` / `max_queries` | Query budget tracking |
| `itineraries_checked` / `total_itineraries` | Episode progress |

## Tasks

| Task | Difficulty | Itineraries | Valid Traps | Description |
|---|---|---|---|---|
| `basic_validation` | Easy | 4 | 1 | Single violations: overlapping flights, missing hotel, budget overrun. One valid trap. |
| `connection_logic` | Medium | 4 | 1 | Timezone crossing, impossible connections, tight-but-valid layovers, duplicates. |
| `complex_trips` | Hard | 4 | 1 | Multi-issue itineraries, visa violations for Indian/UK travelers, compound errors, relocation trap. |

### Design Principles

1. **~40% false-positive rate**: Forces agents to reason carefully, not just flag everything
2. **Progressive difficulty**: Easy tasks have single clear issues; hard tasks have multi-issue compound errors
3. **Deterministic grading**: Every scenario has an unambiguous ground truth answer
4. **Timezone reasoning**: Flights cross timezone boundaries, requiring UTC conversion

## Reward Function

Per itinerary (0.0–1.0), minus query costs:

| Component | Weight | Description |
|---|---|---|
| Issue detection F1 | 50% | Precision + recall on issue type and segment IDs |
| Severity accuracy | 15% | Correct `critical`/`warning`/`info` on matched issues |
| Overall status | 20% | Exact match on `valid`/`needs_revision`/`reject` |
| Cost accuracy | 15% | Proportional to closeness of `estimated_total_cost` |
| Query penalty | −0.05/query | Each clarification query deducts from the reward |

**Episode score** = average reward across all itineraries in the task.

### Grading Details

- **F1-score**: Issues matched by (issue_type + shared segment_ids). Perfect recall = finding all issues. Perfect precision = no false flags.
- **Severity**: Only scored on matched issues. Getting the issue type right but severity wrong still earns partial F1 credit.
- **Status**: `valid` for clean itineraries or info-only issues. `needs_revision` for warning-level. `reject` for critical.
- **Cost**: `max(0, 1 − |predicted − actual| / actual)`. Off by 10% = 90% credit.

## Setup

```bash
# Install dependencies
pip install -r requirements.txt

# Start the environment server
uvicorn server.app:app --host 0.0.0.0 --port 8000
```

## Docker

```bash
docker build -t travel-itinerary-validator .
docker run -p 8000:8000 travel-itinerary-validator
```

## Usage

```bash
# List available tasks
curl http://localhost:8000/tasks

# Start episode on easy task
curl -X POST http://localhost:8000/reset \
  -H "Content-Type: application/json" \
  -d '{"task_name": "basic_validation"}'

# Ask a clarification (costs 0.05 reward)
curl -X POST http://localhost:8000/step \
  -H "Content-Type: application/json" \
  -d '{
    "action_type": "query",
    "query_text": "What are the visa requirements for Indian citizens?",
    "itinerary_id": "ITIN-A001"
  }'

# Submit validation
curl -X POST http://localhost:8000/step \
  -H "Content-Type: application/json" \
  -d '{
    "action_type": "validate",
    "itinerary_id": "ITIN-A001",
    "issues_found": [
      {
        "segment_ids": ["SEG-A01", "SEG-A02"],
        "issue_type": "overlapping_segments",
        "severity": "critical",
        "description": "SEG-A01 arrives after SEG-A02 departs"
      }
    ],
    "overall_status": "reject",
    "estimated_total_cost": 1330.0,
    "metadata": {}
  }'
```

## Running Inference

```bash
export HF_TOKEN=your_token
export API_BASE_URL=https://router.huggingface.co/v1
export MODEL_NAME=Qwen/Qwen2.5-72B-Instruct
export ENV_BASE_URL=http://localhost:8000

python inference.py
```

## Baseline Scores

| Task | Score |
|---|---|
| `basic_validation` | TBD |
| `connection_logic` | TBD |
| `complex_trips` | TBD |

*(Run `python inference.py` to reproduce baseline scores)*

## Why This Environment Is Challenging

1. **Not just pattern matching**: Agents must perform multi-step reasoning (timezone math, visa lookups, budget summation) simultaneously
2. **Calibrated difficulty**: False-positive traps penalize over-flagging; subtle boundary cases test precision
3. **Exploration cost**: Query mechanism forces agents to decide when clarification is worth the reward penalty
4. **Real-world fidelity**: Every scenario is based on actual corporate travel validation patterns


