# ================================================================
# CropSense BD - Crop & Fertilizer Recommendation System
# streamlit run app_final.py
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
.aez-box {
    background: #2c1a0e; color: #e8b84b;
    border-radius: 4px; padding: 10px 14px;
    font-size: 13px; margin-bottom: 16px;
    display: inline-block;
}
.crop-card {
    background: #2c1a0e; border-radius: 6px;
    padding: 20px 24px; margin-bottom: 16px;
}
.crop-title {
    font-family: Georgia, serif; font-size: 26px;
    font-weight: 900; color: #e8b84b; margin-bottom: 2px;
}
.crop-meta { font-size: 12px; color: rgba(255,255,255,0.5); margin-bottom: 12px; }
.aez-tag {
    display: inline-block;
    background: rgba(232,184,75,0.15);
    border: 1px solid rgba(232,184,75,0.4);
    color: #e8b84b; padding: 3px 10px;
    border-radius: 12px; font-size: 11px;
    margin-right: 6px; margin-bottom: 10px;
}
.fert-label {
    font-size: 11px; color: rgba(232,184,75,0.7);
    letter-spacing: 2px; text-transform: uppercase; margin-bottom: 8px;
}
.fert-table { width:100%; border-collapse:collapse; font-size:13px; }
.fert-table th {
    background:rgba(255,255,255,0.1); color:#e8b84b;
    padding:7px 10px; text-align:left;
    font-size:11px; text-transform:uppercase; letter-spacing:1px;
}
.fert-table td {
    padding:7px 10px;
    border-bottom:1px solid rgba(255,255,255,0.07); color:#fdf6e3;
}
.fert-table tr:last-child td { border-bottom: none; }
.badge-f {
    background:#3d6b35; color:white;
    padding:2px 8px; border-radius:10px; font-size:10px;
    text-transform:uppercase; letter-spacing:1px;
}
.badge-t {
    background:#e8b84b; color:#2c1a0e;
    padding:2px 8px; border-radius:10px; font-size:10px;
    text-transform:uppercase; letter-spacing:1px;
}
.no-fert { color:rgba(255,255,255,0.4); font-size:13px; font-style:italic; }
.info-box {
    background:#edf4eb; border-left:4px solid #3d6b35;
    padding:12px 16px; border-radius:0 4px 4px 0;
    font-size:13px; color:#2c4a2a; margin: 16px 0;
}
.conf-bar-bg {
    background: rgba(255,255,255,0.1);
    border-radius: 4px; height: 6px; margin-top: 6px;
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
    1:'Old Himalayan Piedmont Plain',
    3:'Tista Meander Floodplain',
    4:'Karatoya-Bangali Floodplain',
    8:'Young Brahmaputra Floodplain',
    9:'Old Brahmaputra Floodplain',
    11:'High Ganges River Floodplain',
    12:'Low Ganges River Floodplain',
    13:'Ganges Tidal Floodplain',
    18:'Meghna Floodplain',
    21:'Sylhet Basin',
    23:'Chittagong Coastal Plain',
    24:'Chittagong Hill Tracts',
}
MONTHS = ['January','February','March','April','May','June',
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

# ── Load model ────────────────────────────────────────────────────
@st.cache_resource
def load_all():
    paths = [
        os.path.dirname(os.path.abspath(__file__)),
        '/mount/src/crop-recommendation', '.',
    ]
    base = next((p for p in paths
                 if os.path.exists(os.path.join(p,'crop_model.pkl'))), '.')
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

st.markdown('<div class="info-box">🌱 Select your district and month, enter current weather conditions, then click <b>Get Recommendations</b>. The app will show the best crops to grow along with official BARC fertilizer doses.</div>',
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
want_fruit = st.checkbox("Include fruit tree recommendations", value=True)
tree_age   = None
if want_fruit:
    tree_age = st.number_input(
        "Tree age (years) — used to determine fertilizer dosage for fruit trees",
        min_value=0, max_value=50, value=10, step=1
    )

st.markdown("<br>", unsafe_allow_html=True)
btn = st.button("🌾  Get Crop & Fertilizer Recommendations")

# ── Prediction ────────────────────────────────────────────────────
if btn:
    aez      = AEZ_MAP.get(district, 9)
    aez_name = AEZ_NAMES.get(aez, f'AEZ {aez}')

    # Build input sample matching training features
    sample = {f: 0 for f in features}
    weather_vals = {
        'Rainfall (mm)': rainfall, 'Mean Temp. (*C)': temp,
        'RHmean (%)': humidity, 'SShr (hrs)': sunshine,
        'WS (Km/hr)': wind_spd, 'Week': week,
    }
    for k, v in weather_vals.items():
        if k in sample: sample[k] = v

    # One-hot zone and month
    zone_col  = f'Agricultural Zone_{district}'
    month_col = f'Month_{month}'
    if zone_col  in sample: sample[zone_col]  = 1
    if month_col in sample: sample[month_col] = 1

    X_input = pd.DataFrame([sample])[features]

    proba     = model.predict_proba(X_input)[0]
    top_idx   = proba.argsort()[-top_n:][::-1]
    top_crops = [(encoder.inverse_transform([i])[0], round(proba[i]*100, 1))
                 for i in top_idx]

    # ── Results ───────────────────────────────────────────────────
    st.divider()
    st.markdown(f"### 🌾 Recommendations for **{district}**")

    # AEZ info box
    st.markdown(f"""
    <div class="aez-box">
        📌 &nbsp; <b>AEZ {aez}</b> — {aez_name} &nbsp;·&nbsp;
        {month}, Week {week} &nbsp;·&nbsp;
        🌡️ {temp}°C &nbsp; 🌧️ {rainfall}mm &nbsp; 💧 {humidity}%
    </div>
    """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    for rank, (crop, conf) in enumerate(top_crops, 1):
        emoji    = get_emoji(crop)
        is_fruit = is_fruit_tree(crop)
        badge    = '<span class="badge-t">🌳 Fruit Tree</span>' \
                   if is_fruit else '<span class="badge-f">🌾 Field Crop</span>'

        fert = get_fertilizer(crop, field_df, fruit_df,
                              tree_age=tree_age if is_fruit else None)

        # Confidence bar width
        bar_w = int(conf)

        # Fertilizer HTML
        if 'error' in fert:
            fert_html = f'<p class="no-fert">⚠️ {fert["error"]}</p>'
        else:
            unit      = fert['unit']
            variety   = fert.get('variety', '-')
            note      = fert.get('note', '')
            age_group = fert.get('age_group', '-')
            soil_lvl  = fert.get('soil_level', '-')

            if fert['type'] == 'fruit':
                meta = f'Variety: {variety} &nbsp;·&nbsp; Age group: {age_group}'
            else:
                meta = f'Variety: {variety} &nbsp;·&nbsp; Soil level: {soil_lvl} &nbsp;·&nbsp; Unit: {unit}'
            if note:
                meta += f' &nbsp;·&nbsp; <i>{note}</i>'

            rows = ''.join(
                f'<tr><td>{n}</td><td><b>{v}</b> {unit}</td></tr>'
                for n, v in fert['nutrients'].items()
            )
            fert_html = f'''
            <p style="font-size:11px;color:rgba(255,255,255,0.4);margin-bottom:8px;">{meta}</p>
            <table class="fert-table">
              <tr><th>Nutrient</th><th>Recommended Amount</th></tr>
              {rows if rows else "<tr><td colspan='2' style='color:rgba(255,255,255,0.3)'>No data available</td></tr>"}
            </table>''' if rows else '<p class="no-fert">No nutrient data found.</p>'

        # AEZ tag for output
        aez_tag = f'<span class="aez-tag">AEZ {aez}: {aez_name}</span>'

        st.markdown(f"""
        <div class="crop-card">
          <div style="display:flex;justify-content:space-between;align-items:flex-start;">
            <div>
              <div class="crop-title">#{rank} &nbsp; {emoji} {crop}</div>
              <div class="crop-meta">
                {badge} &nbsp; {aez_tag}
              </div>
            </div>
            <div style="text-align:right;">
              <div style="font-size:28px;color:#c8e6c9;font-weight:700;">{conf}%</div>
              <div style="font-size:10px;color:rgba(255,255,255,0.4);">confidence</div>
              <div class="conf-bar-bg">
                <div style="width:{bar_w}%;background:linear-gradient(90deg,#3d6b35,#e8b84b);
                            height:6px;border-radius:4px;"></div>
              </div>
            </div>
          </div>
          <div class="fert-label" style="margin-top:12px;">
            📋 Fertilizer Recommendation — BARC FRG-2024
          </div>
          {fert_html}
        </div>
        """, unsafe_allow_html=True)

    st.markdown("""
    <div class="info-box">
    ℹ️ <b>How recommendations are generated:</b><br>
    Crops are predicted using an <b>XGBoost classifier</b> (79.25% accuracy) trained on
    historical BAMIS weather data from 14 agricultural districts.
    Each district is mapped to its <b>Agro-Ecological Zone (AEZ)</b> based on BARC FRG-2024 (pages 28–35).
    Fertilizer doses follow official <b>BARC Fertilizer Recommendation Guide 2024</b> —
    field crops in <b>kg/ha</b> assuming medium soil fertility,
    fruit trees in <b>g/tree</b> based on tree age group.
    <br><br>
    ⚠️ <b>Always consult your local agricultural extension officer</b> for site-specific advice.
    </div>
    """, unsafe_allow_html=True)

else:
    st.info("👆 Select your district, month, and weather conditions above, then click **Get Recommendations**")
    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown("**1. Enter Location & Weather**\n\nSelect district, month, week and input current weather measurements from your area.")
    with c2:
        st.markdown("**2. AI Analysis**\n\nXGBoost model analyzes conditions against BAMIS historical data and maps your district to its Agro-Ecological Zone (AEZ).")
    with c3:
        st.markdown("**3. Crop + AEZ + Fertilizer**\n\nGet top crop picks with AEZ zone info and official BARC fertilizer doses for each recommended crop.")
