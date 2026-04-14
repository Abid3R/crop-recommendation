# ================================================================
# CropSense BD - Crop & Fertilizer Recommendation System
# streamlit run app.py
# ================================================================
import streamlit as st
import pandas as pd
import numpy as np
import joblib
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from fertilizer_lookup import load_field_df, load_fruit_df, get_fertilizer, is_fruit_tree

st.set_page_config(page_title="CropSense BD", page_icon="🌾", layout="wide")

st.markdown("""
<style>
html, body, [class*="css"] {
    font-family: 'Segoe UI', Arial, sans-serif;
    color: #1a1a1a;
}
.stApp { background: #f5f0e8; }
#MainMenu, footer, header { visibility: hidden; }
[data-testid="collapsedControl"] {
    display:block !important; visibility:visible !important;
}
.main-title {
    font-family: Georgia, serif; font-size: 46px; font-weight: 900;
    color: #2c1a0e; line-height: 1; letter-spacing: -1px; margin-bottom: 4px;
}
.main-title em { color: #3d6b35; font-style: italic; }
.subtitle {
    font-size: 11px; letter-spacing: 2px; text-transform: uppercase;
    color: #8a7060; margin-bottom: 20px;
}
.sec {
    font-size: 11px; font-weight: 700; letter-spacing: 2px;
    text-transform: uppercase; color: #7a4a2a;
    border-bottom: 2px solid rgba(74,44,23,0.15);
    padding-bottom: 6px; margin: 16px 0 8px;
}
.info-box {
    background:#edf4eb; border-left:4px solid #3d6b35;
    padding:12px 16px; border-radius:0 4px 4px 0;
    font-size:13px; color:#1a1a1a !important;
    margin: 16px 0;
}
.stButton > button {
    width:100%; background:#2c1a0e !important; color:#e8b84b !important;
    border:none !important; border-radius:4px !important;
    font-weight:700 !important; letter-spacing:2px !important;
    text-transform:uppercase !important; padding:16px !important;
    font-size:13px !important;
}
.stButton > button:hover { background:#3d6b35 !important; }
.stSelectbox label, .stNumberInput label {
    color:#1a1a1a !important; font-weight:600 !important; font-size:13px !important;
}
input { color:#1a1a1a !important; }
[data-testid="stMetricValue"] { color:#2c1a0e !important; font-weight:700 !important; }
[data-testid="stMetricLabel"] { color:#6a5040 !important; }

/* ===== FERTILIZER RECOMMENDATION TEXT FIXES ===== */
/* Force dark text inside expanders (where fertilizer details live) */
.stExpander p, .stExpander div, .stExpander span,
.stMarkdown, .stWrite, .stCaption {
    color: #1a1a1a !important;
}
/* Make captions darker (default light gray is hard to read) */
.stCaption {
    color: #2c2c2c !important;
    font-weight: 500;
}
/* Ensure info boxes (st.info) inside expanders have readable text */
.stAlert div, .stAlert p {
    color: #1a1a1a !important;
}
/* Fertilizer nutrient lines (written with st.write) */
.stWrite p, .stMarkdown p {
    color: #1a1a1a !important;
}
/* Override any light text in metric area that might affect fertilizer block */
[data-testid="stMetricValue"] {
    color: #2c1a0e !important;
}
</style>
""", unsafe_allow_html=True)

# ── Constants ─────────────────────────────────────────────────────
AEZ_MAP = {
    'Barisal':13,'Bogra':4,'Chittagonj':23,'Cumilla':18,
    'Dhaka':9,'Dinajpur':1,'Faridpur':11,'Jashore':11,
    'Khulna':12,'Mymensingh':8,'Rajshahi':11,
    'Rangamati':24,'Rangpur':3,'Sylhet':21,
}
AEZ_NAMES = {
    1:'Old Himalayan Piedmont Plain', 3:'Tista Meander Floodplain',
    4:'Karatoya-Bangali Floodplain',  8:'Young Brahmaputra Floodplain',
    9:'Old Brahmaputra Floodplain',  11:'High Ganges River Floodplain',
   12:'Low Ganges River Floodplain', 13:'Ganges Tidal Floodplain',
   18:'Meghna Floodplain',           21:'Sylhet Basin',
   23:'Chittagong Coastal Plain',    24:'Chittagong Hill Tracts',
}
MONTHS   = ['January','February','March','April','May','June',
            'July','August','September','October','November','December']
DISTRICTS = sorted(AEZ_MAP.keys())

CROP_EMOJI = {
    'Aman':'🌾','Boro':'🌾','Aush':'🌾','Wheat':'🌿','jute':'🪢',
    'Sugarcane':'🎋','Potato':'🥔','Tomato':'🍅','Banana':'🍌',
    'Mango':'🥭','Guava':'🍈','pineapple':'🍍','jackfruit':'🫐',
    'papaya':'🍈','licchi':'🍒','Soybean':'🫘','Red Lentil':'🫘',
    'corn khorip-1':'🌽','Corn(Robi)':'🌽','garlic':'🧄',
    'indian jujube':'🍈','Tula':'☁️','masterd seed':'🌱',
}
def get_emoji(c):
    for k,v in CROP_EMOJI.items():
        if k.lower() in c.lower(): return v
    return '🌱'

# Friendly nutrient names
NUTRIENT_LABELS = {
    'N (kg/ha)':               '🌿 Nitrogen (N)',
    'P (kg/ha)':               '🪨 Phosphorus (P)',
    'K (kg/ha)':               '🌱 Potassium (K)',
    'S (kg/ha)':               '🟡 Sulphur (S)',
    'Zn (kg/ha)':              '⚪ Zinc (Zn)',
    'B (kg/ha)':               '🔵 Boron (B)',
    'Mg (kg/ha)':              '⚫ Magnesium (Mg)',
    'Organic Matter (t/ha)':   '♻️ Organic Compost',
    'N (g/tree)':              '🌿 Nitrogen (N)',
    'P (g/tree)':              '🪨 Phosphorus (P)',
    'K (g/tree)':              '🌱 Potassium (K)',
    'S (g/tree)':              '🟡 Sulphur (S)',
    'Zn (g/tree)':             '⚪ Zinc (Zn)',
    'B (g/tree)':              '🔵 Boron (B)',
    'Organic Matter (kg/tree)':'♻️ Organic Compost',
}

# ── Load model ────────────────────────────────────────────────────
@st.cache_resource
def load_all():
    paths = [
        os.path.dirname(os.path.abspath(__file__)),
        '/mount/src/crop-recommendation', '.',
    ]
    base = next((p for p in paths
                 if os.path.exists(os.path.join(p,'crop_model.pkl'))), '.')
    model    = joblib.load(os.path.join(base,'crop_model.pkl'))
    encoder  = joblib.load(os.path.join(base,'label_encoder.pkl'))
    features = joblib.load(os.path.join(base,'feature_names.pkl'))
    field_df = load_field_df(os.path.join(base,'field_crops_fertilizer.csv'))
    fruit_df = load_fruit_df(os.path.join(base,'fruit_trees_fertilizer.csv'))
    return model, encoder, features, field_df, fruit_df

try:
    model, encoder, features, field_df, fruit_df = load_all()
except Exception as e:
    st.error(f"⚠️ Could not load model: {e}")
    st.stop()

# ── Header ────────────────────────────────────────────────────────
st.markdown('<div class="main-title">🌾 CropSense <em>BD</em></div>',
            unsafe_allow_html=True)
st.markdown('<div class="subtitle">AI Crop & Fertilizer Recommendation · Bangladesh · BARC FRG-2024</div>',
            unsafe_allow_html=True)

c1,c2,c3,c4 = st.columns(4)
with c1: st.metric("Best Model", "XGBoost")
with c2: st.metric("Accuracy",   "79.25%")
with c3: st.metric("Crops",      "41")
with c4: st.metric("Districts",  "14")

st.markdown('<div class="info-box">🌱 Select your district and month, enter current weather conditions, then click <b>Get Recommendations</b>.</div>',
            unsafe_allow_html=True)
st.divider()

# ── Inputs ────────────────────────────────────────────────────────
st.markdown('<div class="sec">📍 Location & Time</div>', unsafe_allow_html=True)
c1,c2,c3 = st.columns(3)
with c1: district = st.selectbox("Agricultural District", DISTRICTS)
with c2: month    = st.selectbox("Month", MONTHS, index=6)
with c3: week     = st.selectbox("Week", [1,2,3,4], index=2)

st.markdown('<div class="sec">🌦️ Weather Conditions</div>', unsafe_allow_html=True)
c4,c5,c6 = st.columns(3)
with c4:
    rainfall = st.number_input("Rainfall (mm)",         0.0, 1000.0, 111.7, 0.1)
    temp     = st.number_input("Mean Temperature (°C)", -10.0, 50.0, 28.5, 0.1)
with c5:
    humidity = st.number_input("Relative Humidity (%)", 0.0, 100.0, 88.4, 0.1)
    sunshine = st.number_input("Sunshine Hours (hrs)",  0.0, 744.0, 23.3, 0.1)
with c6:
    wind_spd = st.number_input("Wind Speed (km/h)",     0.0, 200.0, 6.5,  0.1)
    top_n    = st.selectbox("Number of recommendations", [3,5,10], index=0)

st.markdown('<div class="sec">🌳 Fruit Tree Options</div>', unsafe_allow_html=True)
want_fruit = st.checkbox("Include fruit tree recommendations", value=True)
tree_age   = None
if want_fruit:
    tree_age = st.number_input(
        "Tree age (years) — for fruit tree fertilizer dosage",
        min_value=0, max_value=50, value=10, step=1)

st.markdown("<br>", unsafe_allow_html=True)
btn = st.button("🌾  Get Crop & Fertilizer Recommendations")

# ── Prediction ────────────────────────────────────────────────────
if btn:
    aez      = AEZ_MAP.get(district, 9)
    aez_name = AEZ_NAMES.get(aez, f'AEZ {aez}')

    sample = {f: 0 for f in features}
    for k,v in {
        'Rainfall (mm)':rainfall,'Mean Temp. (*C)':temp,
        'RHmean (%)':humidity,'SShr (hrs)':sunshine,
        'WS (Km/hr)':wind_spd,'Week':week,
    }.items():
        if k in sample: sample[k] = v
    if f'Agricultural Zone_{district}' in sample:
        sample[f'Agricultural Zone_{district}'] = 1
    if f'Month_{month}' in sample:
        sample[f'Month_{month}'] = 1

    X_input   = pd.DataFrame([sample])[features]
    proba     = model.predict_proba(X_input)[0]
    top_idx   = proba.argsort()[-top_n:][::-1]
    top_crops = [(encoder.inverse_transform([i])[0], round(proba[i]*100,1))
                 for i in top_idx]

    st.divider()
    st.markdown(f"### 🌾 Recommendations for **{district}**")
    st.info(f"📌 **Agro-Ecological Zone:** AEZ {aez} — {aez_name}   |   {month}, Week {week}   |   🌡️ {temp}°C   |   🌧️ {rainfall} mm")

    for rank, (crop, conf) in enumerate(top_crops, 1):
        emoji    = get_emoji(crop)
        is_fruit = is_fruit_tree(crop)
        crop_type = "🌳 Fruit Tree" if is_fruit else "🌾 Field Crop"

        fert = get_fertilizer(crop, field_df, fruit_df,
                              tree_age=tree_age if is_fruit else None)

        with st.expander(f"**#{rank}  {emoji} {crop}**  —  {crop_type}  |  Confidence: {conf}%", expanded=True):

            col_left, col_right = st.columns([2,1])

            with col_left:
                st.markdown(f"**AEZ {aez}: {aez_name}**")

                if 'error' in fert:
                    st.warning("No fertilizer data available for this crop.")
                else:
                    unit_type = "per tree" if is_fruit else "per hectare"
                    st.markdown(f"#### 📋 Fertilizer to apply ({unit_type})")

                    if fert['type'] == 'fruit':
                        st.caption(f"Tree age group: {fert.get('age_group','-')}   ·   Variety: {fert.get('variety','-')}")
                        if fert.get('note'):
                            st.caption(f"Note: {fert['note']}")
                    else:
                        st.caption(f"Soil fertility: {fert.get('soil_level','Medium')}   ·   Variety: {fert.get('variety','-')}")

                    # Show each nutrient in plain text
                    for key, val in fert['nutrients'].items():
                        label = NUTRIENT_LABELS.get(key, key)
                        unit  = 'kg/tree' if 'kg/tree' in key else \
                                'g/tree'  if 'g/tree'  in key else \
                                't/ha'    if 't/ha'    in key else 'kg/ha'
                        st.write(f"{label} — **{val} {unit}**")

                    if is_fruit:
                        st.info("💡 Apply in 2 splits: half at start of season, half after first fruiting.")
                    else:
                        st.info("💡 Based on medium soil fertility (BARC FRG-2024). Do a soil test for more precise amounts.")

            with col_right:
                st.metric("Model Confidence", f"{conf}%")
                st.metric("Crop Type", "Fruit Tree" if is_fruit else "Field Crop")
                st.metric("AEZ Zone", f"AEZ {aez}")

    st.markdown('<div class="info-box">ℹ️ <b>How this works:</b> XGBoost classifier (79.25% accuracy) trained on BAMIS weather data. Districts mapped to AEZ zones from BARC FRG-2024. Fertilizer doses from BARC Fertilizer Recommendation Guide 2024. Field crops in kg/ha, fruit trees in g/tree.<br><br>⚠️ Always consult your local agricultural extension officer.</div>',
                unsafe_allow_html=True)

else:
    st.info("👆 Select your district, month, and weather conditions above, then click **Get Recommendations**")
    c1,c2,c3 = st.columns(3)
    with c1: st.markdown("**1. Enter Location & Weather**\n\nChoose your district, current month, and enter weather measurements.")
    with c2: st.markdown("**2. AI Crop Prediction**\n\nXGBoost finds best crops for your area and season from BAMIS historical data.")
    with c3: st.markdown("**3. Simple Fertilizer Advice**\n\nGet plain language fertilizer amounts from BARC FRG-2024 — easy to understand.")
