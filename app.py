import streamlit as st
import joblib
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import os

st.set_page_config(
    page_title="CropSense BD",
    page_icon="🌾",
    layout="wide"
)

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Playfair+Display:wght@700;900&family=DM+Mono:wght@300;400;500&display=swap');

html, body, [class*="css"] { font-family: 'DM Mono', monospace; }
.stApp { background: #f5f0e8; }
#MainMenu, footer, header { visibility: hidden; }

.main-title {
    font-family: 'Playfair Display', serif;
    font-size: 56px;
    font-weight: 900;
    color: #2c1a0e;
    line-height: 1;
    letter-spacing: -2px;
    margin-bottom: 4px;
}
.main-title em { color: #3d6b35; font-style: italic; }
.subtitle {
    font-size: 11px;
    letter-spacing: 3px;
    text-transform: uppercase;
    color: #8a7060;
    margin-bottom: 32px;
}
.section-label {
    font-size: 10px;
    letter-spacing: 3px;
    text-transform: uppercase;
    color: #7a4a2a;
    border-bottom: 1px solid rgba(74,44,23,0.15);
    padding-bottom: 6px;
    margin-bottom: 4px;
    margin-top: 8px;
}
.result-box {
    background: #2c1a0e;
    border-radius: 4px;
    padding: 32px;
    color: #fdf6e3;
    margin-bottom: 24px;
}
.result-label {
    font-size: 10px;
    letter-spacing: 3px;
    text-transform: uppercase;
    color: rgba(232,184,75,0.7);
    margin-bottom: 8px;
}
.result-crop {
    font-family: 'Playfair Display', serif;
    font-size: 48px;
    font-weight: 900;
    color: #e8b84b;
    line-height: 1;
    margin-bottom: 4px;
}
.result-conf { font-size: 14px; color: rgba(255,255,255,0.5); }
.result-conf span { color: #c8e6c9; font-size: 24px; }
.soil-note {
    font-size: 11px;
    color: #8a7060;
    background: #ede8df;
    padding: 10px 14px;
    border-radius: 4px;
    border-left: 3px solid #3d6b35;
    margin-bottom: 12px;
}
.stButton > button {
    width: 100%;
    background: #2c1a0e !important;
    color: #e8b84b !important;
    border: none !important;
    border-radius: 2px !important;
    font-family: 'DM Mono', monospace !important;
    font-size: 12px !important;
    letter-spacing: 3px !important;
    text-transform: uppercase !important;
    padding: 16px !important;
}
.stButton > button:hover { background: #3d6b35 !important; }
</style>
""", unsafe_allow_html=True)

# ── Load model ───────────────────────────────────────────────────
@st.cache_resource
def load_model():
    base = '/mount/src/crop-recommendation'
    m = joblib.load(f'{base}/crop_model_with_soil.pkl')
    e = joblib.load(f'{base}/label_encoder_soil.pkl')
    x = joblib.load(f'{base}/feature_columns_soil.pkl')
    return m, e, x

try:
    model, encoder, X_cols = load_model()
    model_loaded = True
except Exception as err:
    model_loaded = False

# ── Constants ────────────────────────────────────────────────────
ZONES  = ['Barisal','Bogra','Chittagonj','Cumilla','Dhaka',
          'Dinajpur','Faridpur','Jashore','Khulna','Mymensingh',
          'Rajshahi','Rangamati','Rangpur','Sylhet']
MONTHS = ['January','February','March','April','May','June',
          'July','August','September','October','November','December']

# Zone-based default soil values (avg for Bangladesh)
ZONE_SOIL = {
    'Barisal':    {'N': 62, 'P': 38, 'K': 52, 'ph': 6.3},
    'Bogra':      {'N': 58, 'P': 35, 'K': 48, 'ph': 6.1},
    'Chittagonj': {'N': 70, 'P': 42, 'K': 55, 'ph': 5.9},
    'Cumilla':    {'N': 65, 'P': 40, 'K': 50, 'ph': 6.2},
    'Dhaka':      {'N': 60, 'P': 38, 'K': 48, 'ph': 6.4},
    'Dinajpur':   {'N': 55, 'P': 32, 'K': 45, 'ph': 6.0},
    'Faridpur':   {'N': 63, 'P': 39, 'K': 51, 'ph': 6.3},
    'Jashore':    {'N': 61, 'P': 37, 'K': 49, 'ph': 6.2},
    'Khulna':     {'N': 64, 'P': 40, 'K': 52, 'ph': 6.1},
    'Mymensingh': {'N': 68, 'P': 41, 'K': 54, 'ph': 6.0},
    'Rajshahi':   {'N': 56, 'P': 33, 'K': 46, 'ph': 6.3},
    'Rangamati':  {'N': 72, 'P': 44, 'K': 58, 'ph': 5.8},
    'Rangpur':    {'N': 57, 'P': 34, 'K': 47, 'ph': 6.1},
    'Sylhet':     {'N': 74, 'P': 45, 'K': 60, 'ph': 5.7},
}

CROP_EMOJI = {
    'Aman':'🌾','Aush':'🌾','Boro':'🌾','Wheat':'🌿','Jute':'🪢',
    'Sugarcane':'🎋','Potato':'🥔','Tomato':'🍅','Banana':'🍌',
    'Mango':'🥭','Guava':'🍈','pineapple':'🍍','jackfruit':'🫐',
    'papaya':'🍈','licchi':'🍒','Soybean':'🫘','Red Lentil':'🫘',
    'corn khorip-1':'🌽','Corn(Robi)':'🌽','garlic':'🧄','Tula':'☁️',
}
def get_emoji(crop):
    for k, v in CROP_EMOJI.items():
        if k.lower() in crop.lower(): return v
    return '🌱'

# ── Header ───────────────────────────────────────────────────────
st.markdown('<div class="main-title">Smart <em>Crop</em> Advisor</div>', unsafe_allow_html=True)
st.markdown('<div class="subtitle">🌾 Random Forest · 41 Crops · 14 Bangladesh Regions · 99.87% Accuracy</div>', unsafe_allow_html=True)

col1, col2, col3, col4 = st.columns(4)
with col1: st.metric("Accuracy",  "99.87%")
with col2: st.metric("Crops",     "41")
with col3: st.metric("Regions",   "14")
with col4: st.metric("CV Score",  "99.95%")
st.divider()

if not model_loaded:
    st.error("⚠️ Model files not found.")
    st.stop()

# ── Inputs ───────────────────────────────────────────────────────
st.markdown('<div class="section-label">Location & Time</div>', unsafe_allow_html=True)
c1, c2, c3 = st.columns(3)
with c1: zone  = st.selectbox("Agricultural Zone", ZONES)
with c2: month = st.selectbox("Month", MONTHS, index=6)
with c3: week  = st.selectbox("Week", [1, 2, 3, 4], index=2)

st.markdown('<div class="section-label">Weather Conditions</div>', unsafe_allow_html=True)
c4, c5 = st.columns(2)
with c4:
    rainfall = st.number_input("Rainfall (mm)",      min_value=0.0,   max_value=1000.0, value=111.7, step=0.1)
    temp     = st.number_input("Mean Temp (°C)",     min_value=-10.0, max_value=50.0,   value=28.5,  step=0.1)
    humidity = st.number_input("Humidity (%)",       min_value=0.0,   max_value=100.0,  value=88.4,  step=0.1)
with c5:
    sunshine = st.number_input("Sunshine (hrs)",     min_value=0.0,   max_value=744.0,  value=23.3,  step=0.1)
    wind_dir = st.number_input("Wind Direction (°)", min_value=0.0,   max_value=360.0,  value=175.0, step=1.0)
    wind_spd = st.number_input("Wind Speed (km/h)",  min_value=0.0,   max_value=200.0,  value=6.5,   step=0.1)

# ── Soil Inputs ──────────────────────────────────────────────────
st.markdown('<div class="section-label">Soil Properties</div>', unsafe_allow_html=True)
st.markdown(f'<div class="soil-note">💡 Default values are pre-filled based on average soil data for <b>{zone}</b>. Change if you have a soil test report.</div>', unsafe_allow_html=True)

default_soil = ZONE_SOIL[zone]
c6, c7, c8, c9 = st.columns(4)
with c6: N  = st.number_input("Nitrogen (N)",    min_value=0.0, max_value=200.0, value=float(default_soil['N']), step=1.0)
with c7: P  = st.number_input("Phosphorus (P)",  min_value=0.0, max_value=200.0, value=float(default_soil['P']), step=1.0)
with c8: K  = st.number_input("Potassium (K)",   min_value=0.0, max_value=200.0, value=float(default_soil['K']), step=1.0)
with c9: ph = st.number_input("Soil pH",         min_value=0.0, max_value=14.0,  value=float(default_soil['ph']), step=0.1)

st.markdown("<br>", unsafe_allow_html=True)
predict_btn = st.button("⟶  Suggest Crop")

# ── Prediction ───────────────────────────────────────────────────
if predict_btn:
    with st.spinner("Analyzing conditions..."):
        sample = pd.DataFrame([{
            'Agricultural Zone': zone,
            'Month':             month,
            'Week':              week,
            'Rainfall (mm)':     rainfall,
            'Mean Temp. (*C)':   temp,
            'RHmean (%)':        humidity,
            'SShr (hrs)':        sunshine,
            'WD (deg)':          wind_dir,
            'WS (Km/hr)':        wind_spd,
            'N':                 N,
            'P':                 P,
            'K':                 K,
            'ph':                ph,
        }])
        sample  = pd.get_dummies(sample).reindex(columns=X_cols, fill_value=0)
        pred    = model.predict(sample)
        proba   = model.predict_proba(sample)[0]
        top_idx = proba.argsort()[-10:][::-1]

        crop       = encoder.inverse_transform(pred)[0]
        confidence = round(float(proba.max()) * 100, 1)
        top10      = [(encoder.inverse_transform([i])[0], round(float(proba[i])*100,1)) for i in top_idx]

    emoji = get_emoji(crop)
    st.markdown(f"""
    <div class="result-box">
        <div class="result-label">Recommended Crop</div>
        <div class="result-crop">{emoji} {crop}</div>
        <div class="result-conf">Confidence: <span>{confidence}%</span></div>
    </div>
    """, unsafe_allow_html=True)

    col_a, col_b = st.columns([3, 2])
    with col_a:
        st.markdown("**Top 10 Crop Probabilities**")
        crops_list = [t[0] for t in top10]
        probs_list = [t[1] for t in top10]
        colors = ['#e8b84b' if i==0 else '#3d6b35' if i<3 else '#7a4a2a' for i in range(len(crops_list))]
        fig = go.Figure(go.Bar(
            x=probs_list[::-1], y=crops_list[::-1],
            orientation='h', marker_color=colors[::-1],
            text=[f"{p}%" for p in probs_list[::-1]], textposition='outside',
        ))
        fig.update_layout(
            paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
            font=dict(family='DM Mono', color='#2c1a0e', size=12),
            margin=dict(l=0, r=60, t=10, b=10), height=360,
            xaxis=dict(showgrid=False, showticklabels=False, zeroline=False),
            yaxis=dict(showgrid=False),
        )
        st.plotly_chart(fig, use_container_width=True)

    with col_b:
        st.markdown("**Input Summary**")
        st.markdown(f"""
        | Parameter | Value |
        |---|---|
        | Zone | {zone} |
        | Month | {month} |
        | Week | {week} |
        | Rainfall | {rainfall} mm |
        | Temperature | {temp} °C |
        | Humidity | {humidity} % |
        | Sunshine | {sunshine} hrs |
        | Wind Dir | {wind_dir}° |
        | Wind Speed | {wind_spd} km/h |
        | N | {N} |
        | P | {P} |
        | K | {K} |
        | pH | {ph} |
        """)
else:
    st.info("👆 Fill in the conditions above and click **Suggest Crop**")
    c1, c2, c3 = st.columns(3)
    with c1: st.markdown("**1. Enter Conditions**\n\nSelect zone, month, week, weather and soil data above.")
    with c2: st.markdown("**2. AI Analysis**\n\nRandom Forest analyzes 13 features including N, P, K, pH.")
    with c3: st.markdown("**3. Get Recommendation**\n\nGet best crop with 99.87% accuracy and top 10 alternatives.")
