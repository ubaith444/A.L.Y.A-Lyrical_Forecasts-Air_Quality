# Alya Weather API

FastAPI backend for Indian coordinate-based forecast, air quality, and historical climate analysis.

## Run locally

```powershell
cd backend
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

OpenAPI is available at `http://localhost:8000/docs`. The frontend can use `http://localhost:8000/api/v1` as its API base URL.

## API highlights

- `GET /api/v1/health` and `GET /api/v1/ready`
- `GET /api/v1/locations` and `GET /api/v1/locations/{location_id}`
- `GET /api/v1/weather?location_id=new-delhi` and `GET /api/v1/weather/current?...`
- `GET /api/v1/air-quality?location_id=new-delhi`
- `POST /api/v1/historical/ingestions`, then poll `GET /api/v1/historical/ingestions/{job_id}`
- `GET /api/v1/historical/summary`, `/summary.csv`, `/monsoon`, `/compare`, `/export.csv`, and `/datasets`
- `POST /api/v1/evaluations` to run a chronological persistence-baseline evaluation
- `GET /api/v1/sources` for provenance and source limitations

All live requests require either `location_id` or a validated `latitude` and `longitude`. Forecast and air-quality values are provider grid-cell values for the requested coordinate; they are not district-wide or station observations.

## Data and correctness notes

- Live weather uses Open-Meteo Forecast API. Live air quality uses Open-Meteo Air Quality API.
- The API returns **US EPA AQI** where Open-Meteo provides it. It does not convert it into Indian AQI: required Indian AQI inputs and averaging periods are not established by this provider response.
- Historical ingestions explicitly request Open-Meteo's `ERA5` model and are labelled `reanalysis`, never direct station observations.
- Historical CSVs and SQLite metadata are created under `backend/data/` and intentionally ignored by Git. Rows retain source, kind, location, and retrieval time. Missing data is not interpolated or imputed.
- The location file is a documented, extendable seed catalogue of selected cities and two district reference coordinates. It is not a complete verified district catalogue. Extend `app/data/india_locations.json`; identifiers must remain unique and coordinates valid.
- No ML forecast is deployed. Evaluation records are reproducible persistence baselines using chronological train/test splits and MAE/RMSE.

## Configuration

Copy `backend/.env.example` to `backend/.env`. Use a comma-separated `CORS_ORIGINS` list in production and do not enable wildcard origins. All provider URLs, timeout/retry behavior, cache TTL, data path, and database path are environment-configurable through `app/core/config.py`.

## Frontend integration status

The repository frontend is currently a Vite shell and does not issue API calls. When it is implemented, configure its API base URL as `http://localhost:8000/api/v1` for local development, send either `location_id` or both `latitude` and `longitude` for live data, and handle the standard `error` response and nullable/unavailable pollutant values.

## Verification

```powershell
cd backend
pytest -q
mypy app
cd ..
ruff check backend
ruff format --check backend
```
