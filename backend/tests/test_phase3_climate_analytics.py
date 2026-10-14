"""
Tamil Nadu Climate & Forecast Intelligence Platform
Phase 3 Test Suite: Climate Analytics, Seasonal Rainfall, Anomalies & Reports

Tests:
1. Historical Climate Trends (/api/climate/trends)
2. Seasonal Rainfall & 38-District Rankings (/api/climate/seasonal-rainfall)
3. Climate Anomaly Detection & Matrix Heatmap (/api/climate/anomalies)
4. Multi-District Climate Comparisons (/api/climate/district-comparison)
5. Climate Indicators & Executive Summary (/api/climate/summary)
6. Report Generation, Metadata & PDF/CSV Download (/api/climate/reports)
7. Scientific Validation (Zero-baseline safety, 1991–2020 LPA definition, non-PostgreSQL architecture)
"""

import os
import pytest
import requests

BASE_URL = "http://127.0.0.1:8000"


def test_climate_trends_api():
    r = requests.get(f"{BASE_URL}/api/climate/trends?district=chennai&start_year=2015&end_year=2024&season=all", timeout=10)
    assert r.status_code == 200
    data = r.json()
    assert data["district_id"] == "chennai"
    assert "1991–2020" in data["baseline_period"]
    assert "warming_rate_c_per_decade" in data
    assert isinstance(data["warming_rate_c_per_decade"], (int, float))
    assert len(data["yearly_trends"]) == 10
    
    # Check structure of trend items
    sample = data["yearly_trends"][0]
    assert "year" in sample
    assert "mean_temp_celsius" in sample
    assert "temp_anomaly_celsius" in sample
    assert "rainfall_mm" in sample
    assert "rainfall_departure_pct" in sample
    assert "rainy_days" in sample
    assert "heavy_rain_days" in sample
    assert "max_dry_spell_days" in sample
    assert sample["imd_category"] in ["Large Excess", "Excess", "Normal", "Deficient", "Large Deficient"]


def test_seasonal_rainfall_and_rankings():
    r = requests.get(f"{BASE_URL}/api/climate/seasonal-rainfall?year=2024&season=all", timeout=10)
    assert r.status_code == 200
    data = r.json()
    assert "monsoons_statewide" in data
    assert "northeast_monsoon" in data["monsoons_statewide"]
    assert "southwest_monsoon" in data["monsoons_statewide"]
    
    # 38-district rankings
    rankings = data["district_rankings"]
    assert len(rankings) == 38
    assert rankings[0]["rank"] == 1
    assert rankings[0]["recorded_mm"] >= rankings[-1]["recorded_mm"]
    assert len(data["top_5_wettest_districts"]) == 5
    assert len(data["top_5_most_deficient_districts"]) == 5


def test_climate_anomalies_and_heatmaps():
    r = requests.get(f"{BASE_URL}/api/climate/anomalies?district=coimbatore&start_year=2015&end_year=2024", timeout=10)
    assert r.status_code == 200
    data = r.json()
    assert data["district_id"] == "coimbatore"
    assert "severity_summary" in data
    assert "matrix_heatmap" in data
    assert len(data["matrix_heatmap"]) == 120 # 10 years * 12 months
    
    cell = data["matrix_heatmap"][0]
    assert "temp_anomaly_celsius" in cell
    assert "rainfall_anomaly_mm" in cell
    assert "rainfall_departure_pct" in cell
    assert cell["severity"] in ["Neutral", "Warning", "High-Risk"]
    assert "prolonged_dry_spells" in data
    assert isinstance(data["prolonged_dry_spells"], list)


def test_climate_district_comparison():
    r = requests.get(f"{BASE_URL}/api/climate/district-comparison?districts=chennai,coimbatore,madurai,nilgiris", timeout=10)
    assert r.status_code == 200
    data = r.json()
    assert data["count"] == 4
    for d in data["districts"]:
        assert "annual_normal_rainfall_mm" in d
        assert "nem_normal_mm" in d
        assert "swm_normal_mm" in d
        assert "mean_annual_temp_celsius" in d
        assert "rainy_days_per_year" in d


def test_climate_summary_indicators():
    r = requests.get(f"{BASE_URL}/api/climate/summary?year=2024", timeout=10)
    assert r.status_code == 200
    data = r.json()
    assert "statewide_rainfall" in data
    assert "monsoon_status" in data
    assert "key_findings" in data
    assert len(data["key_findings"]) >= 3


def test_climate_report_generation_and_download():
    # 1. Generate Report
    payload = {
        "district": "madurai",
        "start_year": 2015,
        "end_year": 2024,
        "season": "all",
        "variable": "all",
        "format": "both"
    }
    r_create = requests.post(f"{BASE_URL}/api/climate/reports", json=payload, timeout=15)
    assert r_create.status_code == 200
    rep = r_create.json()
    report_id = rep["report_id"]
    assert report_id.startswith("CR_")
    assert "pdf_url" in rep
    assert "csv_url" in rep

    # 2. Retrieve Metadata
    r_meta = requests.get(f"{BASE_URL}/api/climate/reports/{report_id}", timeout=10)
    assert r_meta.status_code == 200
    meta = r_meta.json()
    assert meta["district_id"] == "madurai"
    assert meta["report_id"] == report_id

    # 3. Download PDF and verify binary signature
    r_pdf = requests.get(f"{BASE_URL}/api/climate/reports/{report_id}/download?format=pdf", timeout=10)
    assert r_pdf.status_code == 200
    assert r_pdf.headers["content-type"] == "application/pdf"
    assert r_pdf.content.startswith(b"%PDF"), "Downloaded PDF does not start with valid PDF magic bytes"
    assert len(r_pdf.content) > 10000

    # 4. Download CSV and verify headers
    r_csv = requests.get(f"{BASE_URL}/api/climate/reports/{report_id}/download?format=csv", timeout=10)
    assert r_csv.status_code == 200
    assert "text/csv" in r_csv.headers["content-type"]
    assert "year,mean_temp_celsius" in r_csv.text or "year" in r_csv.text
    assert "madurai" in r_csv.text.lower()


def test_zero_postgresql_dependency():
    """Verify Phase 3 strictly uses embedded SQLite and local storage."""
    from backend.data.database import DB_PATH
    assert os.path.exists(DB_PATH)
    assert not os.getenv("DATABASE_URL", "").startswith("postgres")
