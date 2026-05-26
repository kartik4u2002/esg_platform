# Data Sources & Formats (SOURCES.md)

This document outlines the real-world formats researched for each of the three emission sources, sample payloads, and edge cases that could break the pipeline in production.

---

## 1. SAP Procurement (Scope 1 Direct Fuel Emissions)

### 1.1 Real-World Format Research
SAP ERP systems export material ledgers and procurement databases using standard German table fields (e.g., table `EKBE` or custom transaction exports). 
* **What we learned**: Key fields use fixed SAP naming abbreviations:
  * `BELNR` (Belegnummer - Accounting Document Number)
  * `BUDAT` (Buchungsdatum - Posting Date)
  * `MENGE` (Quantity)
  * `MEINS` (Base Unit of Measure)
  * `DMBTR` (Amount in Local Currency)
  * `WERKS` (Plant/Facility Code)

### 1.2 Sample Payload (CSV)
```csv
BELNR,BUKRS,WERKS,MATNR,MENGE,MEINS,DMBTR,BUDAT,LIFNR,Brennstoffart
INV-001,CC01,P100,MAT001,150.5,L,2500.00,15.03.2024,V001,Diesel
INV-002,CC01,P100,MAT002,75,GAL,3200.00,2024-03-18,V002,Gasoline
```

### 1.3 Production Vulnerabilities (What would break)
1. **German Number Formats**: A quantity representing one thousand liters could be written as `1.000` (European) or `1,000` (US). If the locale settings mismatch, a quantity of `1` could be parsed as `1000` or vice versa.
2. **Dynamic Units**: Units such as `BARRELS` or `TONS` require dynamic density factors (e.g., converting tons of LPG to liters requires knowing temperature and specific gravity).

---

## 2. Utility Electricity (Scope 2 Indirect Energy Emissions)

### 2.1 Real-World Format Research
Utility providers (e.g., PG&E, National Grid, EDF) provide Green Button XML or standard billing CSV exports for corporate accounts.
* **What we learned**: Billing cycles are rarely aligned to clean calendar months. They are periodic, representing meter reading ranges (e.g. Jan 14 to Feb 12). 

### 2.2 Sample Payload (CSV)
```csv
meter_id,billing_start,billing_end,usage,unit,tariff,facility_id
MET-8801,2024-01-01,2024-01-31,12500,kWh,Standard-Biz,FAC-NYC
MET-8802,15.01.2024,14.02.2024,14.5,MWh,OffPeak-Biz,FAC-LON
```

### 2.3 Production Vulnerabilities (What would break)
1. **Meter Swaps**: If a facility exchanges meter `A` for meter `B` mid-month, both meters might run in parallel for 2 days. This triggers our `OVERLAPPING_PERIOD` warning flag, requiring human resolution to prevent double-counting.
2. **Estimated vs. Actual Bills**: Utility providers often issue bills based on "estimated" readings and adjust them next month. This leads to retroactively modified historical rows.

---

## 3. Corporate Travel (Scope 3 Business Flights)

### 2.1 Real-World Format Research
Modern travel management companies (like Concur, TravelPerk, or Navan) expose REST APIs returning JSON lists representing completed trip segments.
* **What we learned**: Flight distances are calculated using the Great-Circle distance formula between airport pairs identified by 3-letter IATA codes. 

### 2.2 Sample Payload (JSON)
```json
[
  {
    "trip_id": "TRP-001",
    "employee_id": "EMP-1001",
    "booking_source": "TravelPerk",
    "from_airport": "JFK",
    "to_airport": "LAX",
    "trip_type": "round_trip",
    "travel_class": "economy",
    "distance_km": 3983,
    "transportation_cost": 450.00
  }
]
```

### 2.3 Production Vulnerabilities (What would break)
1. **Multi-Leg Flights / Layovers**: A booking for `JFK -> LHR -> BOM` represented as a single flight would have a different distance than the direct line `JFK -> BOM`. The system must parse individual segment legs rather than assuming one direct segment.
2. **Minor/Military Airports**: If an executive flies to a private or minor regional airport, it might lack a registered 3-letter IATA code, causing IATA validation checks to fail.
