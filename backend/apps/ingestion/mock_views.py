"""
Mock views for testing the travel data ingestion without an actual external API.

Provides a feed of 20 hardcoded travel records with deliberate data quality
issues for testing the validation and anomaly detection pipeline.
"""
from __future__ import annotations

from rest_framework.permissions import AllowAny
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView


class MockTravelFeedView(APIView):
    """
    Returns 20 hardcoded corporate travel records as JSON.

    Includes deliberate data quality issues:
    - 3 records with missing distance_km (null)
    - 1 record with invalid IATA code ('ZZZ' and '12X')
    """

    permission_classes = [AllowAny]
    authentication_classes = []

    def get(self, request: Request) -> Response:
        """Return the mock travel feed."""
        records = [
            {
                'trip_id': 'TRP-001',
                'employee_id': 'EMP-1001',
                'booking_source': 'CWT',
                'from_airport': 'JFK',
                'to_airport': 'LAX',
                'trip_type': 'round_trip',
                'travel_class': 'economy',
                'hotel_type': 'business',
                'distance_km': 3983,
                'transportation_cost': 450.00,
            },
            {
                'trip_id': 'TRP-002',
                'employee_id': 'EMP-1002',
                'booking_source': 'Concur',
                'from_airport': 'SFO',
                'to_airport': 'ORD',
                'trip_type': 'one_way',
                'travel_class': 'business',
                'hotel_type': 'luxury',
                'distance_km': 2960,
                'transportation_cost': 1250.00,
            },
            {
                'trip_id': 'TRP-003',
                'employee_id': 'EMP-1003',
                'booking_source': 'CWT',
                'from_airport': 'LHR',
                'to_airport': 'CDG',
                'trip_type': 'round_trip',
                'travel_class': 'economy',
                'hotel_type': 'standard',
                'distance_km': 344,
                'transportation_cost': 180.00,
            },
            {
                'trip_id': 'TRP-004',
                'employee_id': 'EMP-1004',
                'booking_source': 'Egencia',
                'from_airport': 'FRA',
                'to_airport': 'MUC',
                'trip_type': 'one_way',
                'travel_class': 'economy',
                'hotel_type': None,
                'distance_km': 304,
                'transportation_cost': 95.00,
            },
            # --- Record with missing distance_km (1 of 3) ---
            {
                'trip_id': 'TRP-005',
                'employee_id': 'EMP-1005',
                'booking_source': 'CWT',
                'from_airport': 'DXB',
                'to_airport': 'SIN',
                'trip_type': 'round_trip',
                'travel_class': 'business',
                'hotel_type': 'luxury',
                'distance_km': None,
                'transportation_cost': 2800.00,
            },
            {
                'trip_id': 'TRP-006',
                'employee_id': 'EMP-1006',
                'booking_source': 'Concur',
                'from_airport': 'NRT',
                'to_airport': 'ICN',
                'trip_type': 'one_way',
                'travel_class': 'economy',
                'hotel_type': 'business',
                'distance_km': 1193,
                'transportation_cost': 320.00,
            },
            {
                'trip_id': 'TRP-007',
                'employee_id': 'EMP-1007',
                'booking_source': 'Egencia',
                'from_airport': 'ATL',
                'to_airport': 'MIA',
                'trip_type': 'round_trip',
                'travel_class': 'economy',
                'hotel_type': 'standard',
                'distance_km': 973,
                'transportation_cost': 210.00,
            },
            # --- Record with missing distance_km (2 of 3) ---
            {
                'trip_id': 'TRP-008',
                'employee_id': 'EMP-1008',
                'booking_source': 'CWT',
                'from_airport': 'SYD',
                'to_airport': 'MEL',
                'trip_type': 'one_way',
                'travel_class': 'economy',
                'hotel_type': None,
                'distance_km': None,
                'transportation_cost': 150.00,
            },
            {
                'trip_id': 'TRP-009',
                'employee_id': 'EMP-1009',
                'booking_source': 'Concur',
                'from_airport': 'LAX',
                'to_airport': 'SEA',
                'trip_type': 'round_trip',
                'travel_class': 'business',
                'hotel_type': 'business',
                'distance_km': 1544,
                'transportation_cost': 680.00,
            },
            {
                'trip_id': 'TRP-010',
                'employee_id': 'EMP-1010',
                'booking_source': 'CWT',
                'from_airport': 'BOS',
                'to_airport': 'DCA',
                'trip_type': 'one_way',
                'travel_class': 'economy',
                'hotel_type': 'standard',
                'distance_km': 638,
                'transportation_cost': 175.00,
            },
            # --- Record with invalid IATA code ---
            {
                'trip_id': 'TRP-011',
                'employee_id': 'EMP-1011',
                'booking_source': 'Egencia',
                'from_airport': 'ZZZ',
                'to_airport': '12X',
                'trip_type': 'round_trip',
                'travel_class': 'economy',
                'hotel_type': 'standard',
                'distance_km': 500,
                'transportation_cost': 200.00,
            },
            {
                'trip_id': 'TRP-012',
                'employee_id': 'EMP-1012',
                'booking_source': 'CWT',
                'from_airport': 'DEN',
                'to_airport': 'PHX',
                'trip_type': 'round_trip',
                'travel_class': 'economy',
                'hotel_type': 'business',
                'distance_km': 942,
                'transportation_cost': 285.00,
            },
            {
                'trip_id': 'TRP-013',
                'employee_id': 'EMP-1013',
                'booking_source': 'Concur',
                'from_airport': 'EWR',
                'to_airport': 'DTW',
                'trip_type': 'one_way',
                'travel_class': 'economy',
                'hotel_type': None,
                'distance_km': 804,
                'transportation_cost': 195.00,
            },
            # --- Record with missing distance_km (3 of 3) ---
            {
                'trip_id': 'TRP-014',
                'employee_id': 'EMP-1014',
                'booking_source': 'CWT',
                'from_airport': 'HKG',
                'to_airport': 'TPE',
                'trip_type': 'round_trip',
                'travel_class': 'business',
                'hotel_type': 'luxury',
                'distance_km': None,
                'transportation_cost': 1100.00,
            },
            {
                'trip_id': 'TRP-015',
                'employee_id': 'EMP-1015',
                'booking_source': 'Egencia',
                'from_airport': 'AMS',
                'to_airport': 'BCN',
                'trip_type': 'one_way',
                'travel_class': 'economy',
                'hotel_type': 'standard',
                'distance_km': 1235,
                'transportation_cost': 165.00,
            },
            {
                'trip_id': 'TRP-016',
                'employee_id': 'EMP-1016',
                'booking_source': 'CWT',
                'from_airport': 'IAH',
                'to_airport': 'MSP',
                'trip_type': 'round_trip',
                'travel_class': 'economy',
                'hotel_type': 'business',
                'distance_km': 1738,
                'transportation_cost': 380.00,
            },
            {
                'trip_id': 'TRP-017',
                'employee_id': 'EMP-1017',
                'booking_source': 'Concur',
                'from_airport': 'DFW',
                'to_airport': 'SLC',
                'trip_type': 'one_way',
                'travel_class': 'economy',
                'hotel_type': None,
                'distance_km': 1434,
                'transportation_cost': 225.00,
            },
            {
                'trip_id': 'TRP-018',
                'employee_id': 'EMP-1018',
                'booking_source': 'Egencia',
                'from_airport': 'MCO',
                'to_airport': 'CLT',
                'trip_type': 'round_trip',
                'travel_class': 'business',
                'hotel_type': 'business',
                'distance_km': 821,
                'transportation_cost': 540.00,
            },
            {
                'trip_id': 'TRP-019',
                'employee_id': 'EMP-1019',
                'booking_source': 'CWT',
                'from_airport': 'PHL',
                'to_airport': 'TPA',
                'trip_type': 'one_way',
                'travel_class': 'economy',
                'hotel_type': 'standard',
                'distance_km': 1354,
                'transportation_cost': 190.00,
            },
            {
                'trip_id': 'TRP-020',
                'employee_id': 'EMP-1020',
                'booking_source': 'Concur',
                'from_airport': 'PDX',
                'to_airport': 'LAS',
                'trip_type': 'round_trip',
                'travel_class': 'economy',
                'hotel_type': 'standard',
                'distance_km': 1527,
                'transportation_cost': 310.00,
            },
        ]
        return Response(records)
