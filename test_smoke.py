"""Quick smoke-test: full episode with perfect actions."""
import requests

base = "http://localhost:8000"
requests.post(f"{base}/reset", json={"task_name": "basic_validation"})

perfect_actions = [
    {
        "itinerary_id": "ITIN-A001",
        "issues_found": [{"segment_ids": ["SEG-A01", "SEG-A02"], "issue_type": "overlapping_segments", "severity": "critical", "description": "overlap"}],
        "overall_status": "reject",
        "estimated_total_cost": 1330.0,
        "metadata": {},
    },
    {
        "itinerary_id": "ITIN-B001",
        "issues_found": [],
        "overall_status": "valid",
        "estimated_total_cost": 1140.0,
        "metadata": {},
    },
    {
        "itinerary_id": "ITIN-C001",
        "issues_found": [{"segment_ids": ["SEG-C02", "SEG-C03"], "issue_type": "missing_hotel", "severity": "warning", "description": "missing night"}],
        "overall_status": "needs_revision",
        "estimated_total_cost": 1270.0,
        "metadata": {},
    },
    {
        "itinerary_id": "ITIN-D001",
        "issues_found": [{"segment_ids": ["SEG-D01", "SEG-D02", "SEG-D03", "SEG-D04"], "issue_type": "budget_overrun", "severity": "warning", "description": "over budget"}],
        "overall_status": "needs_revision",
        "estimated_total_cost": 1690.0,
        "metadata": {},
    },
]

for i, action in enumerate(perfect_actions):
    r = requests.post(f"{base}/step", json=action)
    obs = r.json()
    iid = action["itinerary_id"]
    print(f"  Step {i+1}: {iid} -> reward={obs['reward']} done={obs['done']}")
    if obs["done"]:
        print(f"  Episode score: {obs['reward']}")
        print(f"  Step rewards:  {obs['metadata'].get('step_rewards')}")
