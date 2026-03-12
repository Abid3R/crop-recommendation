import streamlit as st
import joblib
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import os, glob

st.set_page_config(page_title="Debug", page_icon="🌾")

st.write("### Debug Info")
st.write("Current dir:", os.getcwd())
st.write("__file__:", __file__)
st.write("Files in current dir:", os.listdir('.'))
st.write("Files in /mount/src/:", os.listdir('/mount/src/') if os.path.exists('/mount/src/') else "not found")

# Find all pkl files anywhere
pkl_files = glob.glob('/mount/**/*.pkl', recursive=True)
st.write("PKL files found:", pkl_files)
st.stop()
# ── Page config ──────────────────────────────────────────────────
st.set_page_config(
    page_title="CropSense BD",
    page_icon="🌾",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ── Custom CSS ───────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Playfair+Display:wght@700;900&family=DM+Mono:wght@300;400;500&display=swap');

/* Global */
html, body, [class*="css"] {
    font-family: 'DM Mono', monospace;
}

.stApp {
    background: #f5f0e8;
}

/* Hide default streamlit elements */
#MainMenu, footer, header { visibility: hidden; }

/* Sidebar */
[data-testid="stSidebar"] {
    background: #2c1a0e !important;
    border-right: none;
}

[data-testid="stSidebar"] * {
    color: #fdf6e3 !important;
}

[data-testid="stSidebar"] .stSelectbox label,
[data-testid="stSidebar"] .stSlider label,
[data-testid="stSidebar"] .stNumberInput label {
    color: rgba(253,246,227,0.6) !important;
    font-size: 11px !important;
    letter-spacing: 2px !important;
    text-transform: uppercase !important;
}

[data-testid="stSidebar"] select,
[data-testid="stSidebar"] input {
    background: rgba(255,255,255,0.08) !important;
    border: 1px solid rgba(255,255,255,0.15) !important;
    color: #fdf6e3 !important;
    border-radius: 2px !important;
}

/* Main title */
.main-title {
    font-family: 'Playfair Display', serif;
    font-size: 64px;
    font-weight: 900;
    color: #2c1a0e;
    line-height: 1;
    letter-spacing: -2px;
    margin-bottom: 4px;
}

.main-title em {
    color: #3d6b35;
    font-style: italic;
}

.subtitle {
    font-size: 11px;
    letter-spacing: 3px;
    text-transform: uppercase;
    color: #8a7060;
    margin-bottom: 40px;
}

/* Result box */
.result-box {
    background: #2c1a0e;
    border-radius: 4px;
    padding: 36px;
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
    font-size: 52px;
    font-weight: 900;
    color: #e8b84b;
    line-height: 1;
    margin-bottom: 4px;
}

.result-conf {
    font-size: 14px;
    color: rgba(255,255,255,0.5);
}

.result-conf span {
    color: #c8e6c9;
    font-size: 24px;
}

/* Metric cards */
.metric-row {
    display: flex;
    gap: 16px;
    margin-bottom: 24px;
}

.metric-card {
    flex: 1;
    background: white;
    border: 1px solid rgba(74,44,23,0.1);
    border-radius: 4px;
    padding: 20px;
    text-align: center;
}

.metric-value {
    font-size: 28px;
    font-weight: 500;
    color: #2c1a0e;
}

.metric-label {
    font-size: 10px;
    letter-spacing: 2px;
    text-transform: uppercase;
    color: #8a7060;
    margin-top: 4px;
}

/* Predict button */
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
    padding: 14px !important;
    transition: all 0.3s !important;
}

.stButton > button:hover {
    background: #3d6b35 !important;
    transform: translateY(-1px);
    box-shadow: 0 8px 24px rgba(44,26,14,0.2) !important;
}

/* Section divider */
.section-div {
    font-size: 10px;
    letter-spacing: 3px;
    text-transform: uppercase;
    color: #8a7060;
    border-bottom: 1px solid rgba(74,44,23,0.12);
    padding-bottom: 8px;
    margin: 20px 0 16px;
}

.badge {
    display: inline-block;
    background: #3d6b35;
    color: #fdf6e3;
    padding: 3px 10px;
    border-radius: 2px;
    font-size: 10px;
    letter-spacing: 2px;
    text-transform: uppercase;
    margin-bottom: 16px;
}
</style>
""", unsafe_allow_html=True)

# ── Load model ───────────────────────────────────────────────────
@st.cache_resource
def load_model():
    import os
    base_paths = [
        '',
        os.path.dirname(os.path.abspath(__file__)),
        '/mount/src/crop-recommendation/',
    ]
    for base in base_paths:
        try:
            m = joblib.load(os.path.join(base, 'crop_model.pkl'))
            e = joblib.load(os.path.join(base, 'label_encoder.pkl'))
            x = joblib.load(os.path.join(base, 'feature_columns.pkl'))
            return m, e, x
        except:
            continue
    raise FileNotFoundError("Model files not found")

try:
    model, encoder, X_cols = load_model()
    model_loaded = True
except:
    model_loaded = False

# ── Constants ────────────────────────────────────────────────────
ZONES = ['Barisal','Bogra','Chittagonj','Cumilla','Dhaka',
         'Dinajpur','Faridpur','Jashore','Khulna','Mymensingh',
         'Rajshahi','Rangamati','Rangpur','Sylhet']

MONTHS = ['January','February','March','April','May','June',
          'July','August','September','October','November','December']

CROP_EMOJI = {
    'Aman': '🌾', 'Aush': '🌾', 'Boro': '🌾', 'Wheat': '🌿',
    'Jute': '🪢', 'Sugarcane': '🎋', 'Potato': '🥔', 'Tomato': '🍅',
    'Banana': '🍌', 'Mango': '🥭', 'Guava': '🍈', 'Pineapple': '🍍',
    'jackfruit': '🫐', 'papaya': '🍈', 'licchi': '🍒',
    'Soybean': '🫘', 'Red Lentil': '🫘', 'corn khorip-1': '🌽',
    'Corn(Robi)': '🌽', 'garlic': '🧄', 'Tula': '☁️',
}

def get_emoji(crop):
    for k, v in CROP_EMOJI.items():
        if k.lower() in crop.lower():
            return v
    return '🌱'

# ── Sidebar inputs ───────────────────────────────────────────────
with st.sidebar:
    st.markdown('<div style="padding: 8px 0 24px;"><span style="font-size:28px;">🌾</span><br><span style="font-family:\'Playfair Display\',serif;font-size:22px;font-weight:900;color:#e8b84b;">CropSense BD</span><br><span style="font-size:10px;letter-spacing:2px;color:rgba(253,246,227,0.4);">AI CROP ADVISOR</span></div>', unsafe_allow_html=True)

    st.markdown('<div class="section-div">Location & Time</div>', unsafe_allow_html=True)
    zone  = st.selectbox("Agricultural Zone", ZONES, index=0)
    month = st.selectbox("Month", MONTHS, index=6)
    week  = st.selectbox("Week", [1, 2, 3, 4], index=2)

    st.markdown('<div class="section-div">Weather Conditions</div>', unsafe_allow_html=True)
    rainfall = st.number_input("Rainfall (mm)",    min_value=0.0,   max_value=1000.0, value=111.7, step=0.1)
    temp     = st.number_input("Mean Temp (°C)",   min_value=-10.0, max_value=50.0,   value=28.5,  step=0.1)
    humidity = st.number_input("Humidity (%)",     min_value=0.0,   max_value=100.0,  value=88.4,  step=0.1)
    sunshine = st.number_input("Sunshine (hrs)",   min_value=0.0,   max_value=744.0,  value=23.3,  step=0.1)
    wind_dir = st.number_input("Wind Dir (deg)",   min_value=0.0,   max_value=360.0,  value=175.0, step=1.0)
    wind_spd = st.number_input("Wind Speed (km/h)",min_value=0.0,   max_value=200.0,  value=6.5,   step=0.1)

    st.markdown("<br>", unsafe_allow_html=True)
    predict_btn = st.button("⟶  Suggest Crop")

# ── Main content ─────────────────────────────────────────────────
st.markdown('<div class="main-title">Smart <em>Crop</em><br>Advisor</div>', unsafe_allow_html=True)
st.markdown('<div class="subtitle">Random Forest · 41 Crops · 14 Bangladesh Regions · 79.37% Accuracy</div>', unsafe_allow_html=True)

# Stats row
col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric("Model Accuracy", "79.37%")
with col2:
    st.metric("Total Crops", "41")
with col3:
    st.metric("Regions", "14")
with col4:
    st.metric("Training Samples", "3,973")

st.divider()

if not model_loaded:
    st.error("⚠️ Model files not found. Place `crop_model.pkl`, `label_encoder.pkl`, and `feature_columns.pkl` in the same folder.")

elif predict_btn:
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
            'WS (Km/hr)':        wind_spd
        }])
        sample  = pd.get_dummies(sample).reindex(columns=X_cols, fill_value=0)
        pred    = model.predict(sample)
        proba   = model.predict_proba(sample)[0]
        top_idx = proba.argsort()[-10:][::-1]

        crop       = encoder.inverse_transform(pred)[0]
        confidence = round(float(proba.max()) * 100, 1)
        top10      = [(encoder.inverse_transform([i])[0], round(float(proba[i])*100,1)) for i in top_idx]

    # Result
    emoji = get_emoji(crop)
    st.markdown(f"""
    <div class="result-box">
        <div class="result-label">Recommended Crop</div>
        <div class="result-crop">{emoji} {crop}</div>
        <div class="result-conf">Confidence: <span>{confidence}%</span></div>
    </div>
    """, unsafe_allow_html=True)

    # Charts
    col_a, col_b = st.columns([3, 2])

    with col_a:
        st.markdown("**Top 10 Crop Probabilities**")
        crops_list = [t[0] for t in top10]
        probs_list = [t[1] for t in top10]
        colors     = ['#e8b84b' if i == 0 else '#3d6b35' if i < 3 else '#7a4a2a' for i in range(len(crops_list))]

        fig = go.Figure(go.Bar(
            x=probs_list[::-1],
            y=crops_list[::-1],
            orientation='h',
            marker_color=colors[::-1],
            text=[f"{p}%" for p in probs_list[::-1]],
            textposition='outside',
        ))
        fig.update_layout(
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            font=dict(family='DM Mono', color='#2c1a0e', size=12),
            margin=dict(l=0, r=60, t=10, b=10),
            height=360,
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
        """)

else:
    st.info("👈 Fill in the weather conditions in the sidebar and click **Suggest Crop**")

    st.markdown("### How it works")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown("**1. Enter Conditions**\n\nSelect your agricultural zone, month, week and current weather data from the sidebar.")
    with col2:
        st.markdown("**2. AI Analysis**\n\nThe Random Forest model analyzes 9 features across 3,973 training samples.")
    with col3:
        st.markdown("**3. Get Recommendation**\n\nReceive the best crop suggestion with confidence score and top 10 alternatives.")
