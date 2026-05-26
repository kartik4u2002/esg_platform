# Technical Tradeoffs (TRADEOFFS.md)

This document outlines three system components we deliberately chose **not** to build for this release, along with the technical and product rationale behind these decisions.

---

## 1. Dynamic Greenhouse Gas (GHG) Calculations Engine
* **What was omitted**: We did not build an in-app emissions engine that multiplies quantities (e.g., liters of diesel, kWh of electricity) into CO2 equivalents ($CO_2e$).
* **Why**: Greenhouse gas emissions factors change yearly, vary heavily by geographical region (e.g. the carbon intensity of 1 kWh of electricity in France is much lower than in Germany due to nuclear power), and depend on specific regulatory frameworks (e.g., EPA, DEFRA, GHG Protocol).
* **Alternative Strategy**: We focused heavily on perfecting **activity data normalization** (guaranteeing that raw volumes, meter readings, and flight distances are clean, de-duplicated, and standard-unit-compliant). In a real production deployment, this normalized data would be piped to a specialized, third-party emissions API (like *Climatiq* or *Wren*) or mapped to a database of regulatory emissions factors updated dynamically by sustainability experts, rather than hardcoding volatile factors directly inside Django.

---

## 2. In-App Drag-and-Drop CSV Column Mapping UI
* **What was omitted**: We did not build a user-facing interactive mapper where users can upload any CSV and drag columns to match our database fields.
* **Why**: Building a robust, error-tolerant frontend column mapping UI requires substantial development overhead (handling state transitions, partial uploads, type matching previews, and validation mapping rules).
* **Alternative Strategy**: We implemented a programmatic **Adapter Pattern** in the backend (`BaseAdapter`, `SAPProcurementAdapter`, etc.). This enforces a strict separation of concerns:
  1. Integrations are written as maintainable, testable Python classes.
  2. If a vendor changes their CSV output format, developers can modify a single adapter file in minutes.
  3. The system remains highly secure against injection and formatting exploits because file parsing is strictly validation-checked before writing to the database.

---

## 3. Fine-Grained Object-Level Permissions
* **What was omitted**: We did not implement row-level permissions within a single organization (e.g., "Analyst A can only view invoices from Plant 100, but not Plant 200").
* **Why**: Implementing object-level permissions (using libraries like `django-guardian`) increases query complexity and database indexing overhead, slowing down list views. For a launch product, tenant-level isolation is the primary security boundary.
* **Alternative Strategy**: We enforced strict **organization-level multi-tenancy** globally. The security boundary is simple: you can access everything in your organization, and absolutely nothing outside of it. Fine-grained organizational permissions (such as dividing users by country or cost-center divisions) can be added as a middleware layer later as the enterprise scale demands.
