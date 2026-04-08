import requests
import json
import time

base = "http://localhost:8000"

# 1. Health check
r = requests.get(f"{base}/health")
print("Health:", r.json())

# 2. List tasks
r = requests.get(f"{base}/tasks")
tasks = r.json()["tasks"]
print(f"Tasks: {len(tasks)} tasks")
for t in tasks:
    print(f"  {t['name']} ({t['difficulty']}) - {t['itineraries']} itineraries")

# 3. Test edge_cases task reset + query mechanism
r = requests.post(f"{base}/reset", json={"task_name": "edge_cases"})
obs = r.json()
print(f"\nEdge cases reset -> {obs['itinerary_id']} (queries: {obs['queries_used']}/{obs['max_queries']})")

r = requests.post(f"{base}/step", json={
    "action_type": "query",
    "query_text": "What are the hotel rules?",
    "itinerary_id": obs["itinerary_id"]
})
qobs = r.json()
print(f"Query response: {qobs['clarification'][:80]}...")
print(f"Queries used: {qobs['queries_used']}")

r = requests.post(f"{base}/step", json={
    "action_type": "validate",
    "itinerary_id": "ITIN-Y001",
    "issues_found": [],
    "overall_status": "valid",
    "estimated_total_cost": 580.0,
    "metadata": {}
})
obs2 = r.json()
print(f"Reward after 1 query: {obs2['reward']} (expected 0.95)")

# 4. Full perfect run of basic_validation (6 itineraries)
print("\n--- Full basic_validation episode ---")
r = requests.post(f"{base}/reset", json={"task_name": "basic_validation"})
obs = r.json()

perfect_actions = [
    {"id": "ITIN-A001", "issues": [{"segment_ids": ["SEG-A01", "SEG-A02"], "issue_type": "overlapping_segments", "severity": "critical", "description": "overlap"}], "status": "reject", "cost": 1330.0},
    {"id": "ITIN-B001", "issues": [], "status": "valid", "cost": 1140.0},
    {"id": "ITIN-C001", "issues": [{"segment_ids": ["SEG-C02", "SEG-C03"], "issue_type": "missing_hotel", "severity": "warning", "description": "missing hotel"}], "status": "needs_revision", "cost": 1270.0},
    {"id": "ITIN-D001", "issues": [{"segment_ids": ["SEG-D01", "SEG-D02", "SEG-D03", "SEG-D04"], "issue_type": "budget_overrun", "severity": "warning", "description": "over budget"}], "status": "needs_revision", "cost": 1690.0},
    {"id": "ITIN-M001", "issues": [{"segment_ids": ["SEG-M01", "SEG-M02", "SEG-M03"], "issue_type": "budget_overrun", "severity": "warning", "description": "over"}, {"segment_ids": ["SEG-M01"], "issue_type": "missing_return", "severity": "warning", "description": "no return"}], "status": "needs_revision", "cost": 1080.0},
    {"id": "ITIN-N001", "issues": [{"segment_ids": ["SEG-N01"], "issue_type": "policy_violation", "severity": "info", "description": "business class"}], "status": "valid", "cost": 1120.0},
]

for pa in perfect_actions:
    r = requests.post(f"{base}/step", json={
        "action_type": "validate",
        "itinerary_id": pa["id"],
        "issues_found": pa["issues"],
        "overall_status": pa["status"],
        "estimated_total_cost": pa["cost"],
        "metadata": {}
    })
    obs = r.json()
    print(f"  {pa['id']}: reward={obs['reward']:.2f} done={obs['done']}")

# 5. Test unstructured context in multi_city
print("\n--- Multi-city unstructured context ---")
r = requests.post(f"{base}/reset", json={"task_name": "multi_city"})
obs3 = r.json()
ctx = obs3.get("unstructured_context", "")
print(f"{obs3['itinerary_id']}: has_context={bool(ctx)}")
if ctx:
    print(f"  Preview: {ctx[:60]}...")

print("\nAll tests passed!")
