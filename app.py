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
    font-family: 'Segoe UI', Arial, sans-serif; color: #1a1a1a;
}
.stApp { background: #f5f0e8; }
#MainMenu, footer, header { visibility: hidden; }
[data-testid="collapsedControl"] {
    display: block !important; visibility: visible !important;
    background: #e8b84b !important; border-radius: 50% !important;
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
.crop-card {
    background: #2c1a0e; border-radius: 8px;
    padding: 24px 28px; margin-bottom: 20px;
}
.crop-title {
    font-family: Georgia, serif; font-size: 28px;
    font-weight: 900; color: #e8b84b; margin-bottom: 4px;
}
.aez-tag {
    display: inline-block;
    background: rgba(232,184,75,0.15);
    border: 1px solid rgba(232,184,75,0.4);
    color: #e8b84b; padding: 3px 10px;
    border-radius: 12px; font-size: 11px; margin-right: 6px;
}
.badge-f {
    background:#3d6b35; color:white;
    padding:3px 10px; border-radius:10px; font-size:11px;
}
.badge-t {
    background:#e8b84b; color:#2c1a0e;
    padding:3px 10px; border-radius:10px; font-size:11px;
}
.fert-section {
    background: rgba(255,255,255,0.06);
    border-radius: 6px; padding: 16px 18px; margin-top: 14px;
}
.fert-title {
    font-size: 12px; font-weight: 700;
    color: #e8b84b; letter-spacing: 1px;
    text-transform: uppercase; margin-bottom: 12px;
}
.fert-item {
    display: flex; align-items: center;
    padding: 8px 0;
    border-bottom: 1px solid rgba(255,255,255,0.06);
}
.fert-item:last-child { border-bottom: none; }
.fert-name {
    font-size: 14px; color: #fdf6e3;
    font-weight: 600; flex: 1;
}
.fert-amount {
    font-size: 16px; color: #c8e6c9;
    font-weight: 700; margin-right: 8px;
}
.fert-unit {
    font-size: 11px; color: rgba(255,255,255,0.4);
}
.fert-note {
    font-size: 11px; color: rgba(255,255,255,0.35);
    margin-top: 10px; font-style: italic;
}
.no-fert {
    font-size: 13px; color: rgba(255,255,255,0.35);
    font-style: italic; padding: 8px 0;
}
.conf-num {
    font-size: 30px; color: #c8e6c9; font-weight: 700;
}
.conf-label {
    font-size: 10px; color: rgba(255,255,255,0.35); margin-top: 2px;
}
.info-box {
    background:#edf4eb; border-left:4px solid #3d6b35;
    padding:12px 16px; border-radius:0 4px 4px 0;
    font-size:13px; color:#2c4a2a; margin: 16px 0;
}
.aez-box {
    background: #2c1a0e; color: #e8b84b;
    border-radius: 6px; padding: 12px 16px;
    font-size: 14px; margin-bottom: 20px;
    border: 1px solid rgba(232,184,75,0.3);
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
    4:'Karatoya-Bangali Floodplain', 8:'Young Brahmaputra Floodplain',
    9:'Old Brahmaputra Floodplain', 11:'High Ganges River Floodplain',
    12:'Low Ganges River Floodplain', 13:'Ganges Tidal Floodplain',
    18:'Meghna Floodplain', 21:'Sylhet Basin',
    23:'Chittagong Coastal Plain', 24:'Chittagong Hill Tracts',
}
MONTHS = ['January','February','March','April','May','June',
          'July','August','September','October','November','December']
DISTRICTS = sorted(AEZ_MAP.keys())

# Friendly fertilizer names for farmers
FRIENDLY_NAMES = {
    'N (kg/ha)':              ('Nitrogen (N)',           'kg per hectare',  '🌿'),
    'P (kg/ha)':              ('Phosphorus (P)',         'kg per hectare',  '🪨'),
    'K (kg/ha)':              ('Potassium (K)',          'kg per hectare',  '🌱'),
    'S (kg/ha)':              ('Sulphur (S)',            'kg per hectare',  '🟡'),
    'Zn (kg/ha)':             ('Zinc (Zn)',              'kg per hectare',  '⚪'),
    'B (kg/ha)':              ('Boron (B)',              'kg per hectare',  '🔵'),
    'Mg (kg/ha)':             ('Magnesium (Mg)',         'kg per hectare',  '⚫'),
    'Organic Matter (t/ha)':  ('Organic Compost/Manure','tons per hectare','♻️'),
    'N (g/tree)':             ('Nitrogen (N)',           'grams per tree',  '🌿'),
    'P (g/tree)':             ('Phosphorus (P)',         'grams per tree',  '🪨'),
    'K (g/tree)':             ('Potassium (K)',          'grams per tree',  '🌱'),
    'S (g/tree)':             ('Sulphur (S)',            'grams per tree',  '🟡'),
    'Zn (g/tree)':            ('Zinc (Zn)',              'grams per tree',  '⚪'),
    'B (g/tree)':             ('Boron (B)',              'grams per tree',  '🔵'),
    'Organic Matter (kg/tree)':('Organic Compost/Manure','kg per tree',    '♻️'),
}

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

def friendly_fert_html(fert):
    """Convert fertilizer data to farmer-friendly plain display."""
    if 'error' in fert:
        return f'<p class="no-fert">⚠️ No fertilizer data available for this crop.</p>'

    is_fruit  = fert['type'] == 'fruit'
    unit_type = 'per tree' if is_fruit else 'per hectare'

    if is_fruit:
        age_group = fert.get('age_group', '-')
        variety   = fert.get('variety', '-')
        note      = fert.get('note', '')
        header_info = f'Tree variety: {variety} &nbsp;·&nbsp; Age group: {age_group}'
        if note: header_info += f' &nbsp;·&nbsp; {note}'
    else:
        variety   = fert.get('variety', '-')
        soil_lvl  = fert.get('soil_level', 'Medium')
        header_info = f'Variety: {variety} &nbsp;·&nbsp; Soil fertility: {soil_lvl}'

    rows_html = ''
    for key, val in fert['nutrients'].items():
        if key in FRIENDLY_NAMES:
            name, unit_label, icon = FRIENDLY_NAMES[key]
        else:
            name, unit_label, icon = key, unit_type, '🌱'

        rows_html += f'''
        <div class="fert-item">
            <span class="fert-name">{icon} &nbsp; {name}</span>
            <span class="fert-amount">{val}</span>
            <span class="fert-unit">{unit_label}</span>
        </div>'''

    note_html = ''
    if is_fruit:
        note_html = '<p class="fert-note">💡 Apply in split doses — half at start of growing season, half after first fruiting.</p>'
    else:
        note_html = '<p class="fert-note">💡 Apply based on medium soil fertility (BARC FRG-2024). Get a soil test for precise doses.</p>'

    return f'''
    <div class="fert-section">
        <div class="fert-title">📋 How much fertilizer to apply ({unit_type})</div>
        <p style="font-size:11px;color:rgba(255,255,255,0.3);margin-bottom:10px;">{header_info}</p>
        {rows_html if rows_html else '<p class="no-fert">No nutrient data found.</p>'}
        {note_html}
    </div>'''

# ── Load model ────────────────────────────────────────────────────
@st.cache_resource
def load_all():
    paths = [
        os.path.dirname(os.path.abspath(__file__)),
        '/mount/src/crop-recommendation', '.',
    ]
    base = next((p for p in paths
                 if os.path.exists(os.path.join(p, 'crop_model.pkl'))), '.')
    model    = joblib.load(os.path.join(base, 'crop_model.pkl'))
    encoder  = joblib.load(os.path.join(base, 'label_encoder.pkl'))
    features = joblib.load(os.path.join(base, 'feature_names.pkl'))
    field_df = load_field_df(os.path.join(base, 'field_crops_fertilizer.csv'))
    fruit_df = load_fruit_df(os.path.join(base, 'fruit_trees_fertilizer.csv'))
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
with c1: st.metric("Best Model",  "XGBoost")
with c2: st.metric("Accuracy",    "79.25%")
with c3: st.metric("Crops",       "41")
with c4: st.metric("Districts",   "14")

st.markdown('<div class="info-box">🌱 Select your district and month, enter current weather conditions, then click <b>Get Recommendations</b>. You will see the best crops to grow with exact fertilizer amounts in simple language.</div>',
            unsafe_allow_html=True)
st.divider()

# ── Inputs ────────────────────────────────────────────────────────
st.markdown('<div class="sec">📍 Location & Time</div>', unsafe_allow_html=True)
c1, c2, c3 = st.columns(3)
with c1: district = st.selectbox("Agricultural District", DISTRICTS)
with c2: month    = st.selectbox("Month", MONTHS, index=6)
with c3: week     = st.selectbox("Week", [1,2,3,4], index=2)

st.markdown('<div class="sec">🌦️ Current Weather Conditions</div>', unsafe_allow_html=True)
c4, c5, c6 = st.columns(3)
with c4:
    rainfall = st.number_input("Rainfall (mm)",         0.0, 1000.0, 111.7, 0.1)
    temp     = st.number_input("Mean Temperature (°C)", -10.0, 50.0, 28.5, 0.1)
with c5:
    humidity = st.number_input("Relative Humidity (%)", 0.0, 100.0, 88.4, 0.1)
    sunshine = st.number_input("Sunshine Hours (hrs)",  0.0, 744.0, 23.3, 0.1)
with c6:
    wind_spd = st.number_input("Wind Speed (km/h)",     0.0, 200.0, 6.5,  0.1)
    top_n    = st.selectbox("Number of recommendations", [3, 5, 10], index=0)

st.markdown('<div class="sec">🌳 Fruit Tree Options</div>', unsafe_allow_html=True)
want_fruit = st.checkbox("Include fruit tree fertilizer recommendations", value=True)
tree_age   = None
if want_fruit:
    tree_age = st.number_input(
        "Tree age (years) — used to find the right fertilizer amount for fruit trees",
        min_value=0, max_value=50, value=10, step=1
    )

st.markdown("<br>", unsafe_allow_html=True)
btn = st.button("🌾  Get Crop & Fertilizer Recommendations")

# ── Prediction ────────────────────────────────────────────────────
if btn:
    aez      = AEZ_MAP.get(district, 9)
    aez_name = AEZ_NAMES.get(aez, f'AEZ {aez}')

    # Build sample
    sample = {f: 0 for f in features}
    for k, v in {
        'Rainfall (mm)': rainfall, 'Mean Temp. (*C)': temp,
        'RHmean (%)': humidity, 'SShr (hrs)': sunshine,
        'WS (Km/hr)': wind_spd, 'Week': week,
    }.items():
        if k in sample: sample[k] = v

    if f'Agricultural Zone_{district}' in sample:
        sample[f'Agricultural Zone_{district}'] = 1
    if f'Month_{month}' in sample:
        sample[f'Month_{month}'] = 1

    X_input   = pd.DataFrame([sample])[features]
    proba     = model.predict_proba(X_input)[0]
    top_idx   = proba.argsort()[-top_n:][::-1]
    top_crops = [(encoder.inverse_transform([i])[0], round(proba[i]*100, 1))
                 for i in top_idx]

    st.divider()
    st.markdown(f"### 🌾 Crop Recommendations for **{district}**")

    st.markdown(f"""
    <div class="aez-box">
        📌 <b>Your Agro-Ecological Zone: AEZ {aez} — {aez_name}</b><br>
        <span style="font-size:12px;color:rgba(232,184,75,0.7);">
        {month}, Week {week} &nbsp;·&nbsp;
        Temperature: {temp}°C &nbsp;·&nbsp;
        Rainfall: {rainfall} mm &nbsp;·&nbsp;
        Humidity: {humidity}%
        </span>
    </div>
    """, unsafe_allow_html=True)

    for rank, (crop, conf) in enumerate(top_crops, 1):
        emoji    = get_emoji(crop)
        is_fruit = is_fruit_tree(crop)
        badge    = '<span class="badge-t">🌳 Fruit Tree</span>' \
                   if is_fruit else '<span class="badge-f">🌾 Field Crop</span>'

        fert     = get_fertilizer(crop, field_df, fruit_df,
                                  tree_age=tree_age if is_fruit else None)
        fert_html = friendly_fert_html(fert)

        st.markdown(f"""
        <div class="crop-card">
          <div style="display:flex;justify-content:space-between;align-items:flex-start;">
            <div>
              <div class="crop-title">#{rank} &nbsp; {emoji} {crop}</div>
              <div style="margin-top:6px;">
                {badge} &nbsp;
                <span class="aez-tag">AEZ {aez}: {aez_name}</span>
              </div>
            </div>
            <div style="text-align:right;">
              <div class="conf-num">{conf}%</div>
              <div class="conf-label">model confidence</div>
            </div>
          </div>
          {fert_html}
        </div>
        """, unsafe_allow_html=True)

    st.markdown("""
    <div class="info-box">
    ℹ️ <b>How this works:</b> An XGBoost classifier (79.25% accuracy) trained on BAMIS
    weather data predicts the most suitable crops for your district and conditions.
    Your district is mapped to its <b>Agro-Ecological Zone (AEZ)</b> from BARC FRG-2024.
    Fertilizer amounts come from the official <b>BARC Fertilizer Recommendation Guide 2024</b>.
    Field crop amounts are in <b>kg per hectare</b> (medium soil).
    Fruit tree amounts are in <b>grams per tree</b> based on tree age.
    <br><br>⚠️ Always consult your local agricultural extension officer for final advice.
    </div>
    """, unsafe_allow_html=True)

else:
    st.info("👆 Select your district, month, and weather conditions above, then click **Get Recommendations**")
    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown("**1. Enter Location & Weather**\n\nChoose your district, current month, and input weather measurements.")
    with c2:
        st.markdown("**2. AI Crop Prediction**\n\nXGBoost model finds the best crops for your conditions based on historical BAMIS data.")
    with c3:
        st.markdown("**3. Plain Fertilizer Advice**\n\nGet simple, clear fertilizer amounts from BARC FRG-2024 — easy to understand and act on.")
