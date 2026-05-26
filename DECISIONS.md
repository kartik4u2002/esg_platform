# Technical Decisions & Assumptions (DECISIONS.md)

This document details the ambiguities resolved, architectural assumptions made, scope boundaries defined, and open questions we would address with the Product Manager if this were a live project.

---

## 1. Scope Boundaries: Handled vs Ignored Fields

Each raw data source contains extra business metadata. To maintain focus on core emissions auditing, we made explicit decisions on which fields are actively normalized/validated and which are ignored (stored in raw form but not processed).

### 1.1 SAP Procurement (Scope 1)
* **Handled**: 
  * `quantity` (`MENGE`) and `unit` (`MEINS`) — converted to standardized `litre` (or `kilogram` for LPG).
  * `posting_date` (`BUDAT`) — normalized to a standard ISO date representing the single point-in-time emission event.
  * `fuel_type` (`Brennstoffart`) — maps to emission factors (Diesel, Gasoline, LPG).
  * `plant_code` (`WERKS`) — mapped to `facility_or_entity` to isolate emissions by site.
  * `invoice_number` (`BELNR`) and `company_code` (`BUKRS`) — used to construct duplicate detection keys.
* **Ignored**:
  * `amount` (`DMBTR`) — saved in raw payload but not used. Carbon footprint calculations are strictly activity-based (quantity of fuel), not spend-based.
  * `vendor_id` (`LIFNR`) and `material_number` (`MATNR`) — stored as metadata.

### 1.2 Utility Electricity (Scope 2)
* **Handled**:
  * `usage` and `unit` — normalized to standard `kWh` (1 MWh = 1000 kWh).
  * `billing_start` and `billing_end` — parsed into a date range (`period_start`, `period_end`) to handle period overlap validation.
  * `facility_id` and `meter_id` — used to isolate consumption by building/meter.
* **Ignored**:
  * `tariff` — saved in metadata. Tariffs change frequently and represent financial variables, not physical energy consumption.

### 1.3 Corporate Travel (Scope 3)
* **Handled**:
  * `from_airport` and `to_airport` — validated against a set of known 3-letter IATA codes.
  * `distance_km` — used to quantify transport distance.
  * `trip_id` — uniqueness tracking.
* **Ignored**:
  * `transportation_cost`, `travel_class` (economy vs business), `hotel_type` — stored as metadata. 
  * *Assumption*: We assumed a flat distance-based emissions multiplier for the initial pipeline. Real deployments would adjust emissions factors based on `travel_class` (first class has a higher carbon footprint per passenger than economy).

---

## 2. Resolved Ambiguities

### 2.1 European vs. US Number Formats
* **Ambiguity**: CSV quantities could arrive as `1.234,56` (European format) or `1,234.56` (US format).
* **Resolution**: Created a smart normalizer (`normalize_quantity`) that scans the positions of commas and decimals:
  * If both are present, it dynamically detects which is the decimal separator based on right-most occurrence.
  * If only a comma is present and it is followed by 1 or 2 digits, it is treated as a decimal separator (e.g. `123,5` -> `123.5`). If followed by exactly 3 digits, it is treated as a thousands separator (e.g., `1,000` -> `1000.0`).

### 2.2 Date Format Flexibility
* **Ambiguity**: Ingested files have inconsistent date formats across vendors (`DD.MM.YYYY`, `YYYY-MM-DD`, `MM/DD/YYYY`).
* **Resolution**: The pipeline iteratively tests dates against 5 popular formats (`%d.%m.%Y`, `%Y-%m-%d`, `%m/%d/%Y`, `%d-%m-%Y`, `%Y/%m/%d`). If a format matches, the pipeline logs the matched format pattern inside `normalization_log` for auditing.

### 2.3 Internal Container Communication
* **Ambiguity**: During Scope 3 API ingestion, Gunicorn returned a `400 Bad Request`.
* **Resolution**: Gunicorn only trusts incoming proxy headers from `127.0.0.1` by default. Because Traefik runs in a separate bridge network container, we configured Gunicorn to trust all proxy headers by adding `--forwarded-allow-ips '*'` and appending internal Docker hostnames (`web`, `localhost`) to Django's `ALLOWED_HOSTS`.

---

## 3. Product Manager Questions

If we could align with the Product Manager, we would raise these key system design questions:

1. **Self-Correction and Editing Policy**: Should analysts be allowed to edit a record's normalized values directly, or must corrections only occur by uploading a *revised batch*?
   * *Our choice*: We allowed reviewers to change a record's status to `approved`/`rejected` and log a reason, but did not allow modifying the raw values to guarantee the source of truth is never tampered with.
2. **Missing Flight Distances**: If an API response is missing `distance_km`, should we automatically calculate it using the Great-Circle distance between `from_airport` and `to_airport` via coordinates, or fail the record?
   * *Our choice*: We raised a warning flag (`MISSING_DISTANCE`) and passed it to the review queue for manual reviewer input.
3. **Timezones**: What is the system standard timezone for carbon reporting?
   * *Our choice*: We defaulted all dates to UTC on import to keep calculations consistent, ignoring local daylight saving transitions.
