"""
Tamil Nadu Climate & Forecast Intelligence Platform
Phase 5: Bilingual Risk Summaries (English & Tamil)

Provides deterministic, template-based meteorological risk summaries
in both English and Tamil (தமிழ்), adhering to verified safety guidelines.
Preserves exact values, units, timestamps, and sources across both languages.
"""

from typing import Dict, Any, Tuple
from backend.data.districts_data import TAMIL_NADU_DISTRICTS

# Standardized bilingual vocabulary for meteorological hazards
HAZARD_TRANSLATIONS = {
    "rainfall": {"en": "Heavy Rainfall Risk", "ta": "கனமழை ஆபத்து"},
    "heat": {"en": "Extreme Heat Risk", "ta": "தீவிர வெப்ப ஆபத்து"},
    "wind": {"en": "High Wind & Squall Risk", "ta": "பலத்த காற்று மற்றும் சூறாவளி ஆபத்து"},
    "dry_spell": {"en": "Prolonged Dry Spell Risk", "ta": "தொடர் வறட்சி நிலை ஆபத்து"},
    "compound": {"en": "Compound Weather Risk", "ta": "கூட்டு வானிலை ஆபத்து"}
}

SEVERITY_TRANSLATIONS = {
    "Low": {"en": "Low", "ta": "குறைவு"},
    "Moderate": {"en": "Moderate", "ta": "மிதமான"},
    "High": {"en": "High", "ta": "அதிக"},
    "Severe": {"en": "Severe", "ta": "தீவிர"}
}


def generate_bilingual_risk_summary(
    district_id: str,
    hazard_type: str,
    severity: str,
    trigger_value: float,
    threshold_value: float,
    unit: str,
    forecast_period: str = "Next 24 Hours",
    data_source: str = "Open-Meteo & IMD Numerical Ensemble",
    updated_at: str = "Live"
) -> Dict[str, Any]:
    """
    Generates deterministic, mathematically consistent risk summaries in English and Tamil.
    """
    dist_info = TAMIL_NADU_DISTRICTS.get(district_id.lower(), {})
    dist_name_en = dist_info.get("name", district_id.capitalize())
    dist_name_ta = dist_info.get("tamil_name", dist_name_en)

    hazard_en = HAZARD_TRANSLATIONS.get(hazard_type, {"en": hazard_type.capitalize(), "ta": hazard_type})["en"]
    hazard_ta = HAZARD_TRANSLATIONS.get(hazard_type, {"en": hazard_type.capitalize(), "ta": hazard_type})["ta"]

    sev_en = SEVERITY_TRANSLATIONS.get(severity, {"en": severity, "ta": severity})["en"]
    sev_ta = SEVERITY_TRANSLATIONS.get(severity, {"en": severity, "ta": severity})["ta"]

    # Construct Hazard-Specific Narratives & Precautions
    if hazard_type == "rainfall":
        if severity == "Severe":
            desc_en = f"Extremely heavy rainfall of {trigger_value:.1f} {unit} is forecast across {dist_name_en} (Threshold: >{threshold_value:.1f} {unit}). Widespread waterlogging and flash inundation are probable in low-lying zones."
            desc_ta = f"{dist_name_ta} மாவட்டத்தில் {trigger_value:.1f} {unit} தீவிர கனமழை பெய்யக்கூடும் என முன்னறிவிப்பு தெரிவிக்கிறது (வரம்பு: >{threshold_value:.1f} {unit}). தாழ்வான பகுதிகளில் கடுமையான வெள்ளப்பெருக்கு மற்றும் நீர் தேங்குதல் ஏற்பட வாய்ப்புள்ளது."
            rec_en = "Avoid all non-essential travel. Stay away from stormwater drains, electrical installations, and inundated causeways. Fishermen must suspend marine operations."
            rec_ta = "அத்தியாவசியமற்ற பயணங்களைத் தவிர்க்கவும். மழைநீர் வடிகால்கள், மின்சார சாதனங்கள் மற்றும் வெள்ளம் பெருக்கெடுக்கும் தரைப்பாலங்களிலிருந்து விலகி இருக்கவும். மீனவர்கள் கடலுக்குச் செல்வதை உடனடியாக நிறுத்த வேண்டும்."
        elif severity == "High":
            desc_en = f"Heavy rainfall of {trigger_value:.1f} {unit} is forecast in {dist_name_en} during {forecast_period} (Threshold: >{threshold_value:.1f} {unit}). Localized surface flooding and traffic congestion expected."
            desc_ta = f"{dist_name_ta} மாவட்டத்தில் {forecast_period} காலப்பகுதியில் {trigger_value:.1f} {unit} கனமழை எதிர்பார்க்கப்படுகிறது (வரம்பு: >{threshold_value:.1f} {unit}). உள்ளூர் பகுதிகளில் நீர் தேங்குதல் மற்றும் போக்குவரத்து பாதிப்புகள் ஏற்படலாம்."
            rec_en = "Ensure agricultural field drainage channels are clear. Keep battery devices charged and monitor official regional forecasts."
            rec_ta = "விவசாய நிலங்களில் முறையான வடிகால் வசதிகளை உறுதி செய்யவும். மின்கல சாதனங்களை மின்னூட்டம் செய்து வைத்துக் கொள்ளவும் மற்றும் அதிகாரப்பூர்வ வானிலை அறிவிப்புகளைப் பின்பற்றவும்."
        elif severity == "Moderate":
            desc_en = f"Moderate precipitation of {trigger_value:.1f} {unit} is anticipated in {dist_name_en}. Standard localized showers with manageable runoff."
            desc_ta = f"{dist_name_ta} மாவட்டத்தில் {trigger_value:.1f} {unit} மிதமான மழை பெய்யக்கூடும். பொதுவான உள்ளூர் மழைப்பொழிவு இயல்பாகக் காணப்படும்."
            rec_en = "Exercise standard road safety caution during sudden cloudbursts."
            rec_ta = "திடீர் மழையின் போது சாலைப் பாதுகாப்பைக் கடைப்பிடிக்கவும்."
        else:
            desc_en = f"Light rainfall of {trigger_value:.1f} {unit} expected in {dist_name_en}. Conditions remain within benign seasonal bounds."
            desc_ta = f"{dist_name_ta} மாவட்டத்தில் {trigger_value:.1f} {unit} லேசான மழை பெய்யக்கூடும். வானிலை இயல்பு வரம்பிற்குள் உள்ளது."
            rec_en = "No special precautions required."
            rec_ta = "குறிப்பிட்ட முன்னெச்சரிக்கை நடவடிக்கைகள் எதுவும் தேவையில்லை."

    elif hazard_type == "heat":
        if severity in ["Severe", "High"]:
            desc_en = f"Elevated thermal stress with Heat Index reaching {trigger_value:.1f} {unit} across {dist_name_en} (Threshold: >{threshold_value:.1f} {unit}). Severe risk of heat exhaustion and cramps."
            desc_ta = f"{dist_name_ta} மாவட்டத்தில் வெப்பச் சுட்டெண் {trigger_value:.1f} {unit} ஆக உயர்ந்து தீவிர வெப்ப அழுத்தம் ஏற்படக்கூடும் (வரம்பு: >{threshold_value:.1f} {unit}). உடல் சோர்வு மற்றும் வெப்ப பக்கவாதம் ஏற்பட அதிக வாய்ப்புள்ளது."
            rec_en = "Stay adequately hydrated with water and oral electrolytes. Refrain from direct sun exposure between 11:30 AM and 03:30 PM. Provide shade and water for cattle."
            rec_ta = "போதுமான அளவு தண்ணீர் மற்றும் எலக்ட்ரோலைட் திரவங்களை அருந்தவும். முற்பகல் 11:30 முதல் பிற்பகல் 03:30 வரை நேரடி வெயிலில் செல்வதைத் தவிர்க்கவும். கால்நடைகளுக்கு நிழல் மற்றும் குடிநீர் வசதி செய்யவும்."
        else:
            desc_en = f"Moderate thermal conditions ({trigger_value:.1f} {unit}) in {dist_name_en}. Seasonal warmth expected."
            desc_ta = f"{dist_name_ta} மாவட்டத்தில் மிதமான வெப்ப நிலை ({trigger_value:.1f} {unit}) நிலவுகிறது. பருவகாலத்திற்குரிய வெப்பம் நிலவும்."
            rec_en = "Maintain adequate daily hydration during afternoon hours."
            rec_ta = "மதிய வேளையில் போதுமான அளவு தண்ணீர் குடிக்கவும்."

    elif hazard_type == "wind":
        if severity in ["Severe", "High"]:
            desc_en = f"Squally wind gusts up to {trigger_value:.1f} {unit} forecast for {dist_name_en} (Threshold: >{threshold_value:.1f} {unit}). Potential for loose roofing detachment and tree branch snapping."
            desc_ta = f"{dist_name_ta} மாவட்டத்தில் மணிக்கு {trigger_value:.1f} {unit} வேகத்தில் பலத்த காற்று வீசக்கூடும் என எதிர்பார்க்கப்படுகிறது (வரம்பு: >{threshold_value:.1f} {unit}). கூரைகள் மற்றும் மரக்கிளைகள் முறிந்து விழும் அபாயம் உள்ளது."
            rec_en = "Secure outdoor banners, roofing sheets, and lightweight structures. Mariners should avoid nearshore transit."
            rec_ta = "வெளியில் உள்ள விளம்பரப் பலகைகள் மற்றும் தற்காலிக கூரைகளைப் பத்திரப்படுத்தவும். மீனவர்கள் கடலோரப் பயணங்களைத் தவிர்க்கவும்."
        else:
            desc_en = f"Moderate wind speed of {trigger_value:.1f} {unit} across {dist_name_en}."
            desc_ta = f"{dist_name_ta} மாவட்டத்தில் மணிக்கு {trigger_value:.1f} {unit} வேகத்தில் மிதமான காற்று வீசுகிறது."
            rec_en = "Normal weather activity."
            rec_ta = "இயல்பான வானிலை நடவடிக்கைகள்."

    elif hazard_type == "dry_spell":
        if severity in ["Severe", "High"]:
            desc_en = f"Prolonged dry spell of {int(trigger_value)} consecutive dry days detected in {dist_name_en} (Threshold: >{int(threshold_value)} days). Soil moisture depletion threatens standing crops."
            desc_ta = f"{dist_name_ta} மாவட்டத்தில் தொடர்ந்து {int(trigger_value)} நாட்களாக மழை இல்லாத தொடர் வறட்சி நிலை நிலவுகிறது (வரம்பு: >{int(threshold_value)} நாட்கள்). மண் ஈரப்பதம் குறைந்து பயிர்கள் வாட வாய்ப்புள்ளது."
            rec_en = "Adopt micro-irrigation (drip/sprinkler) scheduling during night hours. Apply organic mulch to conserve residual root-zone moisture."
            rec_ta = "இரவு நேரங்களில் சொட்டு நீர் பாசனம் மேற்கொள்ளவும். மண் ஈரப்பதத்தைப் பாதுகாக்க பயிர்களுக்கு இடையே மூடாக்கு இடுவதை உறுதி செய்யவும்."
        else:
            desc_en = f"{int(trigger_value)} dry days in {dist_name_en}. Soil moisture reserves currently adequate."
            desc_ta = f"{dist_name_ta} மாவட்டத்தில் {int(trigger_value)} நாட்கள் உலர் நிலை. தற்போது போதுமான மண் ஈரப்பதம் உள்ளது."
            rec_en = "Monitor soil moisture regularly."
            rec_ta = "மண்ணின் ஈரப்பதத்தைத் தொடர்ந்து கண்காணிக்கவும்."

    else:  # Compound risk
        desc_en = f"Multiple intersecting hazard triggers detected in {dist_name_en}: elevated thermal gradient compounded by atmospheric dry spell."
        desc_ta = f"{dist_name_ta} மாவட்டத்தில் பல வானிலை காரணிகள் இணைந்து கூட்டு வானிலை ஆபத்தை ஏற்படுத்துகின்றன."
        rec_en = "Follow multi-hazard disaster management cell advisories."
        rec_ta = "பேரிடர் மேலாண்மைத் துறையின் பலதரப்பட்ட பாதுகாப்பு வழிகாட்டுதல்களைப் பின்பற்றவும்."

    return {
        "district_id": district_id.lower(),
        "district_name": {"en": dist_name_en, "ta": dist_name_ta},
        "hazard_type": hazard_type,
        "hazard_name": {"en": hazard_en, "ta": hazard_ta},
        "severity": {"en": sev_en, "ta": sev_ta},
        "trigger_value": trigger_value,
        "threshold_value": threshold_value,
        "unit": unit,
        "forecast_period": forecast_period,
        "data_source": data_source,
        "updated_at": updated_at,
        "summary": {
            "en": {
                "headline": f"{sev_en} {hazard_en} — {dist_name_en}",
                "description": desc_en,
                "precautions": rec_en
            },
            "ta": {
                "headline": f"{sev_ta} {hazard_ta} — {dist_name_ta}",
                "description": desc_ta,
                "precautions": rec_ta
            }
        }
    }
