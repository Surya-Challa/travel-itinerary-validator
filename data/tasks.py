"""
Task data: 12 travel itineraries across 3 difficulty levels.

Each task has 4 itineraries:
  - 2–3 itineraries with real constraint violations
  - 1–2 itineraries that are VALID (false-positive traps)

Ground truth is hidden from the agent via the environment layer.
"""

from __future__ import annotations
from models import TravelSegment, Issue, GroundTruth, ItineraryData

# ---------------------------------------------------------------------------
# Constant rule text shown to agent every step
# ---------------------------------------------------------------------------

VALIDATION_RULES = """
TRAVEL ITINERARY VALIDATION RULES
===================================

1. OVERLAPPING SEGMENTS
   No two active travel segments (flights, trains) may overlap in time.
   Compare times in UTC — convert from stated UTC offsets before comparing.

2. IMPOSSIBLE CONNECTION
   Minimum layover between connecting flights/trains at the same airport/station:
     - Domestic → Domestic: 60 minutes
     - Domestic → International: 90 minutes
     - International → Domestic: 90 minutes
     - International → International: 120 minutes
   A flight is "international" if origin and destination are in different countries.

3. MISSING HOTEL
   If an itinerary has a gap of 6 or more hours between arrival in a city and
   the next departure from the same city (or a nearby airport in the same metro),
   a hotel or accommodation must be present for the overnight period.
   Exception: if the next departure is within the same calendar day as arrival
   and the gap is under 8 hours, no hotel is required.

4. TIMEZONE INTERPRETATION
   All departure/arrival times include a UTC offset (e.g. -04:00, +09:00).
   Always interpret times using the given offset. Do NOT flag a flight as having
   an impossible duration due to date-line or timezone transitions.
   Example: SFO→NRT departing 11:00-07:00 and arriving next day 14:00+09:00
   is valid (~11 hrs actual flight time).

5. BUDGET OVERRUN
   Sum all segment costs. If the total exceeds the stated budget_limit, flag
   as budget_overrun with severity "warning".

6. MISSING RETURN
   Unless trip_purpose explicitly contains the words "one-way", "relocation",
   or "one way", the itinerary must include a return segment back to the
   origin city/country.

7. DUPLICATE BOOKING
   If two segments have the same segment_type, same origin metro, same destination
   metro, and same departure date, flag as duplicate_booking with severity "warning",
   even if the booking_ref or carrier differs.

8. VISA VIOLATIONS
   Check traveler_nationality against destination and transit countries.
   Use only the visa rules provided in VISA_REQUIREMENTS below.
   Transit passengers who remain in the international zone do NOT need a visa.
   Flag visa issues as severity "critical".

9. POLICY VIOLATIONS
   First-class or business-class on a standard business trip = severity "info".
   Personal/leisure travel mixed into a business trip = severity "info".
   These do not block the trip but should be noted.
""".strip()

VISA_REQUIREMENTS = """
VISA REQUIREMENTS BY NATIONALITY
==================================

US CITIZENS:
  No visa required: EU/Schengen countries, UK, Canada, Japan, South Korea,
                    Australia, Singapore, Mexico, New Zealand, Switzerland.
  Visa required: China, India, Russia, Brazil, Saudi Arabia, Vietnam, Egypt.

INDIAN CITIZENS:
  No visa required: Nepal, Bhutan, Mauritius, Maldives, Indonesia (30-day VOA).
  Visa required: US, all EU/Schengen countries, UK, Canada, Japan,
                 South Korea, Australia, China, Singapore, UAE.

UK CITIZENS:
  No visa required: EU/Schengen countries, US, Canada, Japan, South Korea,
                    Australia, Singapore, Mexico, New Zealand.
  Visa required: China, India, Russia, Saudi Arabia, Vietnam, Egypt.

GERMAN CITIZENS:
  No visa required: EU/Schengen countries, UK, US, Canada, Japan, South Korea,
                    Australia, Singapore, New Zealand, Mexico, Switzerland.
  Visa required: China, India, Russia, Saudi Arabia, Vietnam, Egypt.

CHINESE CITIZENS:
  No visa required: Serbia, UAE, Thailand (30-day), Singapore (30-day),
                    Malaysia, Maldives, Morocco.
  Visa required: US, all EU/Schengen countries, UK, Canada, Japan, South Korea,
                 Australia, India, Russia, New Zealand.

AUSTRALIAN CITIZENS:
  No visa required: EU/Schengen countries, UK, US, Canada, Japan, South Korea,
                    Singapore, New Zealand, Malaysia, Thailand, Indonesia.
  Visa required: China, India, Russia, Saudi Arabia, Vietnam, Egypt, Brazil.
""".strip()


# ---------------------------------------------------------------------------
# TASK 1: basic_validation (Easy)
# 4 itineraries: 3 with clear single violations, 1 clean
# ---------------------------------------------------------------------------

TASK_BASIC_VALIDATION: list[ItineraryData] = [

    # ITIN-A001: Overlapping flights — arrives 10:30 CDT, next departs 09:00 CDT
    ItineraryData(
        itinerary_id="ITIN-A001",
        traveler_name="Alice Chen",
        trip_purpose="Client meeting in Chicago",
        budget_limit=2000.0,
        traveler_nationality="US",
        segments=[
            TravelSegment(
                segment_id="SEG-A01",
                segment_type="flight",
                from_location="JFK (New York)",
                to_location="ORD (Chicago)",
                departure="2026-06-15T08:00:00-04:00",
                arrival="2026-06-15T10:30:00-05:00",
                cost=350.0,
                booking_ref="BK-10001",
                carrier="United Airlines",
            ),
            TravelSegment(
                segment_id="SEG-A02",
                segment_type="flight",
                from_location="ORD (Chicago)",
                to_location="LAX (Los Angeles)",
                departure="2026-06-15T09:00:00-05:00",
                arrival="2026-06-15T11:30:00-07:00",
                cost=280.0,
                booking_ref="BK-10002",
                carrier="American Airlines",
                notes="Booked separately — should be flagged",
            ),
            TravelSegment(
                segment_id="SEG-A03",
                segment_type="hotel",
                from_location="Chicago",
                to_location="Chicago",
                departure="2026-06-15T15:00:00-05:00",
                arrival="2026-06-17T11:00:00-05:00",
                cost=380.0,
                booking_ref="BK-10003",
                carrier="Chicago Marriott",
            ),
            TravelSegment(
                segment_id="SEG-A04",
                segment_type="flight",
                from_location="ORD (Chicago)",
                to_location="JFK (New York)",
                departure="2026-06-17T18:00:00-05:00",
                arrival="2026-06-17T21:30:00-04:00",
                cost=320.0,
                booking_ref="BK-10004",
                carrier="United Airlines",
            ),
        ],
        ground_truth=GroundTruth(
            issues=[
                Issue(
                    segment_ids=["SEG-A01", "SEG-A02"],
                    issue_type="overlapping_segments",
                    severity="critical",
                    description=(
                        "SEG-A01 arrives Chicago at 10:30 CDT but SEG-A02 departs "
                        "Chicago at 09:00 CDT — flight departs before the prior one lands."
                    ),
                )
            ],
            overall_status="reject",
            correct_total_cost=1330.0,
        ),
    ),

    # ITIN-B001: Fully clean itinerary — valid, no issues
    ItineraryData(
        itinerary_id="ITIN-B001",
        traveler_name="Bob Martinez",
        trip_purpose="Annual conference in Denver",
        budget_limit=1800.0,
        traveler_nationality="US",
        segments=[
            TravelSegment(
                segment_id="SEG-B01",
                segment_type="flight",
                from_location="SFO (San Francisco)",
                to_location="DEN (Denver)",
                departure="2026-07-10T07:00:00-07:00",
                arrival="2026-07-10T10:30:00-06:00",
                cost=290.0,
                booking_ref="BK-20001",
                carrier="Southwest Airlines",
            ),
            TravelSegment(
                segment_id="SEG-B02",
                segment_type="hotel",
                from_location="Denver",
                to_location="Denver",
                departure="2026-07-10T15:00:00-06:00",
                arrival="2026-07-13T11:00:00-06:00",
                cost=540.0,
                booking_ref="BK-20002",
                carrier="Denver Hilton",
            ),
            TravelSegment(
                segment_id="SEG-B03",
                segment_type="flight",
                from_location="DEN (Denver)",
                to_location="SFO (San Francisco)",
                departure="2026-07-13T16:00:00-06:00",
                arrival="2026-07-13T17:30:00-07:00",
                cost=310.0,
                booking_ref="BK-20003",
                carrier="Southwest Airlines",
            ),
        ],
        ground_truth=GroundTruth(
            issues=[],
            overall_status="valid",
            correct_total_cost=1140.0,
        ),
    ),

    # ITIN-C001: Missing hotel night — hotel checks out Aug 7 but flight is Aug 8
    ItineraryData(
        itinerary_id="ITIN-C001",
        traveler_name="Carol Patel",
        trip_purpose="Partner workshop in Seattle",
        budget_limit=2500.0,
        traveler_nationality="US",
        segments=[
            TravelSegment(
                segment_id="SEG-C01",
                segment_type="flight",
                from_location="BOS (Boston)",
                to_location="SEA (Seattle)",
                departure="2026-08-05T06:00:00-04:00",
                arrival="2026-08-05T09:30:00-07:00",
                cost=420.0,
                booking_ref="BK-30001",
                carrier="Delta",
            ),
            TravelSegment(
                segment_id="SEG-C02",
                segment_type="hotel",
                from_location="Seattle",
                to_location="Seattle",
                departure="2026-08-05T15:00:00-07:00",
                arrival="2026-08-07T11:00:00-07:00",
                cost=400.0,
                booking_ref="BK-30002",
                carrier="Seattle Westin",
            ),
            TravelSegment(
                segment_id="SEG-C03",
                segment_type="flight",
                from_location="SEA (Seattle)",
                to_location="BOS (Boston)",
                departure="2026-08-08T20:00:00-07:00",
                arrival="2026-08-09T04:30:00-04:00",
                cost=450.0,
                booking_ref="BK-30003",
                carrier="JetBlue",
            ),
        ],
        ground_truth=GroundTruth(
            issues=[
                Issue(
                    segment_ids=["SEG-C02", "SEG-C03"],
                    issue_type="missing_hotel",
                    severity="warning",
                    description=(
                        "Hotel (SEG-C02) checks out August 7 but return flight "
                        "(SEG-C03) departs August 8. Night of August 7 has no accommodation."
                    ),
                )
            ],
            overall_status="needs_revision",
            correct_total_cost=1270.0,
        ),
    ),

    # ITIN-D001: Budget overrun — $1690 spent vs $1200 budget
    ItineraryData(
        itinerary_id="ITIN-D001",
        traveler_name="David Kim",
        trip_purpose="Training workshop in Miami",
        budget_limit=1200.0,
        traveler_nationality="US",
        segments=[
            TravelSegment(
                segment_id="SEG-D01",
                segment_type="flight",
                from_location="ORD (Chicago)",
                to_location="MIA (Miami)",
                departure="2026-09-01T09:00:00-05:00",
                arrival="2026-09-01T13:00:00-04:00",
                cost=380.0,
                booking_ref="BK-40001",
                carrier="Spirit Airlines",
            ),
            TravelSegment(
                segment_id="SEG-D02",
                segment_type="hotel",
                from_location="Miami",
                to_location="Miami",
                departure="2026-09-01T14:00:00-04:00",
                arrival="2026-09-04T11:00:00-04:00",
                cost=750.0,
                booking_ref="BK-40002",
                carrier="Miami Beach Resort",
            ),
            TravelSegment(
                segment_id="SEG-D03",
                segment_type="car_rental",
                from_location="Miami",
                to_location="Miami",
                departure="2026-09-01T14:00:00-04:00",
                arrival="2026-09-04T12:00:00-04:00",
                cost=210.0,
                booking_ref="BK-40003",
                carrier="Enterprise",
            ),
            TravelSegment(
                segment_id="SEG-D04",
                segment_type="flight",
                from_location="MIA (Miami)",
                to_location="ORD (Chicago)",
                departure="2026-09-04T17:00:00-04:00",
                arrival="2026-09-04T19:30:00-05:00",
                cost=350.0,
                booking_ref="BK-40004",
                carrier="Spirit Airlines",
            ),
        ],
        ground_truth=GroundTruth(
            issues=[
                Issue(
                    segment_ids=["SEG-D01", "SEG-D02", "SEG-D03", "SEG-D04"],
                    issue_type="budget_overrun",
                    severity="warning",
                    description=(
                        "Total cost is $1,690 which exceeds the $1,200 budget limit by $490."
                    ),
                )
            ],
            overall_status="needs_revision",
            correct_total_cost=1690.0,
        ),
    ),
]


# ---------------------------------------------------------------------------
# TASK 2: connection_logic (Medium)
# 4 itineraries: timezone trap, connection, duplicate, missing return
# ---------------------------------------------------------------------------

TASK_CONNECTION_LOGIC: list[ItineraryData] = [

    # ITIN-E001: Valid timezone trap — SFO→NRT looks odd crossing date line but is correct
    ItineraryData(
        itinerary_id="ITIN-E001",
        traveler_name="Elena Volkov",
        trip_purpose="Tech summit in Tokyo",
        budget_limit=5000.0,
        traveler_nationality="US",
        segments=[
            TravelSegment(
                segment_id="SEG-E01",
                segment_type="flight",
                from_location="SFO (San Francisco)",
                to_location="NRT (Tokyo)",
                departure="2026-07-01T11:00:00-07:00",
                arrival="2026-07-02T14:00:00+09:00",
                cost=1200.0,
                booking_ref="BK-50001",
                carrier="ANA",
                notes="Crosses international date line — actual flight ~11 hrs",
            ),
            TravelSegment(
                segment_id="SEG-E02",
                segment_type="hotel",
                from_location="Tokyo",
                to_location="Tokyo",
                departure="2026-07-02T15:00:00+09:00",
                arrival="2026-07-05T11:00:00+09:00",
                cost=660.0,
                booking_ref="BK-50002",
                carrier="Tokyo Shinagawa Prince Hotel",
            ),
            TravelSegment(
                segment_id="SEG-E03",
                segment_type="flight",
                from_location="NRT (Tokyo)",
                to_location="SFO (San Francisco)",
                departure="2026-07-05T17:00:00+09:00",
                arrival="2026-07-05T10:00:00-07:00",
                cost=1100.0,
                booking_ref="BK-50003",
                carrier="ANA",
                notes="Arrives same date it departs (date line) — actual flight ~10 hrs",
            ),
        ],
        ground_truth=GroundTruth(
            issues=[],
            overall_status="valid",
            correct_total_cost=2960.0,
        ),
    ),

    # ITIN-F001: Impossible connection at JFK — 30-min layover for international
    ItineraryData(
        itinerary_id="ITIN-F001",
        traveler_name="Frank Nakamura",
        trip_purpose="Supplier meeting in London",
        budget_limit=4000.0,
        traveler_nationality="US",
        segments=[
            TravelSegment(
                segment_id="SEG-F01",
                segment_type="flight",
                from_location="LAX (Los Angeles)",
                to_location="JFK (New York)",
                departure="2026-06-20T06:00:00-07:00",
                arrival="2026-06-20T14:30:00-04:00",
                cost=320.0,
                booking_ref="BK-60001",
                carrier="Delta",
            ),
            TravelSegment(
                segment_id="SEG-F02",
                segment_type="flight",
                from_location="JFK (New York)",
                to_location="LHR (London)",
                departure="2026-06-20T15:00:00-04:00",
                arrival="2026-06-21T03:00:00+01:00",
                cost=800.0,
                booking_ref="BK-60002",
                carrier="British Airways",
                notes="International flight — 120 min minimum connection required",
            ),
            TravelSegment(
                segment_id="SEG-F03",
                segment_type="hotel",
                from_location="London",
                to_location="London",
                departure="2026-06-21T09:00:00+01:00",
                arrival="2026-06-23T11:00:00+01:00",
                cost=600.0,
                booking_ref="BK-60003",
                carrier="London Savoy",
            ),
            TravelSegment(
                segment_id="SEG-F04",
                segment_type="flight",
                from_location="LHR (London)",
                to_location="LAX (Los Angeles)",
                departure="2026-06-23T11:00:00+01:00",
                arrival="2026-06-23T14:00:00-07:00",
                cost=850.0,
                booking_ref="BK-60004",
                carrier="Virgin Atlantic",
            ),
        ],
        ground_truth=GroundTruth(
            issues=[
                Issue(
                    segment_ids=["SEG-F01", "SEG-F02"],
                    issue_type="impossible_connection",
                    severity="critical",
                    description=(
                        "SEG-F01 arrives JFK at 14:30 EDT. SEG-F02 departs JFK at 15:00 EDT. "
                        "Only 30 minutes layover — international connection requires 120 minutes minimum."
                    ),
                )
            ],
            overall_status="needs_revision",
            correct_total_cost=2570.0,
        ),
    ),

    # ITIN-G001: Duplicate hotel booking — same hotel, same dates, different booking refs
    ItineraryData(
        itinerary_id="ITIN-G001",
        traveler_name="Grace Liu",
        trip_purpose="Sales kickoff in Austin",
        budget_limit=2000.0,
        traveler_nationality="US",
        segments=[
            TravelSegment(
                segment_id="SEG-G01",
                segment_type="flight",
                from_location="EWR (New York)",
                to_location="AUS (Austin)",
                departure="2026-08-12T08:00:00-04:00",
                arrival="2026-08-12T11:00:00-05:00",
                cost=310.0,
                booking_ref="BK-70001",
                carrier="United Airlines",
            ),
            TravelSegment(
                segment_id="SEG-G02",
                segment_type="hotel",
                from_location="Austin",
                to_location="Austin",
                departure="2026-08-12T15:00:00-05:00",
                arrival="2026-08-14T11:00:00-05:00",
                cost=340.0,
                booking_ref="BK-70002",
                carrier="Austin Marriott Downtown",
            ),
            TravelSegment(
                segment_id="SEG-G03",
                segment_type="hotel",
                from_location="Austin",
                to_location="Austin",
                departure="2026-08-12T15:00:00-05:00",
                arrival="2026-08-14T11:00:00-05:00",
                cost=340.0,
                booking_ref="BK-70003",
                carrier="Austin Marriott Downtown",
                notes="Duplicate booking — same hotel, same dates",
            ),
            TravelSegment(
                segment_id="SEG-G04",
                segment_type="flight",
                from_location="AUS (Austin)",
                to_location="EWR (New York)",
                departure="2026-08-14T16:00:00-05:00",
                arrival="2026-08-14T20:30:00-04:00",
                cost=330.0,
                booking_ref="BK-70004",
                carrier="United Airlines",
            ),
        ],
        ground_truth=GroundTruth(
            issues=[
                Issue(
                    segment_ids=["SEG-G02", "SEG-G03"],
                    issue_type="duplicate_booking",
                    severity="warning",
                    description=(
                        "SEG-G02 and SEG-G03 are both hotel bookings at Austin Marriott Downtown "
                        "for the same dates (Aug 12–14). Duplicate booking — cancel one."
                    ),
                )
            ],
            overall_status="needs_revision",
            correct_total_cost=1320.0,
        ),
    ),

    # ITIN-H001: Missing return flight — no return, purpose doesn't say one-way
    ItineraryData(
        itinerary_id="ITIN-H001",
        traveler_name="Hiro Tanaka",
        trip_purpose="Extended client engagement in Boston",
        budget_limit=3000.0,
        traveler_nationality="US",
        segments=[
            TravelSegment(
                segment_id="SEG-H01",
                segment_type="flight",
                from_location="SFO (San Francisco)",
                to_location="BOS (Boston)",
                departure="2026-09-15T07:00:00-07:00",
                arrival="2026-09-15T15:30:00-04:00",
                cost=380.0,
                booking_ref="BK-80001",
                carrier="JetBlue",
            ),
            TravelSegment(
                segment_id="SEG-H02",
                segment_type="hotel",
                from_location="Boston",
                to_location="Boston",
                departure="2026-09-15T16:00:00-04:00",
                arrival="2026-09-22T11:00:00-04:00",
                cost=1260.0,
                booking_ref="BK-80002",
                carrier="Boston Park Plaza",
            ),
        ],
        ground_truth=GroundTruth(
            issues=[
                Issue(
                    segment_ids=["SEG-H01"],
                    issue_type="missing_return",
                    severity="warning",
                    description=(
                        "No return flight from Boston to San Francisco. "
                        "Trip purpose does not indicate one-way or relocation."
                    ),
                )
            ],
            overall_status="needs_revision",
            correct_total_cost=1640.0,
        ),
    ),
]


# ---------------------------------------------------------------------------
# TASK 3: complex_trips (Hard)
# 4 itineraries: multi-issue, visa violations, compound errors, valid complex trap
# ---------------------------------------------------------------------------

TASK_COMPLEX_TRIPS: list[ItineraryData] = [

    # ITIN-I001: Three issues — missing hotel Frankfurt, budget overrun, first-class policy
    ItineraryData(
        itinerary_id="ITIN-I001",
        traveler_name="Isabella Torres",
        trip_purpose="Multi-client tour: London, Paris, Frankfurt",
        budget_limit=2500.0,
        traveler_nationality="US",
        segments=[
            TravelSegment(
                segment_id="SEG-I01",
                segment_type="flight",
                from_location="JFK (New York)",
                to_location="LHR (London)",
                departure="2026-10-01T19:00:00-04:00",
                arrival="2026-10-02T07:00:00+01:00",
                cost=900.0,
                booking_ref="BK-90001",
                carrier="British Airways",
                notes="First class upgrade requested by traveler",
            ),
            TravelSegment(
                segment_id="SEG-I02",
                segment_type="hotel",
                from_location="London",
                to_location="London",
                departure="2026-10-02T09:00:00+01:00",
                arrival="2026-10-04T11:00:00+01:00",
                cost=320.0,
                booking_ref="BK-90002",
                carrier="London Premier Inn",
            ),
            TravelSegment(
                segment_id="SEG-I03",
                segment_type="train",
                from_location="London St Pancras",
                to_location="Paris Gare du Nord",
                departure="2026-10-04T08:00:00+01:00",
                arrival="2026-10-04T11:30:00+02:00",
                cost=180.0,
                booking_ref="BK-90003",
                carrier="Eurostar",
            ),
            TravelSegment(
                segment_id="SEG-I04",
                segment_type="hotel",
                from_location="Paris",
                to_location="Paris",
                departure="2026-10-04T13:00:00+02:00",
                arrival="2026-10-05T11:00:00+02:00",
                cost=140.0,
                booking_ref="BK-90004",
                carrier="Paris Ibis Gare du Nord",
            ),
            TravelSegment(
                segment_id="SEG-I05",
                segment_type="flight",
                from_location="CDG (Paris)",
                to_location="FRA (Frankfurt)",
                departure="2026-10-05T07:00:00+02:00",
                arrival="2026-10-05T08:30:00+02:00",
                cost=160.0,
                booking_ref="BK-90005",
                carrier="Lufthansa",
            ),
            TravelSegment(
                segment_id="SEG-I06",
                segment_type="car_rental",
                from_location="Frankfurt",
                to_location="Frankfurt",
                departure="2026-10-05T09:30:00+02:00",
                arrival="2026-10-06T09:00:00+02:00",
                cost=90.0,
                booking_ref="BK-90006",
                carrier="Hertz Frankfurt Airport",
            ),
            TravelSegment(
                segment_id="SEG-I07",
                segment_type="flight",
                from_location="FRA (Frankfurt)",
                to_location="JFK (New York)",
                departure="2026-10-06T10:00:00+02:00",
                arrival="2026-10-06T13:00:00-04:00",
                cost=950.0,
                booking_ref="BK-90007",
                carrier="Lufthansa",
            ),
        ],
        ground_truth=GroundTruth(
            issues=[
                Issue(
                    segment_ids=["SEG-I05", "SEG-I07"],
                    issue_type="missing_hotel",
                    severity="warning",
                    description=(
                        "Arrives Frankfurt at 08:30 on Oct 5 (SEG-I05), "
                        "return flight Oct 6 at 10:00 (SEG-I07). "
                        "Night of October 5 in Frankfurt has no hotel."
                    ),
                ),
                Issue(
                    segment_ids=["SEG-I01", "SEG-I02", "SEG-I03", "SEG-I04",
                                  "SEG-I05", "SEG-I06", "SEG-I07"],
                    issue_type="budget_overrun",
                    severity="warning",
                    description=(
                        "Total cost is $2,740 which exceeds the $2,500 budget limit by $240."
                    ),
                ),
                Issue(
                    segment_ids=["SEG-I01"],
                    issue_type="policy_violation",
                    severity="info",
                    description=(
                        "SEG-I01 notes indicate a first-class upgrade on a standard business trip. "
                        "Policy requires economy class unless pre-approved."
                    ),
                ),
            ],
            overall_status="needs_revision",
            correct_total_cost=2740.0,
        ),
    ),

    # ITIN-J001: Visa violations for Indian citizen traveling to Japan and South Korea
    ItineraryData(
        itinerary_id="ITIN-J001",
        traveler_name="Jai Krishnamurthy",
        trip_purpose="Client demos in Tokyo and Seoul",
        budget_limit=6000.0,
        traveler_nationality="Indian",
        segments=[
            TravelSegment(
                segment_id="SEG-J01",
                segment_type="flight",
                from_location="DEL (New Delhi)",
                to_location="NRT (Tokyo)",
                departure="2026-10-10T01:00:00+05:30",
                arrival="2026-10-10T13:00:00+09:00",
                cost=800.0,
                booking_ref="BK-A0001",
                carrier="JAL",
            ),
            TravelSegment(
                segment_id="SEG-J02",
                segment_type="hotel",
                from_location="Tokyo",
                to_location="Tokyo",
                departure="2026-10-10T15:00:00+09:00",
                arrival="2026-10-13T11:00:00+09:00",
                cost=540.0,
                booking_ref="BK-A0002",
                carrier="Tokyo Shinjuku Prince Hotel",
            ),
            TravelSegment(
                segment_id="SEG-J03",
                segment_type="flight",
                from_location="NRT (Tokyo)",
                to_location="ICN (Seoul)",
                departure="2026-10-13T10:00:00+09:00",
                arrival="2026-10-13T12:30:00+09:00",
                cost=250.0,
                booking_ref="BK-A0003",
                carrier="Korean Air",
            ),
            TravelSegment(
                segment_id="SEG-J04",
                segment_type="hotel",
                from_location="Seoul",
                to_location="Seoul",
                departure="2026-10-13T14:00:00+09:00",
                arrival="2026-10-15T11:00:00+09:00",
                cost=300.0,
                booking_ref="BK-A0004",
                carrier="Seoul Gangnam Marriott",
            ),
            TravelSegment(
                segment_id="SEG-J05",
                segment_type="flight",
                from_location="ICN (Seoul)",
                to_location="DEL (New Delhi)",
                departure="2026-10-15T14:00:00+09:00",
                arrival="2026-10-15T19:00:00+05:30",
                cost=750.0,
                booking_ref="BK-A0005",
                carrier="Air India",
            ),
        ],
        ground_truth=GroundTruth(
            issues=[
                Issue(
                    segment_ids=["SEG-J01"],
                    issue_type="visa_violation",
                    severity="critical",
                    description=(
                        "Indian citizens require a visa to enter Japan. "
                        "No Japan visa noted for traveler Jai Krishnamurthy."
                    ),
                ),
                Issue(
                    segment_ids=["SEG-J03"],
                    issue_type="visa_violation",
                    severity="critical",
                    description=(
                        "Indian citizens require a visa to enter South Korea. "
                        "No South Korea visa noted for traveler Jai Krishnamurthy."
                    ),
                ),
            ],
            overall_status="reject",
            correct_total_cost=2640.0,
        ),
    ),

    # ITIN-K001: Two issues — duplicate Chicago→NYC flight + missing hotel night in NYC
    ItineraryData(
        itinerary_id="ITIN-K001",
        traveler_name="Karen Walsh",
        trip_purpose="Quarterly board meetings in New York City",
        budget_limit=3000.0,
        traveler_nationality="US",
        segments=[
            TravelSegment(
                segment_id="SEG-K01",
                segment_type="flight",
                from_location="ORD (Chicago)",
                to_location="LGA (New York)",
                departure="2026-11-03T07:00:00-05:00",
                arrival="2026-11-03T10:30:00-04:00",
                cost=290.0,
                booking_ref="BK-B0001",
                carrier="American Airlines",
            ),
            TravelSegment(
                segment_id="SEG-K02",
                segment_type="flight",
                from_location="ORD (Chicago)",
                to_location="JFK (New York)",
                departure="2026-11-03T08:00:00-05:00",
                arrival="2026-11-03T11:30:00-04:00",
                cost=310.0,
                booking_ref="BK-B0002",
                carrier="Delta",
                notes="Separate booking to JFK same day — different terminal but same city",
            ),
            TravelSegment(
                segment_id="SEG-K03",
                segment_type="hotel",
                from_location="New York City",
                to_location="New York City",
                departure="2026-11-03T15:00:00-04:00",
                arrival="2026-11-05T11:00:00-04:00",
                cost=480.0,
                booking_ref="BK-B0003",
                carrier="NYC Hyatt Midtown",
                notes="Board meetings run Nov 3–6 but hotel only covers 2 nights",
            ),
            TravelSegment(
                segment_id="SEG-K04",
                segment_type="flight",
                from_location="JFK (New York)",
                to_location="ORD (Chicago)",
                departure="2026-11-06T18:00:00-04:00",
                arrival="2026-11-06T19:30:00-05:00",
                cost=300.0,
                booking_ref="BK-B0004",
                carrier="Delta",
            ),
        ],
        ground_truth=GroundTruth(
            issues=[
                Issue(
                    segment_ids=["SEG-K01", "SEG-K02"],
                    issue_type="duplicate_booking",
                    severity="warning",
                    description=(
                        "SEG-K01 (ORD→LGA) and SEG-K02 (ORD→JFK) both depart Chicago "
                        "to New York City on November 3. LGA and JFK serve the same metro. "
                        "Duplicate booking — cancel one."
                    ),
                ),
                Issue(
                    segment_ids=["SEG-K03", "SEG-K04"],
                    issue_type="missing_hotel",
                    severity="warning",
                    description=(
                        "Hotel (SEG-K03) checks out November 5 but return flight (SEG-K04) "
                        "departs November 6. Night of November 5 has no accommodation."
                    ),
                ),
            ],
            overall_status="needs_revision",
            correct_total_cost=1380.0,
        ),
    ),

    # ITIN-L001: Valid complex trip — one-way relocation + timezone crossing (false-positive trap)
    ItineraryData(
        itinerary_id="ITIN-L001",
        traveler_name="Liam O'Brien",
        trip_purpose="One-way relocation to Singapore office",
        budget_limit=4000.0,
        traveler_nationality="UK",
        segments=[
            TravelSegment(
                segment_id="SEG-L01",
                segment_type="flight",
                from_location="LHR (London)",
                to_location="SIN (Singapore)",
                departure="2026-11-15T22:00:00+00:00",
                arrival="2026-11-16T18:00:00+08:00",
                cost=1400.0,
                booking_ref="BK-C0001",
                carrier="Singapore Airlines",
                notes="LHR UTC+0, Singapore UTC+8 — actual ~13 hrs flight time",
            ),
            TravelSegment(
                segment_id="SEG-L02",
                segment_type="hotel",
                from_location="Singapore",
                to_location="Singapore",
                departure="2026-11-16T19:00:00+08:00",
                arrival="2026-11-30T11:00:00+08:00",
                cost=1800.0,
                booking_ref="BK-C0002",
                carrier="Marina Bay Sands Serviced Apartments",
                notes="Serviced apartment for relocation period",
            ),
        ],
        ground_truth=GroundTruth(
            issues=[],
            overall_status="valid",
            correct_total_cost=3200.0,
        ),
    ),
]


# ---------------------------------------------------------------------------
# Clarification responses for the query mechanism
# ---------------------------------------------------------------------------

CLARIFICATIONS: dict[str, str] = {
    "visa": (
        "Refer to the VISA REQUIREMENTS section provided in each observation. "
        "Only the rules stated there apply."
    ),
    "connection": (
        "Minimum connection times are measured from ARRIVAL time to DEPARTURE "
        "time of the next segment, both converted to the SAME timezone. "
        "Domestic-Domestic: 60 min. Any international leg: 90 min."
    ),
    "budget": (
        "Sum ALL segment costs. Compare to budget_limit. "
        "Exactly at limit = valid. Over limit by any amount = budget_overrun."
    ),
    "hotel": (
        "A hotel is required for any overnight stay (arrival and departure on "
        "different calendar dates at the destination). Same-day turnarounds "
        "with gap < 8 hours do NOT require a hotel."
    ),
}

# ---------------------------------------------------------------------------
# Task registry
# ---------------------------------------------------------------------------

TASKS: dict[str, list[ItineraryData]] = {
    "basic_validation": TASK_BASIC_VALIDATION,
    "connection_logic": TASK_CONNECTION_LOGIC,
    "complex_trips": TASK_COMPLEX_TRIPS,
}
