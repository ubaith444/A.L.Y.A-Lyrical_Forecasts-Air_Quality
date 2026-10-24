from typing import Any
from fastapi import APIRouter, Query
from pydantic import BaseModel, Field

from app.services.advanced_ai_ml import (
    PIMLEngine,
    DownscalingEngine,
    DataAssimilationEngine,
    AutoregressiveCorrectionEngine,
    EarthSystemEmulator,
    ProbabilisticEngine,
    NaturalLanguageWeatherIntelligence,
    IndiaMultimodalLearningEngine,
    AirQualityIntelligenceEngine,
    ForecastingHorizonStrategyEngine,
    ModelEvaluationAndDriftEngine,
)

router = APIRouter()


class NLPQueryRequest(BaseModel):
    query: str = Field(..., description="Natural language question about weather, risk, or climate")
    location_id: str = Field(default="chennai", description="Target location ID")
    current_temp: float = Field(default=31.5, description="Current ambient temperature in °C")
    daily_rain_mm: float = Field(default=18.4, description="24h accumulated rainfall in mm")
    max_rain_prob: int = Field(default=68, description="Maximum rainfall probability in %")


@router.get("/piml-comparison")
def get_piml_comparison(
    temperature_c: float = Query(31.5, description="Forecast temperature in °C"),
    relative_humidity_pct: float = Query(78.0, description="Forecast relative humidity in %"),
    surface_pressure_hpa: float = Query(1008.4, description="Forecast surface pressure in hPa"),
    elevation_m: float = Query(12.0, description="Ground elevation in meters"),
    wind_speed_kmh: float = Query(14.2, description="Wind speed in km/h"),
) -> dict[str, Any]:
    """Evaluates Physics-Informed ML (PIML) versus Pure ML baseline with conservation loss."""
    comparison = PIMLEngine.compare_pure_ml_vs_piml(
        base_temp=temperature_c,
        base_humidity=relative_humidity_pct,
        elevation_m=elevation_m,
    )
    consistency = PIMLEngine.evaluate_physical_consistency(
        temperature_c=temperature_c,
        relative_humidity_pct=relative_humidity_pct,
        surface_pressure_hpa=surface_pressure_hpa,
        elevation_m=elevation_m,
        wind_speed_kmh=wind_speed_kmh,
    )
    return {
        **comparison,
        "consistency_evaluation": consistency,
    }


@router.get("/downscaling")
def get_downscaled_grid(
    coarse_temp: float = Query(32.0, description="Coarse NWP temperature in °C"),
    coarse_precip: float = Query(8.5, description="Coarse NWP precipitation in mm"),
    base_elevation_m: float = Query(10.0, description="Coarse grid cell average elevation in m"),
    target_elevation_m: float = Query(380.0, description="Fine-scale local elevation in m"),
    distance_to_coast_km: float = Query(18.0, description="Distance to coastline in km"),
    land_use: str = Query("urban", description="Local land-use type (urban, dense_forest, water_body, rural)"),
) -> dict[str, Any]:
    """High-resolution statistical downscaling translating coarse ~25 km NWP to ~1 km fine topographic grid."""
    return DownscalingEngine.downscale_grid(
        coarse_temp=coarse_temp,
        coarse_precip=coarse_precip,
        base_elevation_m=base_elevation_m,
        target_elevation_m=target_elevation_m,
        distance_to_coast_km=distance_to_coast_km,
        land_use=land_use,
    )


@router.get("/data-assimilation")
def get_multimodal_assimilation(
    latitude: float = Query(13.0827, description="Target latitude"),
    longitude: float = Query(80.2707, description="Target longitude"),
    nwp_temp: float = Query(31.5, description="Background NWP temperature in °C"),
    nwp_rh: float = Query(76.0, description="Background NWP relative humidity in %"),
    nwp_precip: float = Query(12.0, description="Background NWP precipitation in mm"),
) -> dict[str, Any]:
    """India-focused multimodal data assimilation fusing satellite, ground AWS, radar, and reanalysis."""
    return DataAssimilationEngine.get_multimodal_state(
        latitude=latitude,
        longitude=longitude,
        nwp_temp=nwp_temp,
        nwp_rh=nwp_rh,
        nwp_precip=nwp_precip,
    )


@router.get("/autoregressive-correction")
def get_autoregressive_correction(
    location_id: str = Query("chennai", description="Station or district identifier"),
    lead_time_hours: int = Query(24, description="Forecast horizon lead time (1-72h)"),
    raw_forecast_temp: float = Query(33.2, description="Raw uncorrected NWP temperature in °C"),
    raw_forecast_precip: float = Query(24.5, description="Raw uncorrected NWP rainfall in mm"),
    season: str = Query("monsoon", description="Current season regime (monsoon, pre_monsoon, post_monsoon, winter)"),
) -> dict[str, Any]:
    """Self-supervised autoregressive error correction based on historical forecast-observation residuals."""
    return AutoregressiveCorrectionEngine.compute_residual_correction(
        raw_forecast_temp=raw_forecast_temp,
        raw_forecast_rain=raw_forecast_precip,
        lead_time_hours=lead_time_hours,
        season=season,
    )


@router.get("/earth-system")
def get_coupled_earth_system(
    surface_temp: float = Query(32.0, description="Surface temperature in °C"),
    daily_precip: float = Query(15.0, description="Daily precipitation in mm"),
    surface_wind_kmh: float = Query(14.0, description="Surface wind speed in km/h"),
    distance_to_ocean_km: float = Query(8.0, description="Distance to ocean in km"),
) -> dict[str, Any]:
    """Coupled Earth System Emulation approximating Atmosphere-Land-Hydrology-Ocean-AQI interactions."""
    return EarthSystemEmulator.emulate_couplings(
        atmosphere_temp=surface_temp,
        rainfall_24h_mm=daily_precip,
        wind_speed_kmh=surface_wind_kmh,
        coastal_proximity_km=distance_to_ocean_km,
    )


@router.get("/probabilistic")
def get_probabilistic_forecast(
    deterministic_temp: float = Query(32.2, description="Deterministic temperature in °C"),
    deterministic_rain: float = Query(14.5, description="Deterministic precipitation in mm"),
) -> dict[str, Any]:
    """Probabilistic forecasting with exceedance curves, prediction intervals, and reliability calibration."""
    return ProbabilisticEngine.compute_probabilistic_outlook(
        deterministic_temp=deterministic_temp,
        deterministic_rain=deterministic_rain,
    )


@router.post("/nlp-query")
def answer_nlp_weather_query(body: NLPQueryRequest) -> dict[str, Any]:
    """Answers natural-language weather intelligence queries grounded in actual forecast and observation data."""
    return NaturalLanguageWeatherIntelligence.answer_query(
        query=body.query,
        location_id=body.location_id,
        current_temp=body.current_temp,
        daily_rain_mm=body.daily_rain_mm,
        max_rain_prob=body.max_rain_prob,
    )


@router.get("/data-sources-matrix")
def get_data_sources_matrix() -> dict[str, Any]:
    """Multisource data fusion taxonomy distinguishing observations, forecasts, and reanalyses."""
    return {
        "status": "active",
        "taxonomy_note": (
            "The platform rigorously distinguishes direct observations from numerical forecasts and historical reanalyses. "
            "Reanalysis datasets (ERA5-Land) represent physics-constrained data assimilations, not direct in-situ thermometer readings."
        ),
        "data_sources": [
            {
                "source_name": "Open-Meteo Weather APIs",
                "purpose": "Baseline multi-model numerical weather prediction (ECMWF, GFS, ICON) and hourly historical weather access",
                "kind": "NWP Forecast & Reanalysis",
                "spatial_resolution": "0.1° to 0.25° (~11–25 km)",
                "update_frequency": "Hourly / 4x Daily",
                "licensing_and_access": "Open-access with CC-BY 4.0 attribution",
            },
            {
                "source_name": "India Meteorological Department (IMD)",
                "purpose": "Official statutory Indian forecasts, nowcasts, color-coded cyclone/flood warnings, and eligible AWS observations",
                "kind": "Official Statutory Observation & Warning",
                "spatial_resolution": "District and subdivision level / Point AWS",
                "update_frequency": "3-Hourly to Real-Time bulletins",
                "licensing_and_access": "Government of India Open Data License / National Meteorological Service mandates",
            },
            {
                "source_name": "ISRO Satellite Products (MOSDAC / INSAT-3D & 3DR)",
                "purpose": "Geostationary cloud motion vectors, hydro-estimator precipitation, and atmospheric sounder vertical profiles",
                "kind": "Direct Satellite Remote Sensing",
                "spatial_resolution": "4 km (thermal) / 1 km (visible)",
                "update_frequency": "Every 15–30 minutes",
                "licensing_and_access": "ISRO MOSDAC Public Meteorological Portal",
            },
            {
                "source_name": "ERA5 & ERA5-Land (ECMWF / Copernicus CDS)",
                "purpose": "Historical atmospheric and high-resolution land-surface reanalysis for 30-year climatological baselines",
                "kind": "Historical Reanalysis Baseline",
                "spatial_resolution": "0.1° (~9 km) for ERA5-Land",
                "update_frequency": "Hourly historical archive (1950–Present)",
                "licensing_and_access": "Copernicus Climate Change Service License (Free open access)",
            },
            {
                "source_name": "NASA POWER Agroclimatology & Solar",
                "purpose": "Complementary top-of-atmosphere and surface solar radiation, photosynthetic active radiation, and surface flux validation",
                "kind": "Satellite & Assimilated Solar Meteorology",
                "spatial_resolution": "0.5° (~50 km)",
                "update_frequency": "Daily / Hourly update cycles",
                "licensing_and_access": "NASA Open Science Data (Public Domain)",
            },
            {
                "source_name": "Available Weather Stations & Rain Gauges (AWS/ARG)",
                "purpose": "In-situ ground truth validation for downscaled micro-grids and autoregressive error residual modeling",
                "kind": "In-Situ Direct Ground Truth",
                "spatial_resolution": "Point location (latitude/longitude coordinates)",
                "update_frequency": "15-minute to Hourly intervals",
                "licensing_and_access": "State Disaster Management / Research Network feeds",
            },
            {
                "source_name": "SRTM Digital Elevation Model & Copernicus Land Cover",
                "purpose": "Orography gradients for Western/Eastern Ghats elevation lapse rates, aspect angle, and land-use microclimates",
                "kind": "Geospatial Surface Topography",
                "spatial_resolution": "30m to 100m fine grid",
                "update_frequency": "Static / Periodic decadal updates",
                "licensing_and_access": "NASA JPL / ESA Copernicus Open Access",
            },
        ],
    }


@router.get("/regional-multimodal")
def get_regional_multimodal_profile(
    region_id: str = Query("tamil_nadu_coast", description="Target region: tamil_nadu_coast, western_ghats_orography, cauvery_delta"),
) -> dict[str, Any]:
    """Module D: Direct India-Focused Multimodal Learning with Spatiotemporal Transformers."""
    return IndiaMultimodalLearningEngine.get_regional_spatiotemporal_profile(region_id=region_id)


@router.get("/air-quality-intelligence")
def get_air_quality_intelligence(
    surface_wind_kmh: float = Query(12.0, description="Surface wind speed in km/h"),
    surface_temp_c: float = Query(30.0, description="Surface temperature in °C"),
    relative_humidity_pct: float = Query(72.0, description="Relative humidity in %"),
    base_pm25: float = Query(38.0, description="Background PM2.5 in ug/m3"),
    base_pm10: float = Query(74.0, description="Background PM10 in ug/m3"),
) -> dict[str, Any]:
    """Module J: Air Quality Intelligence with Planetary Boundary Layer Ventilation and CPCB NAQI."""
    return AirQualityIntelligenceEngine.evaluate_air_quality_forecast(
        surface_wind_kmh=surface_wind_kmh,
        surface_temp_c=surface_temp_c,
        relative_humidity_pct=relative_humidity_pct,
        base_pm25=base_pm25,
        base_pm10=base_pm10,
    )


@router.get("/horizon-strategy")
def get_horizon_strategy_matrix() -> dict[str, Any]:
    """Section 3: Forecasting Model Strategy by Operational Horizon (0-6h, 6-72h, 3-14d, Seasonal)."""
    return ForecastingHorizonStrategyEngine.get_strategy_matrix()


@router.get("/model-evaluation-drift")
def get_model_evaluation_and_drift(
    location_id: str = Query("chennai", description="Station or district identifier"),
) -> dict[str, Any]:
    """Section 5: Chronological Rolling-Origin Backtesting, Baseline Comparisons, and Drift Monitoring."""
    return ModelEvaluationAndDriftEngine.get_evaluation_and_drift_report(location_id=location_id)


@router.get("/architecture-layers")
def get_architecture_layers() -> dict[str, Any]:
    """Section 1: 5-Layer AI/ML End-to-End Pipeline Architecture."""
    return {
        "layers": [
            {
                "layer_number": 1,
                "layer_name": "Multimodal Data Ingestion",
                "components": [
                    "Open-Meteo Multi-NWP Gateway (ECMWF IFS, GFS, ICON)",
                    "ERA5 & ERA5-Land Reanalysis Hourly Archive",
                    "NASA POWER Surface Meteorology & Solar Radiation",
                    "IMD Official AWS Telemetry & Rain Gauges",
                    "ISRO MOSDAC Satellite Products (INSAT-3D/3DR TIR)",
                ],
                "protocols": "Async HTTPX, Parquet Ingestion Queue, UTC Timestamp Normalization",
            },
            {
                "layer_number": 2,
                "layer_name": "Data Quality & Fusion Engine",
                "components": [
                    "Dual-Pass Range and Climatological Outlier Detection",
                    "Spatial Grid Alignment to 0.01° Micro-Grid Topography",
                    "Temporal Alignment to 15-Minute Synoptic Epochs",
                    "3D-Var Optimal Interpolation with Error Covariance Matrices",
                    "Source Provenance, Freshness Telemetry, and Cryptographic Checksums",
                ],
                "protocols": "Observation-Aware Bias Correction, Variance Reduction",
            },
            {
                "layer_number": 3,
                "layer_name": "Advanced AI/ML Model Layer",
                "components": [
                    "Module B: Physics-Informed ML (Clausius-Clapeyron, Hydrostatic PINN)",
                    "Module C: High-Resolution 1 km Downscaling (SRTM Orography & Sea-Breeze)",
                    "Module D: Direct India-Focused Spatiotemporal Learning (ConvLSTM & GNN)",
                    "Module E: Self-Supervised Autoregressive Error Correction (AR Residuals)",
                    "Module F: Coupled Earth-System Emulation (Atmosphere-Land-Ocean-AQI)",
                    "Module G: Probabilistic Quantile Forecasting (Exceedance Curves)",
                ],
                "protocols": "PyTorch / Scikit-Learn Hybrid Physical-ML Surrogate",
            },
            {
                "layer_number": 4,
                "layer_name": "Forecast Verification & Uncertainty",
                "components": [
                    "Chronological Rolling-Origin Backtesting (Zero Temporal Leakage)",
                    "Continuous Verification Metrics: MAE, RMSE, Pearson Correlation",
                    "Event Classification Verification: Brier Score, Precision-Recall AUC",
                    "Probabilistic Reliability Diagrams & Prediction Interval Coverage",
                    "Automated In-Situ Sensor Drift and Telemetry Latency Alarms",
                ],
                "protocols": "Three-Way Baseline Benchmarks (Persistence, Climatology, Provider NWP)",
            },
            {
                "layer_number": 5,
                "layer_name": "Intelligence & Decision Layer",
                "components": [
                    "Module H: Extreme-Event Early Warning (Heatwaves, Heavy Rain, Severe Wind)",
                    "Module I: Explainable AI & Natural-Language Intelligence (SHAP Drivers)",
                    "Module J: Air Quality Intelligence (CPCB NAQI & Inversion Trapping)",
                    "Interactive Geographic Multi-Layer Map (India -> State -> District)",
                    "Strict Statutory Warning Separation (AI Risk vs Government Alerts)",
                ],
                "protocols": "LLM Explanatory Synthesis grounded in verified observation data",
            },
        ],
    }
