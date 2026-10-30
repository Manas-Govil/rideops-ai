# RideOps AI

**A governed multi-agent analytics application for NYC Yellow Taxi data.**

RideOps AI combines a Python/FastAPI backend, a React frontend, PostgreSQL, an ETL pipeline, SQL guardrails, and specialized agents for natural-language mobility analytics.

> This repository contains the application source code and setup instructions. The January 2025 Yellow Taxi Parquet dataset is not included; download it separately as described below. Performance figures should be reproduced locally before being treated as benchmark claims.

## Architecture

```text
NYC Yellow Taxi Parquet + Taxi Zone Lookup
                  |
                  v
       Python ETL (PyArrow / Pandas)
                  |
       Transformations + quality checks
                  |
                  v
             PostgreSQL
                  |
       Analytical SQL views
                  |
                  v
     SQL validation and query limits
                  |
                  v
       RideOps multi-agent graph
       /          |            \
    Help       Quality       SQL Analyst
                  |
                  v
          FastAPI REST API
                  |
                  v
           React + Vite UI
```

## Technology

- **Backend:** Python, FastAPI, Pydantic, SQLAlchemy, psycopg2
- **Data engineering:** PyArrow, Pandas, NumPy
- **Database:** PostgreSQL
- **Frontend:** React, Vite, Axios, Recharts
- **Testing:** Python `unittest`

## Prerequisites

For the Windows setup scripts:

- Windows 10/11
- Python 3.11-3.13 (Python 3.13 recommended)
- Node.js LTS (includes npm)
- PostgreSQL 15 or newer
- Git

Check installations:

```powershell
py --version
node --version
npm --version
psql --version
```

## Quick start (Windows)

### 1. Clone the repository

```powershell
git clone https://github.com/YOUR_USERNAME/rideops-ai.git
cd rideops-ai
```

Replace `YOUR_USERNAME` with the GitHub account that owns the repository.

### 2. Run first-time setup

```powershell
.\setup.bat
```

This creates `.venv`, installs Python requirements, creates `.env` from `.env.example` if needed, and installs frontend packages with `npm ci`.

### 3. Configure PostgreSQL

Create a database named `rideops`. For example, from `psql`:

```sql
CREATE DATABASE rideops;
```

Connect to it and apply the schema:

```powershell
psql -U postgres -h localhost -d rideops -f sql/schema.sql
```

Set your actual PostgreSQL connection string in the project-root `.env` file:

```dotenv
DATABASE_URL=postgresql://postgres:YOUR_PASSWORD@localhost:5432/rideops
ENVIRONMENT=development
LOG_LEVEL=INFO
```

Do not commit `.env`. It may contain passwords or API credentials. The committed `.env.example` is only a template.

### 4. Prepare the data

The repository includes the processed taxi-zone lookup file at:

`data/processed/taxi_zone_lookup_clean.csv`

Download the **January 2025 NYC Yellow Taxi trip data** from the NYC Taxi & Limousine Commission (TLC) Trip Record Data page:

https://www.nyc.gov/site/tlc/about/tlc-trip-record-data.page

Place the downloaded Parquet file at:

`data/raw/yellow_tripdata_2025-01.parquet`

The raw Parquet file is intentionally excluded from Git because it is large and is distributed by the data publisher.

### 5. Load the data

From the repository root, with `.venv` active or by using its Python executable:

```powershell
.\.venv\Scripts\python.exe -m app.etl.run_etl
```

The ETL pipeline expects PostgreSQL and the source Parquet file to be available. It loads taxi zones as needed and processes the trip data in batches.

Apply analytical views after the ETL:

```powershell
.\.venv\Scripts\python.exe -m app.database.apply_views
```

### 6. Start the application

```powershell
.\start.bat
```

The script opens separate terminal windows for the backend and frontend. Keep both open while using the app.

- Frontend: http://localhost:5173
- API root: http://127.0.0.1:8000
- Swagger API documentation: http://127.0.0.1:8000/docs
- Health endpoint: http://127.0.0.1:8000/api/health

To start services manually:

**Terminal 1, backend**

```powershell
.\.venv\Scripts\python.exe -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

**Terminal 2, frontend**

```powershell
cd frontend
npm run dev
```

## Tests

Run the SQL guardrail tests from the repository root:

```powershell
.\.venv\Scripts\python.exe -m unittest tests/test_guardrails.py
```

## Repository layout

```text
rideops-ai/
├── app/
│   ├── agents/          # Help, quality, and SQL analyst agents
│   ├── api/             # FastAPI routes and request/response schemas
│   ├── database/        # Database connection and query helpers
│   ├── etl/             # Extraction, transformation, loading, quality checks
│   ├── evaluation/      # Evaluation utilities
│   ├── graph/           # Agent orchestration
│   └── guardrails/      # SQL validation and query limits
├── data/
│   ├── processed/       # Cleaned taxi-zone lookup
│   └── raw/             # Downloaded Parquet data (not committed)
├── frontend/            # React + Vite application
├── sql/                 # PostgreSQL schema, indexes, and views
├── tests/               # Automated tests
├── .env.example
├── requirements.txt
├── setup.bat
└── start.bat
```

## Configuration and data safety

- Never commit `.env`, passwords, API keys, or private credentials.
- Do not commit `.venv`, `node_modules`, frontend build output, or the raw Parquet dataset.
- Use a PostgreSQL account appropriate for local development. The application should use a restricted database role in shared or production deployments.
- The SQL guardrails are application-level controls, not a replacement for database permissions.

## Current scope and limitations

- The included setup scripts target Windows.
- PostgreSQL must be installed and running separately.
- The full application requires the external Parquet dataset and a populated database.
- The repository does not bundle a hosted deployment or preloaded database.
- Review `.env.example`, SQL files, and the source before exposing a deployment publicly.

## License

No license has been selected yet. Unless a license is added, the repository is publicly viewable if published as public, but reuse is not automatically granted.
