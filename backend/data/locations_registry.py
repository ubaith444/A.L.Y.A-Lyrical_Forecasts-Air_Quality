"""
Tamil Nadu Climate & Forecast Intelligence Platform
Phase 1: Location Registry & Monitoring Stations (Section 1.1)

Explicitly defines the 16 canonical monitoring stations across Tamil Nadu's 4 core regions:
1. Coastal Region: Chennai, Cuddalore, Nagapattinam, Thoothukudi
   Focus: Northeast monsoon, coastal rainfall, humidity, wind and heavy-rain events.
2. Western Region: Coimbatore, Erode, Tiruppur, Nilgiris (Ooty)
   Focus: Elevation effects, temperature differences, rainfall and dry spells.
3. Southern Region: Madurai, Tirunelveli, Kanniyakumari, Ramanathapuram
   Focus: Heat, rainfall variability, dry conditions and coastal influences.
4. Cauvery Delta & Central Region: Thanjavur, Tiruchirappalli, Karur, Salem
   Focus: Agricultural rainfall, seasonal water availability, temperature and rainfall deficits.
"""

from typing import Dict, List, Any

CORE_MONITORING_LOCATIONS: List[Dict[str, Any]] = [
    # 1. Coastal Region (4 Locations)
    {
        "location_id": "CHN_001",
        "name": "Chennai",
        "tamil_name": "சென்னை",
        "region": "Coastal region",
        "latitude": 13.0827,
        "longitude": 80.2707,
        "elevation_m": 7.0,
        "is_coastal": True,
        "is_hill": False,
        "district_id": "chennai",
        "focus_area": "Northeast monsoon, coastal rainfall, humidity, wind and heavy-rain events."
    },
    {
        "location_id": "CDL_003",
        "name": "Cuddalore",
        "tamil_name": "கடலூர்",
        "region": "Coastal region",
        "latitude": 11.7480,
        "longitude": 79.7714,
        "elevation_m": 6.0,
        "is_coastal": True,
        "is_hill": False,
        "district_id": "cuddalore",
        "focus_area": "Cyclonic landfall hotspot, storm surge, coastal rainfall convergence."
    },
    {
        "location_id": "NGP_017",
        "name": "Nagapattinam",
        "tamil_name": "நாகப்பட்டினம்",
        "region": "Coastal region",
        "latitude": 10.7672,
        "longitude": 79.8427,
        "elevation_m": 9.0,
        "is_coastal": True,
        "is_hill": False,
        "district_id": "nagapattinam",
        "focus_area": "Low-lying coastal delta plain, Bay of Bengal depressions, marine winds."
    },
    {
        "location_id": "TUT_016",
        "name": "Thoothukudi",
        "tamil_name": "தூத்துக்குடி",
        "region": "Coastal region",
        "latitude": 8.7642,
        "longitude": 78.1348,
        "elevation_m": 4.0,
        "is_coastal": True,
        "is_hill": False,
        "district_id": "thoothukudi",
        "focus_area": "Gulf of Mannar coastal maritime, post-monsoon cloudbursts, high winds."
    },

    # 2. Western Region (4 Locations)
    {
        "location_id": "CBE_004",
        "name": "Coimbatore",
        "tamil_name": "கோயம்புத்தூர்",
        "region": "Western region",
        "latitude": 11.0168,
        "longitude": 76.9558,
        "elevation_m": 411.0,
        "is_coastal": False,
        "is_hill": False,
        "district_id": "coimbatore",
        "focus_area": "Palakkad Gap wind funneling, western plateau climate, SWM inflow shadow."
    },
    {
        "location_id": "ERD_006",
        "name": "Erode",
        "tamil_name": "ஈரோடு",
        "region": "Western region",
        "latitude": 11.3410,
        "longitude": 77.7172,
        "elevation_m": 183.0,
        "is_coastal": False,
        "is_hill": False,
        "district_id": "erode",
        "focus_area": "Cauvery-Bhavani agricultural basin, temperature extremes and summer heat."
    },
    {
        "location_id": "TPR_005",
        "name": "Tiruppur",
        "tamil_name": "திருப்பூர்",
        "region": "Western region",
        "latitude": 11.1085,
        "longitude": 77.3411,
        "elevation_m": 295.0,
        "is_coastal": False,
        "is_hill": False,
        "district_id": "tiruppur",
        "focus_area": "Semiarid rain shadow, industrial water demands, dry spells."
    },
    {
        "location_id": "OTY_007",
        "name": "Nilgiris (Ooty)",
        "tamil_name": "நீலகிரி (ஊட்டி)",
        "region": "Western region",
        "latitude": 11.4102,
        "longitude": 76.6950,
        "elevation_m": 2240.0,
        "is_coastal": False,
        "is_hill": True,
        "district_id": "nilgiris",
        "focus_area": "High-altitude orographic lift, heavy monsoon bursts, steep temperature lapse."
    },

    # 3. Southern Region (4 Locations)
    {
        "location_id": "MDU_012",
        "name": "Madurai",
        "tamil_name": "மதுரை",
        "region": "Southern region",
        "latitude": 9.9252,
        "longitude": 78.1198,
        "elevation_m": 136.0,
        "is_coastal": False,
        "is_hill": False,
        "district_id": "madurai",
        "focus_area": "Vaigai basin heat spells, rainfall variability, pre-monsoon thunderstorms."
    },
    {
        "location_id": "TNV_013",
        "name": "Tirunelveli",
        "tamil_name": "திருநெல்வேலி",
        "region": "Southern region",
        "latitude": 8.7139,
        "longitude": 77.7567,
        "elevation_m": 47.0,
        "is_coastal": False,
        "is_hill": False,
        "district_id": "tirunelveli",
        "focus_area": "Thamirabarani river basin, dual-monsoon transition, thermal stress."
    },
    {
        "location_id": "KKI_014",
        "name": "Kanniyakumari",
        "tamil_name": "கன்னியாகுமரி",
        "region": "Southern region",
        "latitude": 8.0883,
        "longitude": 77.5385,
        "elevation_m": 19.0,
        "is_coastal": True,
        "is_hill": False,
        "district_id": "kanyakumari",
        "focus_area": "Tri-sea confluence maritime climate, dual-monsoon benefits (SWM + NEM)."
    },
    {
        "location_id": "RMD_015",
        "name": "Ramanathapuram",
        "tamil_name": "இராமநாதபுரம்",
        "region": "Southern region",
        "latitude": 9.3639,
        "longitude": 78.8395,
        "elevation_m": 10.0,
        "is_coastal": True,
        "is_hill": False,
        "district_id": "ramanathapuram",
        "focus_area": "Palk Strait coastline, dry coastal climate, chilli crop water stress."
    },

    # 4. Cauvery Delta & Central Region (4 Locations)
    {
        "location_id": "TNJ_010",
        "name": "Thanjavur",
        "tamil_name": "தஞ்சாவூர்",
        "region": "Cauvery delta and central region",
        "latitude": 10.7870,
        "longitude": 79.1378,
        "elevation_m": 57.0,
        "is_coastal": False,
        "is_hill": False,
        "district_id": "thanjavur",
        "focus_area": "Rice Bowl of Tamil Nadu, Kuruvai/Samba paddy rainfall, Mettur release tracking."
    },
    {
        "location_id": "TRY_009",
        "name": "Tiruchirappalli",
        "tamil_name": "திருச்சிராப்பள்ளி",
        "region": "Cauvery delta and central region",
        "latitude": 10.7905,
        "longitude": 78.7047,
        "elevation_m": 85.0,
        "is_coastal": False,
        "is_hill": False,
        "district_id": "tiruchirappalli",
        "focus_area": "Geographical apex of Cauvery Delta, acute summer heat, moderate NEM."
    },
    {
        "location_id": "KRR_011",
        "name": "Karur",
        "tamil_name": "கரூர்",
        "region": "Cauvery delta and central region",
        "latitude": 10.9601,
        "longitude": 78.0766,
        "elevation_m": 122.0,
        "is_coastal": False,
        "is_hill": False,
        "district_id": "karur",
        "focus_area": "Amaravathi confluence, interior dry plain, high temperature anomalies."
    },
    {
        "location_id": "SLM_018",
        "name": "Salem",
        "tamil_name": "சேலம்",
        "region": "Cauvery delta and central region",
        "latitude": 11.6643,
        "longitude": 78.1460,
        "elevation_m": 278.0,
        "is_coastal": False,
        "is_hill": False,
        "district_id": "salem",
        "focus_area": "Shevaroy foothill basin, Mettur Stanley reservoir catchment, pre-monsoon rain."
    }
]

LOCATIONS_BY_ID: Dict[str, Dict[str, Any]] = {loc["location_id"]: loc for loc in CORE_MONITORING_LOCATIONS}
LOCATIONS_BY_DISTRICT_ID: Dict[str, Dict[str, Any]] = {loc["district_id"]: loc for loc in CORE_MONITORING_LOCATIONS}
