"""
Extended task data — 18 additional itineraries across existing + 2 new tasks.

Adds:
  - 2 extra itineraries per existing task (6 total)
  - TASK_MULTI_CITY: 6 itineraries (medium-hard)
  - TASK_EDGE_CASES: 6 itineraries (expert)
  - CLARIFICATIONS: pre-defined responses for the query mechanism
"""

from __future__ import annotations
from models import TravelSegment, Issue, GroundTruth, ItineraryData


# ---------------------------------------------------------------------------
# Extra itineraries for TASK_BASIC_VALIDATION
# ---------------------------------------------------------------------------

EXTRA_BASIC_VALIDATION: list[ItineraryData] = [

    # ITIN-M001: Two issues — budget overrun + missing return
    ItineraryData(
        itinerary_id="ITIN-M001",
        traveler_name="Maria Rodriguez",
        trip_purpose="Product demo in Dallas",
        budget_limit=800.0,
        traveler_nationality="US",
        unstructured_context=(
            "From: maria.rodriguez@company.com\n"
            "Subject: Dallas trip extension\n\n"
            "Hi Travel Team,\n"
            "Can I extend my stay through the weekend? I'll book the return "
            "flight myself when I know my schedule. Thanks!\n"
        ),
        segments=[
            TravelSegment(
                segment_id="SEG-M01",
                segment_type="flight",
                from_location="ATL (Atlanta)",
                to_location="DFW (Dallas)",
                departure="2026-07-20T08:00:00-04:00",
                arrival="2026-07-20T09:30:00-05:00",
                cost=350.0,
                booking_ref="BK-M0001",
                carrier="Delta",
            ),
            TravelSegment(
                segment_id="SEG-M02",
                segment_type="hotel",
                from_location="Dallas",
                to_location="Dallas",
                departure="2026-07-20T15:00:00-05:00",
                arrival="2026-07-22T11:00:00-05:00",
                cost=420.0,
                booking_ref="BK-M0002",
                carrier="Dallas Marriott City Center",
            ),
            TravelSegment(
                segment_id="SEG-M03",
                segment_type="car_rental",
                from_location="Dallas",
                to_location="Dallas",
                departure="2026-07-20T10:00:00-05:00",
                arrival="2026-07-22T10:00:00-05:00",
                cost=310.0,
                booking_ref="BK-M0003",
                carrier="Hertz DFW Airport",
            ),
        ],
        ground_truth=GroundTruth(
            issues=[
                Issue(
                    segment_ids=["SEG-M01", "SEG-M02", "SEG-M03"],
                    issue_type="budget_overrun",
                    severity="warning",
                    description=(
                        "Total cost is $1,080 which exceeds the $800 budget limit by $280."
                    ),
                ),
                Issue(
                    segment_ids=["SEG-M01"],
                    issue_type="missing_return",
                    severity="warning",
                    description=(
                        "No return flight from Dallas to Atlanta. "
                        "Trip purpose does not indicate one-way or relocation."
                    ),
                ),
            ],
            overall_status="needs_revision",
            correct_total_cost=1080.0,
        ),
    ),

    # ITIN-N001: Valid with policy violation note — FALSE POSITIVE TRAP
    ItineraryData(
        itinerary_id="ITIN-N001",
        traveler_name="Nathan Park",
        trip_purpose="Quarterly review in Phoenix",
        budget_limit=1500.0,
        traveler_nationality="US",
        unstructured_context=(
            "From: nathan.park@company.com\n"
            "Subject: Re: Phoenix travel approval\n\n"
            "Hi, my manager approved the business class upgrade for the "
            "Phoenix trip given the early morning departure. Approval "
            "reference: MGR-2026-0412.\n"
        ),
        segments=[
            TravelSegment(
                segment_id="SEG-N01",
                segment_type="flight",
                from_location="LAX (Los Angeles)",
                to_location="PHX (Phoenix)",
                departure="2026-08-05T07:00:00-07:00",
                arrival="2026-08-05T09:30:00-07:00",
                cost=450.0,
                booking_ref="BK-N0001",
                carrier="American Airlines",
                notes="Business class — manager-approved upgrade",
            ),
            TravelSegment(
                segment_id="SEG-N02",
                segment_type="hotel",
                from_location="Phoenix",
                to_location="Phoenix",
                departure="2026-08-05T14:00:00-07:00",
                arrival="2026-08-07T11:00:00-07:00",
                cost=380.0,
                booking_ref="BK-N0002",
                carrier="Phoenix Sheraton Grand",
            ),
            TravelSegment(
                segment_id="SEG-N03",
                segment_type="flight",
                from_location="PHX (Phoenix)",
                to_location="LAX (Los Angeles)",
                departure="2026-08-07T16:00:00-07:00",
                arrival="2026-08-07T17:30:00-07:00",
                cost=290.0,
                booking_ref="BK-N0003",
                carrier="Southwest Airlines",
            ),
        ],
        ground_truth=GroundTruth(
            issues=[
                Issue(
                    segment_ids=["SEG-N01"],
                    issue_type="policy_violation",
                    severity="info",
                    description=(
                        "Business class on a standard quarterly review trip. "
                        "Policy requires economy unless pre-approved."
                    ),
                ),
            ],
            overall_status="valid",
            correct_total_cost=1120.0,
        ),
    ),
]


# ---------------------------------------------------------------------------
# Extra itineraries for TASK_CONNECTION_LOGIC
# ---------------------------------------------------------------------------

EXTRA_CONNECTION_LOGIC: list[ItineraryData] = [

    # ITIN-O001: Impossible domestic connection — 25 min at O'Hare (needs 60 min)
    ItineraryData(
        itinerary_id="ITIN-O001",
        traveler_name="Olivia Kowalski",
        trip_purpose="Regional sales meeting in Denver",
        budget_limit=2000.0,
        traveler_nationality="US",
        segments=[
            TravelSegment(
                segment_id="SEG-O01",
                segment_type="flight",
                from_location="BOS (Boston)",
                to_location="ORD (Chicago)",
                departure="2026-08-14T08:00:00-04:00",
                arrival="2026-08-14T10:00:00-05:00",
                cost=310.0,
                booking_ref="BK-O0001",
                carrier="United Airlines",
            ),
            TravelSegment(
                segment_id="SEG-O02",
                segment_type="flight",
                from_location="ORD (Chicago)",
                to_location="DEN (Denver)",
                departure="2026-08-14T10:25:00-05:00",
                arrival="2026-08-14T11:45:00-06:00",
                cost=220.0,
                booking_ref="BK-O0002",
                carrier="United Airlines",
                notes="Only 25-minute connection at O'Hare — domestic minimum is 60 minutes",
            ),
            TravelSegment(
                segment_id="SEG-O03",
                segment_type="hotel",
                from_location="Denver",
                to_location="Denver",
                departure="2026-08-14T15:00:00-06:00",
                arrival="2026-08-16T11:00:00-06:00",
                cost=380.0,
                booking_ref="BK-O0003",
                carrier="Denver Grand Hyatt",
            ),
            TravelSegment(
                segment_id="SEG-O04",
                segment_type="flight",
                from_location="DEN (Denver)",
                to_location="BOS (Boston)",
                departure="2026-08-16T14:00:00-06:00",
                arrival="2026-08-16T20:00:00-04:00",
                cost=340.0,
                booking_ref="BK-O0004",
                carrier="JetBlue",
            ),
        ],
        ground_truth=GroundTruth(
            issues=[
                Issue(
                    segment_ids=["SEG-O01", "SEG-O02"],
                    issue_type="impossible_connection",
                    severity="critical",
                    description=(
                        "SEG-O01 arrives ORD at 10:00 CST. SEG-O02 departs ORD at 10:25 CST. "
                        "Only 25 minutes — domestic connection requires 60 minutes minimum."
                    ),
                )
            ],
            overall_status="reject",
            correct_total_cost=1250.0,
        ),
    ),

    # ITIN-P001: Impossible domestic connection — 25 min (needs 60)
    ItineraryData(
        itinerary_id="ITIN-P001",
        traveler_name="Peter Chang",
        trip_purpose="Multi-city vendor tour on West Coast",
        budget_limit=2500.0,
        traveler_nationality="US",
        unstructured_context=(
            "From: peter.chang@company.com\n"
            "Subject: Re: West Coast trip\n\n"
            "I know the SEA connection looks tight — I've made this run "
            "before with Pre-Check and it's always fine. Please don't flag it.\n"
        ),
        segments=[
            TravelSegment(
                segment_id="SEG-P01",
                segment_type="flight",
                from_location="SFO (San Francisco)",
                to_location="SEA (Seattle)",
                departure="2026-09-08T07:00:00-07:00",
                arrival="2026-09-08T09:15:00-07:00",
                cost=190.0,
                booking_ref="BK-P0001",
                carrier="Alaska Airlines",
            ),
            TravelSegment(
                segment_id="SEG-P02",
                segment_type="flight",
                from_location="SEA (Seattle)",
                to_location="PDX (Portland)",
                departure="2026-09-08T09:40:00-07:00",
                arrival="2026-09-08T10:40:00-07:00",
                cost=140.0,
                booking_ref="BK-P0002",
                carrier="Alaska Airlines",
                notes="Separate booking — only 25 min connection at SEA",
            ),
            TravelSegment(
                segment_id="SEG-P03",
                segment_type="hotel",
                from_location="Portland",
                to_location="Portland",
                departure="2026-09-08T14:00:00-07:00",
                arrival="2026-09-10T11:00:00-07:00",
                cost=340.0,
                booking_ref="BK-P0003",
                carrier="Portland Nines Hotel",
            ),
            TravelSegment(
                segment_id="SEG-P04",
                segment_type="flight",
                from_location="PDX (Portland)",
                to_location="SFO (San Francisco)",
                departure="2026-09-10T15:00:00-07:00",
                arrival="2026-09-10T17:00:00-07:00",
                cost=180.0,
                booking_ref="BK-P0004",
                carrier="United Airlines",
            ),
        ],
        ground_truth=GroundTruth(
            issues=[
                Issue(
                    segment_ids=["SEG-P01", "SEG-P02"],
                    issue_type="impossible_connection",
                    severity="critical",
                    description=(
                        "SEG-P01 arrives SEA at 09:15 PDT. SEG-P02 departs SEA at 09:40 PDT. "
                        "Only 25 minutes — domestic connection requires 60 minutes minimum."
                    ),
                )
            ],
            overall_status="reject",
            correct_total_cost=850.0,
        ),
    ),
]


# ---------------------------------------------------------------------------
# Extra itineraries for TASK_COMPLEX_TRIPS
# ---------------------------------------------------------------------------

EXTRA_COMPLEX_TRIPS: list[ItineraryData] = [

    # ITIN-Q001: UK citizen in China — visa + missing hotel + budget overrun
    ItineraryData(
        itinerary_id="ITIN-Q001",
        traveler_name="Quinn Williams",
        trip_purpose="Manufacturing audit in Beijing and Shanghai",
        budget_limit=3000.0,
        traveler_nationality="UK",
        segments=[
            TravelSegment(
                segment_id="SEG-Q01",
                segment_type="flight",
                from_location="LHR (London)",
                to_location="PEK (Beijing)",
                departure="2026-10-20T10:00:00+00:00",
                arrival="2026-10-21T05:00:00+08:00",
                cost=1200.0,
                booking_ref="BK-Q0001",
                carrier="Air China",
            ),
            TravelSegment(
                segment_id="SEG-Q02",
                segment_type="hotel",
                from_location="Beijing",
                to_location="Beijing",
                departure="2026-10-21T14:00:00+08:00",
                arrival="2026-10-23T11:00:00+08:00",
                cost=400.0,
                booking_ref="BK-Q0002",
                carrier="Beijing Grand Hyatt",
            ),
            TravelSegment(
                segment_id="SEG-Q03",
                segment_type="train",
                from_location="Beijing South Station",
                to_location="Shanghai Hongqiao Station",
                departure="2026-10-23T13:00:00+08:00",
                arrival="2026-10-23T18:30:00+08:00",
                cost=150.0,
                booking_ref="BK-Q0003",
                carrier="China Railway High-Speed",
            ),
            TravelSegment(
                segment_id="SEG-Q04",
                segment_type="hotel",
                from_location="Shanghai",
                to_location="Shanghai",
                departure="2026-10-23T20:00:00+08:00",
                arrival="2026-10-24T11:00:00+08:00",
                cost=180.0,
                booking_ref="BK-Q0004",
                carrier="Shanghai Marriott Pudong",
            ),
            TravelSegment(
                segment_id="SEG-Q05",
                segment_type="car_rental",
                from_location="Shanghai",
                to_location="Shanghai",
                departure="2026-10-23T19:00:00+08:00",
                arrival="2026-10-25T09:00:00+08:00",
                cost=200.0,
                booking_ref="BK-Q0005",
                carrier="Avis Shanghai",
            ),
            TravelSegment(
                segment_id="SEG-Q06",
                segment_type="flight",
                from_location="PVG (Shanghai)",
                to_location="LHR (London)",
                departure="2026-10-25T10:00:00+08:00",
                arrival="2026-10-25T14:30:00+00:00",
                cost=1300.0,
                booking_ref="BK-Q0006",
                carrier="British Airways",
            ),
        ],
        ground_truth=GroundTruth(
            issues=[
                Issue(
                    segment_ids=["SEG-Q01"],
                    issue_type="visa_violation",
                    severity="critical",
                    description=(
                        "UK citizens require a visa to enter China. "
                        "No China visa noted for traveler Quinn Williams."
                    ),
                ),
                Issue(
                    segment_ids=["SEG-Q04", "SEG-Q06"],
                    issue_type="missing_hotel",
                    severity="warning",
                    description=(
                        "Hotel SEG-Q04 checks out October 24 but return flight "
                        "SEG-Q06 departs October 25. Night of October 24 has no accommodation."
                    ),
                ),
                Issue(
                    segment_ids=["SEG-Q01", "SEG-Q02", "SEG-Q03", "SEG-Q04",
                                  "SEG-Q05", "SEG-Q06"],
                    issue_type="budget_overrun",
                    severity="warning",
                    description=(
                        "Total cost is $3,430 which exceeds the $3,000 budget limit by $430."
                    ),
                ),
            ],
            overall_status="reject",
            correct_total_cost=3430.0,
        ),
    ),

    # ITIN-R001: Indian one-way relocation via Dubai — visa trap
    ItineraryData(
        itinerary_id="ITIN-R001",
        traveler_name="Raj Mehta",
        trip_purpose="One-way relocation from Mumbai to San Francisco via Dubai",
        budget_limit=5000.0,
        traveler_nationality="Indian",
        unstructured_context=(
            "From: raj.mehta@company.com\n"
            "Subject: Relocation visa update\n\n"
            "Hi, my US work visa is already sorted. The Dubai stopover is "
            "just for a night to break the long journey. My visa situation "
            "is all taken care of — please don't worry about it.\n"
        ),
        segments=[
            TravelSegment(
                segment_id="SEG-R01",
                segment_type="flight",
                from_location="BOM (Mumbai)",
                to_location="DXB (Dubai)",
                departure="2026-11-01T23:00:00+05:30",
                arrival="2026-11-02T01:30:00+04:00",
                cost=400.0,
                booking_ref="BK-R0001",
                carrier="Emirates",
            ),
            TravelSegment(
                segment_id="SEG-R02",
                segment_type="hotel",
                from_location="Dubai",
                to_location="Dubai",
                departure="2026-11-02T03:00:00+04:00",
                arrival="2026-11-03T11:00:00+04:00",
                cost=250.0,
                booking_ref="BK-R0002",
                carrier="Dubai Airport Hotel",
            ),
            TravelSegment(
                segment_id="SEG-R03",
                segment_type="flight",
                from_location="DXB (Dubai)",
                to_location="SFO (San Francisco)",
                departure="2026-11-03T14:00:00+04:00",
                arrival="2026-11-03T18:00:00-08:00",
                cost=1800.0,
                booking_ref="BK-R0003",
                carrier="Emirates",
                notes="Direct flight DXB→SFO ~16 hours",
            ),
        ],
        ground_truth=GroundTruth(
            issues=[
                Issue(
                    segment_ids=["SEG-R01", "SEG-R02"],
                    issue_type="visa_violation",
                    severity="critical",
                    description=(
                        "Indian citizens require a visa to enter the UAE. "
                        "Overnight hotel stay in Dubai means traveler exits the "
                        "transit zone — a UAE visa is required."
                    ),
                ),
            ],
            overall_status="needs_revision",
            correct_total_cost=2450.0,
        ),
    ),
]


# ---------------------------------------------------------------------------
# TASK 4: multi_city (Medium-Hard)
# 6 itineraries: complex routing, transit visas, mixed purpose,
# timezone math, budget edge cases
# ---------------------------------------------------------------------------

TASK_MULTI_CITY: list[ItineraryData] = [

    # ITIN-S001: Valid 5-city US tour — HARD false-positive trap
    ItineraryData(
        itinerary_id="ITIN-S001",
        traveler_name="Sarah Mitchell",
        trip_purpose="Cross-country client visits: Boston, Chicago, Denver, LA",
        budget_limit=6000.0,
        traveler_nationality="US",
        unstructured_context=(
            "From: sarah.mitchell@company.com\n"
            "Subject: Multi-city itinerary confirmed\n\n"
            "All flights and hotels confirmed. Each overnight is covered. "
            "Let me know if you need anything else for approval.\n"
        ),
        segments=[
            TravelSegment(
                segment_id="SEG-S01",
                segment_type="flight",
                from_location="JFK (New York)",
                to_location="BOS (Boston)",
                departure="2026-06-01T07:00:00-04:00",
                arrival="2026-06-01T08:30:00-04:00",
                cost=180.0,
                booking_ref="BK-S0001",
                carrier="JetBlue",
            ),
            TravelSegment(
                segment_id="SEG-S02",
                segment_type="hotel",
                from_location="Boston",
                to_location="Boston",
                departure="2026-06-01T15:00:00-04:00",
                arrival="2026-06-02T11:00:00-04:00",
                cost=200.0,
                booking_ref="BK-S0002",
                carrier="Boston Omni Parker House",
            ),
            TravelSegment(
                segment_id="SEG-S03",
                segment_type="flight",
                from_location="BOS (Boston)",
                to_location="ORD (Chicago)",
                departure="2026-06-02T14:00:00-04:00",
                arrival="2026-06-02T16:00:00-05:00",
                cost=250.0,
                booking_ref="BK-S0003",
                carrier="American Airlines",
            ),
            TravelSegment(
                segment_id="SEG-S04",
                segment_type="hotel",
                from_location="Chicago",
                to_location="Chicago",
                departure="2026-06-02T17:00:00-05:00",
                arrival="2026-06-03T11:00:00-05:00",
                cost=220.0,
                booking_ref="BK-S0004",
                carrier="Chicago Palmer House",
            ),
            TravelSegment(
                segment_id="SEG-S05",
                segment_type="flight",
                from_location="ORD (Chicago)",
                to_location="DEN (Denver)",
                departure="2026-06-03T13:00:00-05:00",
                arrival="2026-06-03T14:15:00-06:00",
                cost=210.0,
                booking_ref="BK-S0005",
                carrier="United Airlines",
            ),
            TravelSegment(
                segment_id="SEG-S06",
                segment_type="hotel",
                from_location="Denver",
                to_location="Denver",
                departure="2026-06-03T16:00:00-06:00",
                arrival="2026-06-04T11:00:00-06:00",
                cost=190.0,
                booking_ref="BK-S0006",
                carrier="Denver Four Seasons",
            ),
            TravelSegment(
                segment_id="SEG-S07",
                segment_type="flight",
                from_location="DEN (Denver)",
                to_location="LAX (Los Angeles)",
                departure="2026-06-04T14:00:00-06:00",
                arrival="2026-06-04T15:00:00-07:00",
                cost=180.0,
                booking_ref="BK-S0007",
                carrier="Southwest Airlines",
            ),
            TravelSegment(
                segment_id="SEG-S08",
                segment_type="hotel",
                from_location="Los Angeles",
                to_location="Los Angeles",
                departure="2026-06-04T17:00:00-07:00",
                arrival="2026-06-05T11:00:00-07:00",
                cost=280.0,
                booking_ref="BK-S0008",
                carrier="LA Beverly Hilton",
            ),
            TravelSegment(
                segment_id="SEG-S09",
                segment_type="flight",
                from_location="LAX (Los Angeles)",
                to_location="JFK (New York)",
                departure="2026-06-05T14:00:00-07:00",
                arrival="2026-06-05T22:00:00-04:00",
                cost=350.0,
                booking_ref="BK-S0009",
                carrier="Delta",
            ),
        ],
        ground_truth=GroundTruth(
            issues=[],
            overall_status="valid",
            correct_total_cost=2060.0,
        ),
    ),

    # ITIN-T001: German backtrack with missing hotel in Frankfurt
    ItineraryData(
        itinerary_id="ITIN-T001",
        traveler_name="Thomas Weber",
        trip_purpose="Sales tour: Paris, Frankfurt, London",
        budget_limit=3500.0,
        traveler_nationality="German",
        unstructured_context=(
            "From: thomas.weber@company.de\n"
            "Subject: Frankfurt overnight\n\n"
            "I'll stay at my apartment in Frankfurt between the Paris and "
            "London legs — no hotel booking needed for that night.\n"
        ),
        segments=[
            TravelSegment(
                segment_id="SEG-T01",
                segment_type="flight",
                from_location="FRA (Frankfurt)",
                to_location="CDG (Paris)",
                departure="2026-07-10T07:00:00+02:00",
                arrival="2026-07-10T08:30:00+02:00",
                cost=180.0,
                booking_ref="BK-T0001",
                carrier="Air France",
            ),
            TravelSegment(
                segment_id="SEG-T02",
                segment_type="hotel",
                from_location="Paris",
                to_location="Paris",
                departure="2026-07-10T13:00:00+02:00",
                arrival="2026-07-11T11:00:00+02:00",
                cost=160.0,
                booking_ref="BK-T0002",
                carrier="Paris Novotel Gare du Nord",
            ),
            TravelSegment(
                segment_id="SEG-T03",
                segment_type="flight",
                from_location="CDG (Paris)",
                to_location="FRA (Frankfurt)",
                departure="2026-07-11T14:00:00+02:00",
                arrival="2026-07-11T15:00:00+02:00",
                cost=180.0,
                booking_ref="BK-T0003",
                carrier="Lufthansa",
            ),
            TravelSegment(
                segment_id="SEG-T04",
                segment_type="flight",
                from_location="FRA (Frankfurt)",
                to_location="LHR (London)",
                departure="2026-07-12T08:00:00+02:00",
                arrival="2026-07-12T08:30:00+01:00",
                cost=150.0,
                booking_ref="BK-T0004",
                carrier="British Airways",
            ),
            TravelSegment(
                segment_id="SEG-T05",
                segment_type="hotel",
                from_location="London",
                to_location="London",
                departure="2026-07-12T14:00:00+01:00",
                arrival="2026-07-14T11:00:00+01:00",
                cost=300.0,
                booking_ref="BK-T0005",
                carrier="London Travelodge City",
            ),
            TravelSegment(
                segment_id="SEG-T06",
                segment_type="flight",
                from_location="LHR (London)",
                to_location="FRA (Frankfurt)",
                departure="2026-07-14T16:00:00+01:00",
                arrival="2026-07-14T18:30:00+02:00",
                cost=140.0,
                booking_ref="BK-T0006",
                carrier="Lufthansa",
            ),
        ],
        ground_truth=GroundTruth(
            issues=[
                Issue(
                    segment_ids=["SEG-T03", "SEG-T04"],
                    issue_type="missing_hotel",
                    severity="warning",
                    description=(
                        "SEG-T03 arrives Frankfurt at 15:00 on July 11. "
                        "SEG-T04 departs Frankfurt at 08:00 on July 12. "
                        "17-hour overnight gap with no hotel booked in Frankfurt. "
                        "Informal accommodation (own apartment) does not count as "
                        "a booked travel segment."
                    ),
                ),
            ],
            overall_status="needs_revision",
            correct_total_cost=1110.0,
        ),
    ),

    # ITIN-U001: Indian transiting Singapore — valid (transit zone, no visa)
    ItineraryData(
        itinerary_id="ITIN-U001",
        traveler_name="Uma Raghavan",
        trip_purpose="Technical conference in Sydney",
        budget_limit=4500.0,
        traveler_nationality="Indian",
        unstructured_context=(
            "From: uma.raghavan@company.in\n"
            "Subject: Singapore transit\n\n"
            "I'll be transiting through Changi Airport — won't leave the "
            "international terminal. Both layovers are around 2.5 hours.\n"
        ),
        segments=[
            TravelSegment(
                segment_id="SEG-U01",
                segment_type="flight",
                from_location="DEL (New Delhi)",
                to_location="SIN (Singapore)",
                departure="2026-09-01T22:00:00+05:30",
                arrival="2026-09-02T06:00:00+08:00",
                cost=320.0,
                booking_ref="BK-U0001",
                carrier="Singapore Airlines",
            ),
            TravelSegment(
                segment_id="SEG-U02",
                segment_type="flight",
                from_location="SIN (Singapore)",
                to_location="SYD (Sydney)",
                departure="2026-09-02T08:30:00+08:00",
                arrival="2026-09-02T19:00:00+10:00",
                cost=550.0,
                booking_ref="BK-U0002",
                carrier="Singapore Airlines",
                notes="Same-ticket connection — remains in transit zone at Changi",
            ),
            TravelSegment(
                segment_id="SEG-U03",
                segment_type="hotel",
                from_location="Sydney",
                to_location="Sydney",
                departure="2026-09-02T22:00:00+10:00",
                arrival="2026-09-06T11:00:00+10:00",
                cost=720.0,
                booking_ref="BK-U0003",
                carrier="Sydney Harbour Marriott",
            ),
            TravelSegment(
                segment_id="SEG-U04",
                segment_type="flight",
                from_location="SYD (Sydney)",
                to_location="DEL (New Delhi)",
                departure="2026-09-06T21:00:00+10:00",
                arrival="2026-09-07T04:00:00+05:30",
                cost=680.0,
                booking_ref="BK-U0004",
                carrier="Air India",
                notes="Direct return — no Singapore transit on return leg",
            ),
        ],
        ground_truth=GroundTruth(
            issues=[],
            overall_status="valid",
            correct_total_cost=2270.0,
        ),
    ),

    # ITIN-V001: Mixed business/personal — policy violation (info only)
    ItineraryData(
        itinerary_id="ITIN-V001",
        traveler_name="Victoria Santos",
        trip_purpose="Client meeting in Barcelona + personal vacation extension",
        budget_limit=3500.0,
        traveler_nationality="US",
        unstructured_context=(
            "From: victoria.santos@company.com\n"
            "Subject: Barcelona personal days\n\n"
            "Manager has approved 3 extra personal days attached to the "
            "Barcelona client meeting. I'll cover my own meals during the "
            "personal portion. Hotel for personal days charged to my card.\n"
        ),
        segments=[
            TravelSegment(
                segment_id="SEG-V01",
                segment_type="flight",
                from_location="JFK (New York)",
                to_location="BCN (Barcelona)",
                departure="2026-08-20T18:00:00-04:00",
                arrival="2026-08-21T08:00:00+02:00",
                cost=650.0,
                booking_ref="BK-V0001",
                carrier="Iberia",
            ),
            TravelSegment(
                segment_id="SEG-V02",
                segment_type="hotel",
                from_location="Barcelona",
                to_location="Barcelona",
                departure="2026-08-21T14:00:00+02:00",
                arrival="2026-08-24T11:00:00+02:00",
                cost=450.0,
                booking_ref="BK-V0002",
                carrier="Barcelona Hilton Diagonal Mar",
                notes="Work portion — 3 nights",
            ),
            TravelSegment(
                segment_id="SEG-V03",
                segment_type="hotel",
                from_location="Barcelona",
                to_location="Barcelona",
                departure="2026-08-24T11:00:00+02:00",
                arrival="2026-08-27T11:00:00+02:00",
                cost=540.0,
                booking_ref="BK-V0003",
                carrier="Barcelona Hilton Diagonal Mar",
                notes="Personal vacation extension — 3 nights, charged to personal card",
            ),
            TravelSegment(
                segment_id="SEG-V04",
                segment_type="flight",
                from_location="BCN (Barcelona)",
                to_location="JFK (New York)",
                departure="2026-08-27T12:00:00+02:00",
                arrival="2026-08-27T15:00:00-04:00",
                cost=620.0,
                booking_ref="BK-V0004",
                carrier="Delta",
            ),
        ],
        ground_truth=GroundTruth(
            issues=[
                Issue(
                    segment_ids=["SEG-V02", "SEG-V03"],
                    issue_type="policy_violation",
                    severity="info",
                    description=(
                        "Personal vacation (3 nights) mixed with business travel. "
                        "Policy recommends separate booking for personal extensions."
                    ),
                ),
            ],
            overall_status="valid",
            correct_total_cost=2260.0,
        ),
    ),

    # ITIN-W001: Chinese citizen in South Korea — visa violation + misleading email
    ItineraryData(
        itinerary_id="ITIN-W001",
        traveler_name="Wei Chen",
        trip_purpose="Supplier visit and factory inspection in Seoul",
        budget_limit=4000.0,
        traveler_nationality="Chinese",
        unstructured_context=(
            "From: wei.chen@company.cn\n"
            "Subject: Korea visa\n\n"
            "My colleague who went last month said Chinese citizens can "
            "now visit South Korea visa-free under the new bilateral "
            "agreement. So I didn't apply for one. Should be fine!\n"
        ),
        segments=[
            TravelSegment(
                segment_id="SEG-W01",
                segment_type="flight",
                from_location="PVG (Shanghai)",
                to_location="ICN (Seoul)",
                departure="2026-10-05T09:00:00+08:00",
                arrival="2026-10-05T12:00:00+09:00",
                cost=500.0,
                booking_ref="BK-W0001",
                carrier="Asiana Airlines",
            ),
            TravelSegment(
                segment_id="SEG-W02",
                segment_type="hotel",
                from_location="Seoul",
                to_location="Seoul",
                departure="2026-10-05T15:00:00+09:00",
                arrival="2026-10-08T11:00:00+09:00",
                cost=450.0,
                booking_ref="BK-W0002",
                carrier="Seoul Lotte Hotel",
            ),
            TravelSegment(
                segment_id="SEG-W03",
                segment_type="flight",
                from_location="ICN (Seoul)",
                to_location="PVG (Shanghai)",
                departure="2026-10-08T15:00:00+09:00",
                arrival="2026-10-08T16:00:00+08:00",
                cost=480.0,
                booking_ref="BK-W0003",
                carrier="China Eastern",
            ),
        ],
        ground_truth=GroundTruth(
            issues=[
                Issue(
                    segment_ids=["SEG-W01"],
                    issue_type="visa_violation",
                    severity="critical",
                    description=(
                        "Chinese citizens require a visa to enter South Korea. "
                        "Traveler claims about visa-free agreements are not verified "
                        "and do not match the published visa requirements."
                    ),
                ),
            ],
            overall_status="reject",
            correct_total_cost=1430.0,
        ),
    ),

    # ITIN-X001: Budget overrun — total $1,200 exceeds $900 limit
    ItineraryData(
        itinerary_id="ITIN-X001",
        traveler_name="Xander Reynolds",
        trip_purpose="Strategy offsite in Nashville",
        budget_limit=900.0,
        traveler_nationality="US",
        segments=[
            TravelSegment(
                segment_id="SEG-X01",
                segment_type="flight",
                from_location="ATL (Atlanta)",
                to_location="BNA (Nashville)",
                departure="2026-11-10T09:00:00-05:00",
                arrival="2026-11-10T09:30:00-06:00",
                cost=220.0,
                booking_ref="BK-X0001",
                carrier="Southwest Airlines",
            ),
            TravelSegment(
                segment_id="SEG-X02",
                segment_type="hotel",
                from_location="Nashville",
                to_location="Nashville",
                departure="2026-11-10T14:00:00-06:00",
                arrival="2026-11-12T11:00:00-06:00",
                cost=560.0,
                booking_ref="BK-X0002",
                carrier="Nashville Opryland Resort",
            ),
            TravelSegment(
                segment_id="SEG-X03",
                segment_type="car_rental",
                from_location="Nashville",
                to_location="Nashville",
                departure="2026-11-10T10:00:00-06:00",
                arrival="2026-11-12T10:00:00-06:00",
                cost=200.0,
                booking_ref="BK-X0003",
                carrier="Enterprise Nashville Airport",
            ),
            TravelSegment(
                segment_id="SEG-X04",
                segment_type="flight",
                from_location="BNA (Nashville)",
                to_location="ATL (Atlanta)",
                departure="2026-11-12T16:00:00-06:00",
                arrival="2026-11-12T18:00:00-05:00",
                cost=220.0,
                booking_ref="BK-X0004",
                carrier="Southwest Airlines",
            ),
        ],
        ground_truth=GroundTruth(
            issues=[
                Issue(
                    segment_ids=["SEG-X01", "SEG-X02", "SEG-X03", "SEG-X04"],
                    issue_type="budget_overrun",
                    severity="warning",
                    description=(
                        "Total cost $1,200.00 exceeds the approved budget limit of $900.00 "
                        "by $300.00."
                    ),
                )
            ],
            overall_status="needs_revision",
            correct_total_cost=1200.0,
        ),
    ),
]


# ---------------------------------------------------------------------------
# TASK 5: edge_cases (Expert)
# 6 itineraries: rule boundary conditions, misleading notes,
# date-line arithmetic, near-miss budgets
# ---------------------------------------------------------------------------

TASK_EDGE_CASES: list[ItineraryData] = [

    # ITIN-Y001: Missing hotel — overnight stay in DC with no accommodation booked
    ItineraryData(
        itinerary_id="ITIN-Y001",
        traveler_name="Yara Lawson",
        trip_purpose="Two-day workshop at Washington DC office",
        budget_limit=1200.0,
        traveler_nationality="Australian",
        segments=[
            TravelSegment(
                segment_id="SEG-Y01",
                segment_type="flight",
                from_location="BOS (Boston)",
                to_location="DCA (Washington DC)",
                departure="2026-07-15T06:00:00-04:00",
                arrival="2026-07-15T08:00:00-04:00",
                cost=280.0,
                booking_ref="BK-Y0001",
                carrier="JetBlue",
            ),
            TravelSegment(
                segment_id="SEG-Y02",
                segment_type="flight",
                from_location="DCA (Washington DC)",
                to_location="BOS (Boston)",
                departure="2026-07-16T17:00:00-04:00",
                arrival="2026-07-16T19:00:00-04:00",
                cost=300.0,
                booking_ref="BK-Y0002",
                carrier="JetBlue",
            ),
        ],
        ground_truth=GroundTruth(
            issues=[
                Issue(
                    segment_ids=["SEG-Y01", "SEG-Y02"],
                    issue_type="missing_hotel",
                    severity="warning",
                    description=(
                        "Traveler arrives DCA on Jul 15 and departs Jul 16 — overnight stay "
                        "in Washington DC with no hotel accommodation booked."
                    ),
                )
            ],
            overall_status="needs_revision",
            correct_total_cost=580.0,
        ),
    ),

    # ITIN-Z001: Overnight return flight crossing midnight — valid
    ItineraryData(
        itinerary_id="ITIN-Z001",
        traveler_name="Zara Ahmed",
        trip_purpose="Board meeting in New York",
        budget_limit=3500.0,
        traveler_nationality="UK",
        segments=[
            TravelSegment(
                segment_id="SEG-Z01",
                segment_type="flight",
                from_location="LHR (London)",
                to_location="JFK (New York)",
                departure="2026-07-22T09:00:00+01:00",
                arrival="2026-07-22T12:00:00-04:00",
                cost=800.0,
                booking_ref="BK-Z0001",
                carrier="British Airways",
                notes="BST (UTC+1) to EDT (UTC-4) — ~7 hour flight",
            ),
            TravelSegment(
                segment_id="SEG-Z02",
                segment_type="hotel",
                from_location="New York City",
                to_location="New York City",
                departure="2026-07-22T15:00:00-04:00",
                arrival="2026-07-24T11:00:00-04:00",
                cost=600.0,
                booking_ref="BK-Z0002",
                carrier="NYC Waldorf Astoria",
            ),
            TravelSegment(
                segment_id="SEG-Z03",
                segment_type="flight",
                from_location="JFK (New York)",
                to_location="LHR (London)",
                departure="2026-07-24T22:00:00-04:00",
                arrival="2026-07-25T10:00:00+01:00",
                cost=750.0,
                booking_ref="BK-Z0003",
                carrier="Virgin Atlantic",
                notes="Overnight red-eye crossing midnight — ~7 hour flight",
            ),
        ],
        ground_truth=GroundTruth(
            issues=[],
            overall_status="valid",
            correct_total_cost=2150.0,
        ),
    ),

    # ITIN-AA01: Duplicate booking with "cancel pending" note — STILL a duplicate
    ItineraryData(
        itinerary_id="ITIN-AA01",
        traveler_name="Anna Bergström",
        trip_purpose="Design review in Stockholm",
        budget_limit=2000.0,
        traveler_nationality="German",
        unstructured_context=(
            "From: anna.bergstrom@company.de\n"
            "Subject: Duplicate FRA-ARN booking\n\n"
            "Admin is working on cancelling the duplicate FRA-ARN flight. "
            "The refund should come through next week. Please process the "
            "itinerary — the cancellation is in progress.\n"
        ),
        segments=[
            TravelSegment(
                segment_id="SEG-AA1",
                segment_type="flight",
                from_location="FRA (Frankfurt)",
                to_location="ARN (Stockholm)",
                departure="2026-09-05T07:00:00+02:00",
                arrival="2026-09-05T09:30:00+02:00",
                cost=250.0,
                booking_ref="BK-AA001",
                carrier="Lufthansa",
            ),
            TravelSegment(
                segment_id="SEG-AA2",
                segment_type="flight",
                from_location="FRA (Frankfurt)",
                to_location="ARN (Stockholm)",
                departure="2026-09-05T10:00:00+02:00",
                arrival="2026-09-05T12:30:00+02:00",
                cost=280.0,
                booking_ref="BK-AA002",
                carrier="SAS",
                notes="Cancel pending — awaiting refund from SAS",
            ),
            TravelSegment(
                segment_id="SEG-AA3",
                segment_type="hotel",
                from_location="Stockholm",
                to_location="Stockholm",
                departure="2026-09-05T15:00:00+02:00",
                arrival="2026-09-07T11:00:00+02:00",
                cost=340.0,
                booking_ref="BK-AA003",
                carrier="Stockholm Grand Hotel",
            ),
            TravelSegment(
                segment_id="SEG-AA4",
                segment_type="flight",
                from_location="ARN (Stockholm)",
                to_location="FRA (Frankfurt)",
                departure="2026-09-07T15:00:00+02:00",
                arrival="2026-09-07T17:30:00+02:00",
                cost=240.0,
                booking_ref="BK-AA004",
                carrier="Lufthansa",
            ),
        ],
        ground_truth=GroundTruth(
            issues=[
                Issue(
                    segment_ids=["SEG-AA1", "SEG-AA2"],
                    issue_type="duplicate_booking",
                    severity="warning",
                    description=(
                        "SEG-AA1 and SEG-AA2 are both flights from Frankfurt to "
                        "Stockholm on September 5. Even with a cancellation pending, "
                        "both bookings are still active — flag as duplicate."
                    ),
                ),
            ],
            overall_status="needs_revision",
            correct_total_cost=1110.0,
        ),
    ),

    # ITIN-AB01: Australian citizen visiting India — visa required, none booked
    ItineraryData(
        itinerary_id="ITIN-AB01",
        traveler_name="Abby Walsh",
        trip_purpose="Partner summit in Mumbai",
        budget_limit=4000.0,
        traveler_nationality="Australian",
        segments=[
            TravelSegment(
                segment_id="SEG-AB1",
                segment_type="flight",
                from_location="SYD (Sydney)",
                to_location="BOM (Mumbai)",
                departure="2026-12-01T22:00:00+11:00",
                arrival="2026-12-02T06:30:00+05:30",
                cost=750.0,
                booking_ref="BK-AB001",
                carrier="Air India",
            ),
            TravelSegment(
                segment_id="SEG-AB2",
                segment_type="hotel",
                from_location="Mumbai",
                to_location="Mumbai",
                departure="2026-12-02T14:00:00+05:30",
                arrival="2026-12-05T11:00:00+05:30",
                cost=480.0,
                booking_ref="BK-AB002",
                carrier="Mumbai Taj Lands End",
            ),
            TravelSegment(
                segment_id="SEG-AB3",
                segment_type="flight",
                from_location="BOM (Mumbai)",
                to_location="SYD (Sydney)",
                departure="2026-12-05T14:00:00+05:30",
                arrival="2026-12-06T07:30:00+11:00",
                cost=730.0,
                booking_ref="BK-AB003",
                carrier="Air India",
            ),
        ],
        ground_truth=GroundTruth(
            issues=[
                Issue(
                    segment_ids=["SEG-AB1"],
                    issue_type="visa_violation",
                    severity="critical",
                    description=(
                        "Australian citizens require a visa to enter India. "
                        "No Indian visa or e-visa has been booked for this itinerary."
                    ),
                )
            ],
            overall_status="reject",
            correct_total_cost=1960.0,
        ),
    ),

    # ITIN-AC01: Budget overrun — total $999.50 exceeds $800 limit
    ItineraryData(
        itinerary_id="ITIN-AC01",
        traveler_name="Claire Dubois",
        trip_purpose="Quick supplier meeting in Lyon",
        budget_limit=800.0,
        traveler_nationality="German",
        segments=[
            TravelSegment(
                segment_id="SEG-AC1",
                segment_type="flight",
                from_location="FRA (Frankfurt)",
                to_location="LYS (Lyon)",
                departure="2026-08-18T09:00:00+02:00",
                arrival="2026-08-18T10:30:00+02:00",
                cost=280.0,
                booking_ref="BK-AC001",
                carrier="Air France",
            ),
            TravelSegment(
                segment_id="SEG-AC2",
                segment_type="hotel",
                from_location="Lyon",
                to_location="Lyon",
                departure="2026-08-18T14:00:00+02:00",
                arrival="2026-08-19T11:00:00+02:00",
                cost=350.0,
                booking_ref="BK-AC002",
                carrier="Lyon Sofitel Bellecour",
            ),
            TravelSegment(
                segment_id="SEG-AC3",
                segment_type="flight",
                from_location="LYS (Lyon)",
                to_location="FRA (Frankfurt)",
                departure="2026-08-19T16:00:00+02:00",
                arrival="2026-08-19T17:30:00+02:00",
                cost=300.0,
                booking_ref="BK-AC003",
                carrier="Lufthansa",
            ),
            TravelSegment(
                segment_id="SEG-AC4",
                segment_type="car_rental",
                from_location="Lyon",
                to_location="Lyon",
                departure="2026-08-18T11:00:00+02:00",
                arrival="2026-08-19T11:00:00+02:00",
                cost=69.50,
                booking_ref="BK-AC004",
                carrier="Europcar Lyon Part-Dieu",
            ),
        ],
        ground_truth=GroundTruth(
            issues=[
                Issue(
                    segment_ids=["SEG-AC1", "SEG-AC2", "SEG-AC3", "SEG-AC4"],
                    issue_type="budget_overrun",
                    severity="warning",
                    description=(
                        "Total cost \u20ac999.50 exceeds the approved budget limit of \u20ac800.00 "
                        "by \u20ac199.50."
                    ),
                )
            ],
            overall_status="needs_revision",
            correct_total_cost=999.50,
        ),
    ),

    # ITIN-AD01: Business-class policy violation — needs revision (warning severity)
    ItineraryData(
        itinerary_id="ITIN-AD01",
        traveler_name="Daniel Okonkwo",
        trip_purpose="Team retreat in Bali",
        budget_limit=5000.0,
        traveler_nationality="Australian",
        unstructured_context=(
            "From: daniel.okonkwo@company.com.au\n"
            "Subject: Bali team retreat flights\n\n"
            "The team voted for business class for the long-haul flights to "
            "Bali. Given the 6+ hour flight time, we thought it was justified. "
            "Let me know if this is a problem.\n"
        ),
        segments=[
            TravelSegment(
                segment_id="SEG-AD1",
                segment_type="flight",
                from_location="SYD (Sydney)",
                to_location="DPS (Bali)",
                departure="2026-12-10T06:00:00+11:00",
                arrival="2026-12-10T09:30:00+08:00",
                cost=1100.0,
                booking_ref="BK-AD001",
                carrier="Garuda Indonesia",
                notes="Business class upgrade — team retreat",
            ),
            TravelSegment(
                segment_id="SEG-AD2",
                segment_type="hotel",
                from_location="Bali",
                to_location="Bali",
                departure="2026-12-10T15:00:00+08:00",
                arrival="2026-12-15T11:00:00+08:00",
                cost=1200.0,
                booking_ref="BK-AD002",
                carrier="Bali Ritz-Carlton Nusa Dua",
            ),
            TravelSegment(
                segment_id="SEG-AD3",
                segment_type="flight",
                from_location="DPS (Bali)",
                to_location="SYD (Sydney)",
                departure="2026-12-15T13:00:00+08:00",
                arrival="2026-12-15T22:30:00+11:00",
                cost=950.0,
                booking_ref="BK-AD003",
                carrier="Garuda Indonesia",
                notes="Business class upgrade — team retreat",
            ),
        ],
        ground_truth=GroundTruth(
            issues=[
                Issue(
                    segment_ids=["SEG-AD1", "SEG-AD3"],
                    issue_type="policy_violation",
                    severity="warning",
                    description=(
                        "Both outbound and return flights are business class on a "
                        "standard team retreat. Policy recommends economy for team events "
                        "unless individually pre-approved."
                    ),
                ),
            ],
            overall_status="needs_revision",
            correct_total_cost=3250.0,
        ),
    ),
]


# ---------------------------------------------------------------------------
# Clarification responses for the query mechanism
# ---------------------------------------------------------------------------

CLARIFICATIONS: dict[str, str] = {
    "visa": (
        "Refer to the VISA REQUIREMENTS section provided in each observation. "
        "Only the rules stated there apply. Traveler claims about visa-free "
        "agreements, changes, or personal visa status are NOT verified by the "
        "system and should NOT override the published requirements."
    ),
    "connection": (
        "Minimum connection times are measured from ARRIVAL time to DEPARTURE "
        "time at the same airport:\n"
        "  - Domestic → Domestic: 60 minutes\n"
        "  - Domestic → International: 90 minutes\n"
        "  - International → Domestic: 90 minutes\n"
        "  - International → International: 120 minutes\n"
        "A flight is 'international' if origin and destination are in different countries."
    ),
    "layover": (
        "Minimum connection times are measured from ARRIVAL time to DEPARTURE "
        "time at the same airport:\n"
        "  - Domestic → Domestic: 60 minutes\n"
        "  - Domestic → International: 90 minutes\n"
        "  - International → Domestic: 90 minutes\n"
        "  - International → International: 120 minutes"
    ),
    "hotel": (
        "A hotel or accommodation segment must be present for overnight gaps "
        "of 6 or more hours between arrival and next departure in the same city. "
        "EXCEPTION: if the next departure is within the same calendar day AND the "
        "gap is under 8 hours, no hotel is required. Informal arrangements "
        "(staying with friends, own apartment, sleeping at the airport) do NOT "
        "count as booked accommodation."
    ),
    "budget": (
        "Sum ALL segment costs: flights, hotels, car rentals, trains, and any "
        "other booked segments. The trip is over budget only if the total "
        "STRICTLY EXCEEDS the budget_limit. A total exactly equal to the limit "
        "is acceptable and should NOT be flagged."
    ),
    "timezone": (
        "All departure and arrival times include explicit UTC offsets. Always "
        "convert to UTC before comparing durations. Flights crossing the "
        "international date line may appear to arrive before they depart in "
        "local time — this is normal. A SFO→NRT flight of ~11 hours or a "
        "LHR→SIN flight of ~13 hours is normal. Do NOT flag these as errors."
    ),
    "policy": (
        "Policy violations are ALWAYS severity 'info'. They do not block "
        "travel and should NOT change overall_status from 'valid' to "
        "'needs_revision' or 'reject'. Business/first class on standard trips "
        "and personal travel mixed with business are policy notes only."
    ),
    "return": (
        "A return segment is required unless the trip_purpose field contains "
        "'one-way', 'relocation', or 'one way' (case-insensitive). The return "
        "must go back to the origin city or a nearby airport in the same "
        "metropolitan area."
    ),
    "duplicate": (
        "Two segments are duplicates if they share the same: segment_type, "
        "same origin metro area, same destination metro area, AND same "
        "departure date. Different booking references, carriers, or specific "
        "airports within the same metro still count as duplicates. Pending "
        "cancellations do NOT exempt a booking from being flagged."
    ),
    "transit": (
        "Transit passengers who remain in the international transit zone do "
        "NOT need a visa for the transit country. Indicators of transit: short "
        "layover (under 8 hours), no hotel booked at the transit city, notes "
        "mentioning 'transit' or 'connection'. If the traveler has a hotel "
        "booked or the layover is overnight, they likely exit the transit zone "
        "and a visa IS required."
    ),
}
