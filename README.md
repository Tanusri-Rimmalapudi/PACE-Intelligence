# PACE Intelligence Platform
> A modular public-record intelligence platform for analyzing **Property Assessed Clean Energy (PACE)** financing adoption across **Riverside County, California**.

PACE Intelligence aggregates and links public-record datasets from county and state agencies to provide a unified view of where PACE assessments are being placed, how adoption changes over time, and which programs and administrators are most active.

The platform combines public records, property data, tax records, and regulatory disclosures into a searchable analytics system powered by PostgreSQL, FastAPI, and Prometheus.

---
## Overview

PACE financing allows homeowners to fund energy-efficiency, renewable energy, and resiliency improvements through assessments attached to their property tax bills.

Although PACE data is publicly available, it is fragmented across multiple agencies and formats.

PACE Intelligence solves this by:

* Collecting data from public sources
* Linking records using Assessor Parcel Numbers (APNs)
* Normalizing inconsistent formats
* Tracking assessment activity over time
* Exposing analytics through a REST API
* Providing operational visibility through monitoring and metrics

The result is a reusable intelligence platform for researchers, journalists, policymakers, and civic technology projects.

---
## Data Sources

| Source                    | Agency                                                                                  | Access Method               |
| ------------------------- | --------------------------------------------------------------------------------------- | --------------------------- |
| County Recorder Documents | Riverside County Recorder-Clerk                                                         | Portal scrape + CPRA export |
| Assessor Property Records | Riverside County Assessor                                                               | Socrata Open Data API       |
| Secured Tax Roll          | Riverside County Tax Collector                                                          | Open data + CPRA export     |
| PACE Program Information  | CAEATFA-Approved Administrators                                                         | Public disclosures          |
| Program Reports           | California Alternative Energy and Advanced Transportation Financing Authority (CAEATFA) | Web scrape                  |
| Licensee Registry         | California Department of Financial Protection and Innovation (DFPI)                     | Web scrape                  |

---
## Architecture

```text
Data Sources
     │
     ▼
Connectors
     │
     ▼
Raw Cache (Filesystem)
     │
     ▼
Normalization
     │
     ▼
PostgreSQL
     │
     ▼
FastAPI
 ├── /analytics/adoption-trend
 ├── /analytics/by-zip
 ├── /analytics/by-program
 ├── /properties/{apn}
 └── /pace
```

---

## Key Features
### Modular Ingestion Framework
Each data source is implemented as an independent connector. Adding a new source requires only:
1. Creating a connector
2. Registering the source
3. Adding a pipeline task

### Raw-First Data Storage
All source responses are cached before transformation.
```text
Source → Raw Cache → Normalize → Database
```

### Entity Resolution
Records are linked using Assessor Parcel Number (APN).
This allows the platform to connect:
* Recorder filings
* Property records
* Tax roll information
* PACE assessments
into a single parcel-centric view.

#### Adoption Trends
```http
GET /analytics/adoption-trend
```
Returns assessment volume over time.

#### ZIP Code Analysis

```http
GET /analytics/by-zip
```

Returns PACE adoption by ZIP code.

#### Program Analysis

```http
GET /analytics/by-program
```

Returns assessment counts grouped by program administrator.

#### Property Lookup

```http
GET /properties/{apn}
```

Returns all linked information for a parcel.

---

### Observability

Operational metrics are exposed through Prometheus and Grafana.

Tracked metrics include:

* Ingestion duration
* Record counts
* Error rates
* Data freshness
* Source availability

This enables monitoring of both data quality and pipeline health.

---

## Tech Stack
### Backend
* Python 3.12
* FastAPI
* SQLAlchemy
* PostgreSQL

### Data Engineering
* AsyncIO
* Prefect
* Socrata APIs
* Public-record ingestion pipelines

### Monitoring
* Prometheus
* Grafana
* Structlog

### Infrastructure
* Docker
* Docker Compose


## Quick Start
### Prerequisites
* Python 3.12+
* Docker Desktop
* Git

### Clone Repository
```bash
git clone https://github.com/YOUR_ORG/pace-intelligence.git
cd pace-intelligence
```

### Configure Environment
```bash
cp .env.example .env
```
Edit environment variables as needed.

### Start Infrastructure
```bash
make dev
```

This launches:
* PostgreSQL
* Prometheus
* Grafana
and runs database migrations.

### Install Dependencies
```bash
make install
```

### Run Initial Ingestion
```bash
make ingest-all
```


### County Recorder Data

#### Option 1 — CPRA Export (Recommended)

Request a CSV export from Riverside County under the California Public Records Act.

Suggested filters:

* Document Type: NOTICE OF ASSESSMENT
* Grantee contains: PACE

Load the export:

```bash
python -c "
import asyncio
from pace_intel.ingestion.connectors.county_recorder import CountyRecorderConnector

asyncio.run(
    list(
        CountyRecorderConnector.load_from_csv(
            'export.csv'
        )
    )
)
"
```

#### Option 2 — Incremental Scrape

```bash
make ingest-recorder
```

Performs a limited rolling ingestion window.

---

## API Documentation

Start the API:

```bash
make api
```

Default URL:

```text
http://localhost:8000
```

Swagger UI:

```text
http://localhost:8000/docs
```

Examples:

```bash
curl http://localhost:8000/analytics/adoption-trend

curl http://localhost:8000/analytics/by-zip

curl http://localhost:8000/properties/123-456-789
```

---

## Monitoring

### Prometheus
```text
http://localhost:9090
```

### Grafana
```text
http://localhost:3000
```

Default credentials:
```text
Username: admin
Password: admin
```


## Project Structure
```text
src/pace_intel/

├── api/
├── compliance/
├── ingestion/
├── observability/
├── pipelines/
├── processing/
├── storage/
└── config.py
```

### Core Components

| Module        | Purpose                          |
| ------------- | -------------------------------- |
| ingestion     | Data collection                  |
| processing    | Normalization and linking        |
| storage       | Database models and repositories |
| api           | REST interface                   |
| observability | Logging and metrics              |
| compliance    | Legal safeguards and attribution |

## Disclaimer
PACE Intelligence is an independent research project and is not affiliated with Riverside County, CAEATFA, DFPI, or any PACE administrator. All information is derived from publicly available records.
