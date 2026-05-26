# ESG Data Ingestion & Normalization Platform

## Architecture Overview

This platform is a full-stack Django REST + React application designed for ingesting, validating, normalizing, and reviewing Environmental, Social, and Governance (ESG) data from multiple sources. The backend is built on Django 5.x with Django REST Framework, using PostgreSQL for persistence, Celery for asynchronous pipeline processing, and Redis as the message broker. The frontend is a React 18 SPA using TypeScript, Tailwind CSS, TanStack Query, and React Router v6.

The system follows a multi-tenant architecture where all data is scoped to an organization via a `TenantQuerySet` mixin. Raw records are written once and never mutated (immutable `raw_payload`). Every state transition writes an `AuditEvent` row, and approved records are locked with a SHA-256 content hash for tamper detection. The ingestion pipeline runs as a Celery chain: **validate → normalize → detect anomalies → enqueue for review**, processing each record through source-specific adapters for SAP Procurement, Utility Electricity, and Corporate Travel data.

---

## Quick Start

```bash
# 1. Clone the repository and navigate to the project root
cd esg_platform

# 2. Copy the environment file
cp .env.example .env

# 3. Build and start all services
docker-compose up --build

# 4. Run database migrations (in a separate terminal)
docker-compose exec web python manage.py migrate

# 5. Seed demo data (creates org, users, records, runs pipeline)
docker-compose exec web python manage.py seed_demo_data

# 6. Access the application
# Frontend: http://localhost:5173
# API Docs: http://localhost:8000/api/docs/
# Admin:    http://localhost:8000/admin/
```

---

## Production Deployment (AWS)

The platform is deployed live on an **AWS EC2** instance at **[https://esg.monster](https://esg.monster)**, utilizing **Traefik** for automated Let's Encrypt SSL termination and reverse proxying.

To spin up the production stack:
```bash
docker-compose -f docker-compose.prod.yml --env-file .env.production up -d --build
```

---

## Sample Datasets

The following sample CSV files are included in the repository root for testing the ingestion system:
* **[spend_analysis_dataset.csv](file:///d:/Audit_system/esg_platform/spend_analysis_dataset.csv)**: Example procurement transaction dataset that can be used to test SAP Procurement (Scope 1) ingestion.
* **[smart_meter_data.csv](file:///d:/Audit_system/esg_platform/smart_meter_data.csv)**: Example smart meter electricity consumption dataset that can be used to test Utility Electricity (Scope 2) ingestion.

---

## Demo Credentials

| Role     | Email                | Password    | Permissions                    |
|----------|----------------------|-------------|--------------------------------|
| Admin    | admin@acme.com       | admin123    | Full access                    |
| Analyst  | analyst@acme.com     | analyst123  | Upload, review, approve/reject |
| Reviewer | reviewer@acme.com    | reviewer123 | Review and approve/reject      |

---

## API Endpoints Reference

### Authentication
| Method | Endpoint                         | Description              |
|--------|----------------------------------|--------------------------|
| POST   | `/api/v1/auth/token/`            | Obtain JWT token pair    |
| POST   | `/api/v1/auth/token/refresh/`    | Refresh access token     |
| GET    | `/api/v1/auth/profile/`          | Get current user profile |

### Ingestion
| Method | Endpoint                              | Description                        |
|--------|---------------------------------------|------------------------------------|
| GET    | `/api/v1/ingestion/sources/`          | List data sources                  |
| POST   | `/api/v1/ingestion/sources/`          | Create data source                 |
| GET    | `/api/v1/ingestion/batches/`          | List import batches                |
| GET    | `/api/v1/ingestion/batches/{id}/`     | Get batch detail                   |
| POST   | `/api/v1/ingestion/upload/sap/`       | Upload SAP CSV (multipart: `file`) |
| POST   | `/api/v1/ingestion/upload/utility/`   | Upload utility CSV (multipart)     |
| POST   | `/api/v1/ingestion/travel/trigger/`   | Trigger travel API pull            |

### Review
| Method | Endpoint                                   | Description                        |
|--------|--------------------------------------------|------------------------------------|
| GET    | `/api/v1/review/queue/`                    | Review queue (filterable)          |
| GET    | `/api/v1/review/records/{id}/`             | Record detail (raw + normalized)   |
| POST   | `/api/v1/review/records/{id}/approve/`     | Approve record `{ notes }`         |
| POST   | `/api/v1/review/records/{id}/reject/`      | Reject `{ notes, rejection_reason }`|

### Audit
| Method | Endpoint                              | Description                    |
|--------|---------------------------------------|--------------------------------|
| GET    | `/api/v1/audit/records/`              | Locked records (org-scoped)    |
| GET    | `/api/v1/audit/records/{id}/trail/`   | Audit event trail for entity   |
| GET    | `/api/v1/audit/export/?format=csv`    | Export locked records as CSV   |

### Documentation
| Method | Endpoint           | Description            |
|--------|--------------------|------------------------|
| GET    | `/api/schema/`     | OpenAPI YAML schema    |
| GET    | `/api/docs/`       | Swagger UI             |
| GET    | `/api/redoc/`      | ReDoc UI               |

---

## Pipeline Stages

Each raw record goes through a 4-step Celery chain:

```
┌──────────┐    ┌─────────────┐    ┌──────────────────┐    ┌───────────────────┐
│ Validate │ →  │ Normalize   │ →  │ Detect Anomalies │ →  │ Enqueue for Review│
└──────────┘    └─────────────┘    └──────────────────┘    └───────────────────┘
```

### 1. Validate
- Runs source-specific validators (field presence, positivity, date parsing, unit support)
- Checks for duplicates (SAP invoices), overlapping periods (utility), IATA codes (travel)
- Creates `ValidationFlag` records with severity levels: error, warning, info

### 2. Normalize
- Converts quantities to standard units (GAL→litre, MWh→kWh)
- Parses dates from multiple formats (DD.MM.YYYY, YYYY-MM-DD, MM/DD/YYYY)
- Handles European number formats (comma decimal separator)
- Logs every transformation in `normalization_log`

### 3. Detect Anomalies
- **Consumption spike**: Flags utility records > 3× average of last 6 readings
- **Quantity outlier**: Flags SAP records with z-score > 3.0
- **Missing flight distance**: Flags travel records with null distance_km

### 4. Enqueue for Review
- Sets `review_status = "pending"` on the NormalizedRecord
- Writes `ENQUEUED_FOR_REVIEW` audit event
- Updates batch progress counters

---

## How to Add a New Data Source

The platform uses an **adapter pattern** for data ingestion. To add a new source type:

### 1. Create an adapter class

```python
# apps/ingestion/adapters/new_source.py
from apps.ingestion.adapters.base import BaseAdapter, ParsedRow, compute_checksum

class NewSourceAdapter(BaseAdapter):
    source_type = 'new_source_type'

    def parse(self, source) -> Iterator[ParsedRow]:
        # Parse source data (CSV, JSON, API response)
        for i, row in enumerate(data):
            payload = self._map_columns(row)
            yield ParsedRow(
                raw_payload=payload,
                source_row_number=i + 1,
                checksum=compute_checksum(payload),
            )

    def validate_source_format(self, source) -> list[str]:
        # Return list of error messages if format is invalid
        return []
```

### 2. Register the adapter

```python
# apps/ingestion/adapters/__init__.py
from .new_source import NewSourceAdapter

ADAPTER_REGISTRY = {
    # ... existing adapters ...
    'new_source_type': NewSourceAdapter,
}
```

### 3. Add the source type to the model

```python
# apps/ingestion/models.py - DataSource.SOURCE_TYPES
('new_source_type', 'New Source'),
```

### 4. Add validators and normalizers

Add source-specific validation logic in `apps/pipeline/tasks.py:validate_record()` and normalization logic in `apps/pipeline/tasks.py:normalize_record()`.

### 5. Add anomaly detectors (optional)

Create detection functions in `apps/pipeline/anomaly.py` and wire them into `detect_anomalies()`.

---

## How the Audit Lock Works

When a reviewer approves a record, the system performs these steps atomically:

1. **Create ReviewDecision** — Records who approved and when
2. **Lock the NormalizedRecord** — Sets `is_locked = True`
3. **Compute content hash** — Serializes the record's key fields to canonical JSON and computes SHA-256
4. **Create AuditLock** — Stores the hash alongside the record reference
5. **Write AuditEvent** — Logs the approval with before/after state

### Tamper Detection

At any point, the system can verify a locked record hasn't been tampered with:

```python
from apps.audit.services import verify_lock_integrity

audit_lock = AuditLock.objects.get(normalized_record_id=record_id)
is_valid = verify_lock_integrity(audit_lock)  # True if untampered
```

### Database-Level Protection

The `AuditEvent` table has PostgreSQL rules that prevent UPDATE and DELETE:

```sql
CREATE RULE no_update_audit AS ON UPDATE TO audit_auditevent DO INSTEAD NOTHING;
CREATE RULE no_delete_audit AS ON DELETE TO audit_auditevent DO INSTEAD NOTHING;
```

Locked records return **HTTP 403** on any write attempt, enforced at both the view and model level.

---

## Services Architecture

```
┌─────────┐  ┌───────┐  ┌─────┐  ┌────────┐  ┌──────┐  ┌──────────┐
│ Frontend│  │  Web  │  │Redis│  │ Worker │  │ Beat │  │ Postgres │
│ :5173   │→ │ :8000 │→ │:6379│← │ Celery │  │Celery│  │  :5432   │
│ (Vite)  │  │(Django│  │     │  │        │  │      │  │          │
│         │  │  DRF) │  │     │  │        │  │      │  │          │
└─────────┘  └───────┘  └─────┘  └────────┘  └──────┘  └──────────┘
```

All services are orchestrated via Docker Compose with shared volumes for media files and code hot-reloading in development.
