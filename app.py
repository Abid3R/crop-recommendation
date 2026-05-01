# ================================================================
# ফসল সাজেস্টার (Fasal Suggester)
# AI-Powered Crop & Fertilizer Recommendation for Bangladeshi Farmers
# Run: streamlit run app.py
# ================================================================
import os
import sys
import time
import joblib
import pandas as pd
import streamlit as st

# Make local imports work when run from any directory
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from aez_mapping import DISTRICT_TO_AEZ, AEZ_NAMES, get_aez, get_aez_name
from fertilizer_lookup import (
    load_field_df, load_fruit_df,
    get_fertilizer, is_fruit_tree,
)

# ----------------------------------------------------------------
# Page config (must be first Streamlit call)
# ----------------------------------------------------------------
st.set_page_config(
    page_title="ফসল সাজেস্টার",
    page_icon="🌾",
    layout="centered",
    initial_sidebar_state="expanded",
)

# ----------------------------------------------------------------
# Bangla translations
# ----------------------------------------------------------------
DISTRICT_BANGLA = {
    'Thakurgaon': 'ঠাকুরগাঁও', 'Panchagar': 'পঞ্চগড়', 'Dinajpur': 'দিনাজপুর',
    'Kurigram': 'কুড়িগ্রাম', 'Lalmonirhat': 'লালমনিরহাট',
    'Rangpur': 'রংপুর', 'Nilphamari': 'নীলফামারী', 'Gaibandha': 'গাইবান্ধা',
    'Bogra': 'বগুড়া', 'Bogura': 'বগুড়া', 'Joypurhat': 'জয়পুরহাট', 'Naogaon': 'নওগাঁ',
    'Natore': 'নাটোর',
    'Sirajganj': 'সিরাজগঞ্জ', 'Jamalpur': 'জামালপুর', 'Tangail': 'টাঙ্গাইল', 'Manikganj': 'মানিকগঞ্জ',
    'Mymensingh': 'ময়মনসিংহ', 'Kishoreganj': 'কিশোরগঞ্জ', 'Sherpur': 'শেরপুর', 'Netrokona': 'নেত্রকোণা',
    'Dhaka': 'ঢাকা', 'Narsingdi': 'নরসিংদী', 'Munshiganj': 'মুন্সিগঞ্জ', 'Gazipur': 'গাজীপুর',
    'Rajshahi': 'রাজশাহী', 'Chapainawabganj': 'চাঁপাইনবাবগঞ্জ', 'Pabna': 'পাবনা',
    'Kushtia': 'কুষ্টিয়া', 'Jashore': 'যশোর', 'Jhenaidah': 'ঝিনাইদহ', 'Faridpur': 'ফরিদপুর',
    'Khulna': 'খুলনা', 'Satkhira': 'সাতক্ষীরা', 'Bagerhat': 'বাগেরহাট',
    'Barisal': 'বরিশাল', 'Pirojpur': 'পিরোজপুর', 'Jhalokati': 'ঝালকাঠি', 'Barguna': 'বরগুনা',
    'Gopalganj': 'গোপালগঞ্জ', 'Madaripur': 'মাদারীপুর', 'Shariatpur': 'শরীয়তপুর',
    'Cumilla': 'কুমিল্লা', 'Brahmanbaria': 'ব্রাহ্মণবাড়িয়া', 'Chandpur': 'চাঁদপুর',
    'Sylhet': 'সিলেট', 'Moulvibazar': 'মৌলভীবাজার', 'Habiganj': 'হবিগঞ্জ', 'Sunamganj': 'সুনামগঞ্জ',
    'Chittagonj': 'চট্টগ্রাম', 'Chittagong': 'চট্টগ্রাম', 'Feni': 'ফেনী', 'Noakhali': 'নোয়াখালী',
    'Rangamati': 'রাঙ্গামাটি', 'Bandarban': 'বান্দরবান', 'Khagrachhari': 'খাগড়াছড়ি',
}

MONTHS = [
    ('January',   'জানুয়ারি'),  ('February', 'ফেব্রুয়ারি'), ('March',     'মার্চ'),
    ('April',     'এপ্রিল'),    ('May',      'মে'),         ('June',      'জুন'),
    ('July',      'জুলাই'),     ('August',   'আগস্ট'),      ('September', 'সেপ্টেম্বর'),
    ('October',   'অক্টোবর'),   ('November', 'নভেম্বর'),    ('December',  'ডিসেম্বর'),
]
MONTH_BN = dict(MONTHS)

# Crop emoji + Bangla name (covers the 41 model output classes)
CROP_INFO = {
    'Aman':                  ('🌾', 'আমন ধান'),
    'Aush':                  ('🌾', 'আউশ ধান'),
    'Boro':                  ('🌾', 'বোরো ধান'),
    'Wheat':                 ('🌿', 'গম'),
    'jute':                  ('🪢', 'পাট'),
    'Sugarcane':             ('🎋', 'আখ'),
    'Potato':                ('🥔', 'আলু'),
    'Tomato':                ('🍅', 'টমেটো'),
    'Brinjal(Robi)':         ('🍆', 'বেগুন (রবি)'),
    'Brinjal(Khorip)':       ('🍆', 'বেগুন (খরিপ)'),
    'Red Lentil':            ('🫘', 'মসুর ডাল'),
    'Soybean':               ('🫘', 'সয়াবিন'),
    'Robi Mug':              ('🫘', 'মুগ ডাল (রবি)'),
    'Khorip Mug 1':          ('🫘', 'মুগ ডাল (খরিপ)'),
    'Badam robi':            ('🥜', 'চীনাবাদাম (রবি)'),
    'Badam Kharip - 1':      ('🥜', 'চীনাবাদাম (খরিপ)'),
    'Corn(Robi)':            ('🌽', 'ভুট্টা (রবি)'),
    'corn khorip-1':         ('🌽', 'ভুট্টা (খরিপ)'),
    'masterd seed':          ('🌱', 'সরিষা'),
    'garlic':                ('🧄', 'রসুন'),
    'robi onion':            ('🧅', 'পেঁয়াজ (রবি)'),
    'khorip onion':          ('🧅', 'পেঁয়াজ (খরিপ)'),
    'robi green chilli':     ('🌶️', 'কাঁচা মরিচ (রবি)'),
    'robi green chilli ':    ('🌶️', 'কাঁচা মরিচ (রবি)'),
    'khorip green chilli':   ('🌶️', 'কাঁচা মরিচ (খরিপ)'),
    'Tula':                  ('☁️', 'তুলা'),
    'Rabi Cucumber':         ('🥒', 'শসা (রবি)'),
    'Kharif cucumber':       ('🥒', 'শসা (খরিপ)'),
    'robi lau (gourd)':      ('🥒', 'লাউ (রবি)'),
    'khorip lau (grourd)':   ('🥒', 'লাউ (খরিপ)'),
    'robi pumpkin Cucurbita': ('🎃', 'মিষ্টিকুমড়া (রবি)'),
    'khorip pumpkin Cucurbita': ('🎃', 'মিষ্টিকুমড়া (খরিপ)'),
    'robi pointed gourd':    ('🥒', 'পটল (রবি)'),
    'khorip pointed grourd': ('🥒', 'পটল (খরিপ)'),
    # Fruit trees
    'Mango':                 ('🥭', 'আম'),
    'Banana':                ('🍌', 'কলা'),
    'Guava':                 ('🍈', 'পেয়ারা'),
    'jackfruit':             ('🌳', 'কাঁঠাল'),
    'licchi':                ('🍒', 'লিচু'),
    'papaya':                ('🍈', 'পেঁপে'),
    'pineapple':             ('🍍', 'আনারস'),
    'indian jujube':         ('🟤', 'বরই'),
}

def crop_meta(label):
    if label in CROP_INFO:
        return CROP_INFO[label]
    # case-insensitive fallback
    lc = label.lower().strip()
    for k, v in CROP_INFO.items():
        if k.lower().strip() == lc:
            return v
    return ('🌱', label)


# ----------------------------------------------------------------
# CSS — recreates the design from the HTML prototype
# ----------------------------------------------------------------
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Hind+Siliguri:wght@300;400;500;600;700&display=swap');

html, body, [class*="css"], .stApp, .stMarkdown, button, input, select, textarea {
    font-family: 'Hind Siliguri', 'Noto Sans Bengali', sans-serif !important;
}

/* App base */
.stApp { background: #f5f1ea; }
#MainMenu, footer { visibility: hidden; }
[data-testid="stHeader"] { background: transparent; height: 0; }
[data-testid="stToolbar"] { display: none !important; }
.block-container { padding-top: 1rem !important; padding-bottom: 2rem; max-width: 920px; }

/* === Sidebar — dark green gradient === */
[data-testid="stSidebar"] > div {
    background: linear-gradient(180deg, #1a5c2a 0%, #2d7d3a 100%);
    padding-top: 1.5rem;
}
[data-testid="stSidebar"] * { color: #ffffff !important; }
[data-testid="stSidebar"] h1, [data-testid="stSidebar"] h2,
[data-testid="stSidebar"] h3 { color: #ffffff !important; }

/* Sidebar selectbox — closed state.
   We make the dropdown a clean WHITE pill with dark green text — easier to
   read against the dark green sidebar than a translucent variant, and avoids
   a long battle with BaseWeb's nested white backgrounds. */
[data-testid="stSidebar"] [data-baseweb="select"] > div {
    background-color: #ffffff !important;
    border: 1.5px solid rgba(255,255,255,0.45) !important;
    border-radius: 10px !important;
    box-shadow: 0 2px 6px rgba(0,0,0,0.08);
}
[data-testid="stSidebar"] [data-baseweb="select"] [role="combobox"],
[data-testid="stSidebar"] [data-baseweb="select"] input {
    color: #1a3d1f !important;
    -webkit-text-fill-color: #1a3d1f !important;
    font-weight: 600 !important;
    font-size: 0.95rem !important;
}
[data-testid="stSidebar"] [data-baseweb="select"] svg {
    color: #1a5c2a !important;
    fill: #1a5c2a !important;
}
/* Sidebar label */
[data-testid="stSidebar"] .stSelectbox label,
[data-testid="stSidebar"] label[data-testid="stWidgetLabel"] p,
[data-testid="stSidebar"] label[data-testid="stWidgetLabel"] {
    color: #ffffff !important;
    font-weight: 700 !important;
    font-size: 0.95rem !important;
    margin-bottom: 0.4rem !important;
}

/* AEZ badge */
.aez-badge {
    background: rgba(255,255,255,0.10);
    border: 1px solid rgba(255,255,255,0.22);
    border-radius: 12px;
    padding: 0.85rem 1rem;
    margin-top: 1rem;
}
.aez-num { font-size: 1.45rem; font-weight: 700; color: #d4f0a0; line-height: 1.1; }
.aez-name { font-size: 0.78rem; color: rgba(255,255,255,0.78); margin-top: 4px; line-height: 1.45; }

.sidebar-divider {
    border: none;
    border-top: 1px solid rgba(255,255,255,0.18);
    margin: 1.4rem 0;
}
.sidebar-about-title {
    font-weight: 600;
    color: #c8ebb0 !important;
    margin-bottom: 0.4rem;
    font-size: 0.92rem;
}
.sidebar-about-body {
    font-size: 0.84rem;
    color: rgba(255,255,255,0.78) !important;
    line-height: 1.75;
}

/* === Hero banner === */
.hero {
    background: linear-gradient(135deg, #1a5c2a 0%, #2d7d3a 55%, #4d9e42 100%);
    margin: -1rem -1rem 1.5rem -1rem;
    padding: 2rem 2rem;
    text-align: center;
    border-radius: 0 0 18px 18px;
    box-shadow: 0 4px 14px rgba(26,92,42,0.18);
}
.hero-title {
    color: #ffffff;
    font-size: 2.1rem;
    font-weight: 700;
    letter-spacing: -0.4px;
    margin: 0;
}
.hero-sub {
    color: #c0e8a0;
    font-size: 1rem;
    margin-top: 6px;
}

/* === Section titles === */
.section-title {
    color: #1a5c2a;
    font-size: 1.15rem;
    font-weight: 700;
    border-bottom: 2px solid #c8dfc0;
    padding-bottom: 0.4rem;
    margin: 1.4rem 0 1rem 0;
}

/* === Input labels & selects === */
.stSelectbox label, .stNumberInput label {
    color: #3a6b30 !important;
    font-weight: 600 !important;
    font-size: 0.92rem !important;
}
.stSelectbox [data-baseweb="select"] > div,
.stNumberInput input,
.stTextInput input {
    border-radius: 10px !important;
    border: 1.5px solid #d0e4c8 !important;
    background: #ffffff !important;
    color: #2a3a22 !important;
    font-size: 0.96rem !important;
}
.stNumberInput input:focus,
.stSelectbox [data-baseweb="select"] > div:focus-within {
    border-color: #2d7d3a !important;
    box-shadow: 0 0 0 2px rgba(45,125,58,0.15) !important;
}

/* === Big primary button === */
.stButton > button {
    width: 100%;
    background: linear-gradient(135deg, #1a5c2a, #3a9e48) !important;
    color: #ffffff !important;
    font-size: 1.25rem !important;
    font-weight: 700 !important;
    border: none !important;
    border-radius: 50px !important;
    padding: 0.9rem 1.5rem !important;
    box-shadow: 0 6px 22px rgba(26,92,42,0.30) !important;
    letter-spacing: 0.3px !important;
    transition: all 0.2s ease !important;
    margin-top: 0.5rem !important;
}
.stButton > button:hover {
    transform: translateY(-2px);
    box-shadow: 0 10px 30px rgba(26,92,42,0.42) !important;
}
/* Secondary (reset) button — outline style */
.reset-btn .stButton > button {
    background: #ffffff !important;
    color: #1a5c2a !important;
    border: 2px solid #1a5c2a !important;
    font-size: 1rem !important;
    font-weight: 600 !important;
    box-shadow: none !important;
    width: auto !important;
    padding: 0.55rem 1.6rem !important;
    margin: 0 auto !important;
    display: block !important;
}
.reset-btn .stButton > button:hover {
    background: #1a5c2a !important;
    color: #ffffff !important;
    transform: translateY(-1px);
}

/* === Result hero === */
.result-hero {
    background: linear-gradient(135deg, #1a5c2a, #3a9e48);
    border-radius: 22px;
    padding: 2rem 1.5rem;
    text-align: center;
    color: #ffffff;
    margin: 0.5rem 0 1.4rem 0;
    box-shadow: 0 8px 28px rgba(26,92,42,0.24);
}
.result-emoji { font-size: 4rem; line-height: 1; }
.result-name  { font-size: 2rem; font-weight: 700; margin-top: 0.4rem; color: #fff; }
.result-name-en { font-size: 0.92rem; opacity: 0.78; margin-top: 4px; color: #fff; }

/* === Context badges === */
.badges { display: flex; flex-wrap: wrap; gap: 8px; margin-bottom: 1.4rem; }
.badge {
    background: #e4f0da;
    color: #1a5c2a;
    border-radius: 20px;
    padding: 0.28rem 0.95rem;
    font-size: 0.85rem;
    font-weight: 600;
}

/* === Soil-level pill buttons === */
.soil-pill-row { display: flex; gap: 8px; flex-wrap: wrap; margin-bottom: 0.4rem; }
.soil-pill-label {
    color: #3a6b30 !important;
    font-weight: 600 !important;
    font-size: 0.95rem !important;
    margin-bottom: 0.5rem !important;
}
/* Streamlit radio styled as pills */
.stRadio > label > div { display: none !important; }  /* hide group label (we add our own) */
.stRadio [role="radiogroup"] {
    display: flex !important;
    gap: 8px !important;
    flex-wrap: wrap !important;
}
.stRadio [role="radiogroup"] label {
    background: #ffffff !important;
    border: 1.5px solid #c0d4b8 !important;
    border-radius: 50px !important;
    padding: 0.5rem 1.2rem !important;
    cursor: pointer;
    font-weight: 600 !important;
    transition: all 0.15s;
    color: #1a3d1f !important;          /* dark green text on white pill */
}
.stRadio [role="radiogroup"] label * {
    color: #1a3d1f !important;          /* override children too */
}
.stRadio [role="radiogroup"] label:hover {
    border-color: #1a7a30 !important;
    background: #f0f7ec !important;
}
.stRadio [role="radiogroup"] label:has(input:checked) {
    background: #1a7a30 !important;
    border-color: #1a7a30 !important;
}
.stRadio [role="radiogroup"] label:has(input:checked),
.stRadio [role="radiogroup"] label:has(input:checked) * {
    color: #ffffff !important;          /* white text on green selected pill */
}
.stRadio [role="radiogroup"] label > div:first-child { display: none !important; } /* hide circle */

/* === Fertilizer table === */
.fert-card {
    background: #ffffff;
    border-radius: 16px;
    overflow: hidden;
    box-shadow: 0 2px 12px rgba(0,0,0,0.07);
    margin-bottom: 1.2rem;
}
.fert-table { width: 100%; border-collapse: collapse; }
.fert-table th {
    background: #1a5c2a;
    color: #ffffff;
    padding: 0.75rem 1rem;
    text-align: left;
    font-size: 0.92rem;
    font-weight: 600;
}
.fert-table td {
    padding: 0.75rem 1rem;
    border-bottom: 1px solid #eef3ec;
    font-size: 0.93rem;
    color: #333;
}
.fert-table tr:nth-child(even) td { background: #f8fcf6; }
.fert-table tr:last-child td { border-bottom: none; }
.fert-value { font-weight: 700; color: #1a5c2a; }

/* === Info / warn boxes === */
.info-box {
    background: #e8f5e2;
    border: 1px solid #b8dca8;
    border-left: 4px solid #2d7d3a;
    border-radius: 10px;
    padding: 0.95rem 1.1rem;
    font-size: 0.92rem;
    color: #2a5c20;
    margin: 0.8rem 0 1rem;
    line-height: 1.6;
}
.warn-box {
    background: #fff8e1;
    border: 1px solid #ffe082;
    border-left: 4px solid #e8b84b;
    border-radius: 10px;
    padding: 0.95rem 1.1rem;
    font-size: 0.92rem;
    color: #7a5a00;
    margin: 0.8rem 0 1rem;
    line-height: 1.6;
}

/* === About card === */
.about-card {
    background: #ffffff;
    border-radius: 16px;
    border: 1px solid #dde8d5;
    padding: 1.2rem 1.5rem;
    font-size: 0.88rem;
    color: #555;
    line-height: 1.8;
    margin: 1.5rem 0;
}
.about-card-title {
    font-weight: 700;
    color: #1a5c2a;
    font-size: 0.96rem;
    margin-bottom: 0.5rem;
}

/* Mobile adjustments */
@media (max-width: 720px) {
    .hero-title { font-size: 1.6rem; }
    .result-emoji { font-size: 3rem; }
    .result-name  { font-size: 1.5rem; }
    .block-container { padding-left: 0.6rem; padding-right: 0.6rem; }
}
</style>
""", unsafe_allow_html=True)


# ----------------------------------------------------------------
# Load model + reference data (cached)
# ----------------------------------------------------------------
@st.cache_resource
def load_artifacts():
    base = os.path.dirname(os.path.abspath(__file__))
    candidates = [base, os.path.join(base, 'uploads'), '.']
    for path in candidates:
        if os.path.exists(os.path.join(path, 'crop_model.pkl')):
            base = path
            break
    model    = joblib.load(os.path.join(base, 'crop_model.pkl'))
    encoder  = joblib.load(os.path.join(base, 'label_encoder.pkl'))
    features = joblib.load(os.path.join(base, 'feature_names.pkl'))
    field_df = load_field_df(os.path.join(base, 'field_crops_fertilizer.csv'))
    fruit_df = load_fruit_df(os.path.join(base, 'fruit_trees_fertilizer.csv'))
    return model, encoder, features, field_df, fruit_df


try:
    model, encoder, features, field_df, fruit_df = load_artifacts()
except Exception as exc:
    st.error(f"⚠️ মডেল ফাইল লোড করা যায়নি: {exc}")
    st.info("নিশ্চিত করুন `crop_model.pkl`, `label_encoder.pkl`, `feature_names.pkl` এবং দুটি ফার্টিলাইজার CSV একই ফোল্ডারে আছে।")
    st.stop()


# ----------------------------------------------------------------
# Session state
# ----------------------------------------------------------------
if 'result' not in st.session_state:
    st.session_state.result = None
if 'inputs_snapshot' not in st.session_state:
    st.session_state.inputs_snapshot = None


# ================================================================
# SIDEBAR — district selector + AEZ badge + about
# ================================================================
with st.sidebar:
    st.markdown("<div style='font-size:1.5rem; font-weight:700; margin-bottom:0.2rem;'>🌾 ফসল সাজেস্টার</div>", unsafe_allow_html=True)
    st.markdown("<div style='font-size:0.8rem; color:#a8dba0 !important; margin-bottom:1.4rem; line-height:1.5;'>BARC FRG-2024 ভিত্তিক ফসল ও সার সুপারিশ</div>", unsafe_allow_html=True)

    districts = sorted(DISTRICT_TO_AEZ.keys())
    district_labels = [f"{DISTRICT_BANGLA.get(d, d)} ({d})" for d in districts]
    default_idx = districts.index('Dhaka') if 'Dhaka' in districts else 0

    sel_idx = st.selectbox(
        "📍 জেলা নির্বাচন করুন",
        options=range(len(districts)),
        format_func=lambda i: district_labels[i],
        index=default_idx,
    )
    district = districts[sel_idx]
    aez_num = get_aez(district)
    aez_name = get_aez_name(aez_num)

    st.markdown(f"""
    <div class="aez-badge">
        <div class="aez-num">AEZ — {aez_num}</div>
        <div class="aez-name">{aez_name}</div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown('<hr class="sidebar-divider">', unsafe_allow_html=True)
    st.markdown("""
    <div class="sidebar-about-title">🌿 এই অ্যাপ সম্পর্কে</div>
    <div class="sidebar-about-body">
        মেশিন লার্নিং ও BARC ডেটা ব্যবহার করে আপনার এলাকার জন্য সেরা ফসল ও সারের পরিমাণ সুপারিশ করা হয়।<br><br>
        <span style="color:#a8dba0 !important;">তথ্যসূত্র:</span><br>
        বাংলাদেশ কৃষি গবেষণা কাউন্সিল (BARC) | কৃষি সম্প্রসারণ অধিদপ্তর (DAE)
    </div>
    """, unsafe_allow_html=True)


# ================================================================
# HERO
# ================================================================
st.markdown("""
<div class="hero">
    <div class="hero-title">আপনার জমির জন্য সঠিক ফসল খুঁজুন</div>
    <div class="hero-sub">আবহাওয়ার তথ্য দিন — মুহূর্তেই পাবেন সেরা ফসল ও সারের পরামর্শ</div>
</div>
""", unsafe_allow_html=True)


# ================================================================
# MAIN — show input form OR result based on session state
# ================================================================
if st.session_state.result is None:

    # ---- Input form ----
    st.markdown('<div class="section-title">🌡️ আবহাওয়া ও সময়ের তথ্য দিন</div>', unsafe_allow_html=True)

    col_m, col_w = st.columns(2)
    with col_m:
        month_idx = st.selectbox(
            "📅 মাস",
            options=range(12),
            format_func=lambda i: MONTHS[i][1],
            index=6,  # July
        )
    with col_w:
        week = st.selectbox(
            "🗓️ সপ্তাহ",
            options=[1, 2, 3, 4],
            format_func=lambda w: f"{w} নম্বর সপ্তাহ",
            index=1,
        )
    month = MONTHS[month_idx][0]

    col_r, col_t, col_h = st.columns(3)
    with col_r:
        rainfall = st.number_input("🌧️ বৃষ্টিপাত (মিমি)", 0.0, 1000.0, 73.5, 0.5)
    with col_t:
        temp = st.number_input("🌡️ গড় তাপমাত্রা (°C)", -10.0, 50.0, 29.1, 0.1)
    with col_h:
        humidity = st.number_input("💧 আর্দ্রতা (%)", 0.0, 100.0, 83.0, 0.5)

    col_s, col_wd, col_ws = st.columns(3)
    with col_s:
        sunshine = st.number_input("☀️ সূর্যালোক (ঘণ্টা)", 0.0, 744.0, 32.0, 0.1)
    with col_wd:
        wind_dir = st.number_input("🧭 বাতাসের দিক (°)", 0.0, 360.0, 159.0, 1.0)
    with col_ws:
        wind_speed = st.number_input("💨 বাতাসের গতি (কিমি/ঘণ্টা)", 0.0, 200.0, 5.9, 0.1)

    st.markdown("<br>", unsafe_allow_html=True)
    submit = st.button("ফসল সাজেস্ট করুন ✨", key="predict_btn")

    # How-to-use card
    st.markdown("""
    <div class="about-card">
        <div class="about-card-title">📖 কীভাবে ব্যবহার করবেন?</div>
        ১. বাম সাইডবারে আপনার <b>জেলা</b> নির্বাচন করুন — AEZ স্বয়ংক্রিয়ভাবে দেখাবে।<br>
        ২. মাস, সপ্তাহ ও আবহাওয়ার তথ্য পূরণ করুন।<br>
        ৩. <b>"ফসল সাজেস্ট করুন"</b> বাটনে চাপুন।<br>
        ৪. সুপারিশকৃত ফসল ও সারের পরিমাণ দেখুন।
    </div>
    """, unsafe_allow_html=True)

    # ---- Predict ----
    if submit:
        with st.spinner(""):
            placeholder = st.empty()
            messages = [
                "আবহাওয়ার তথ্য বিশ্লেষণ করা হচ্ছে...",
                "এলাকা ও AEZ যাচাই করা হচ্ছে...",
                "মেশিন লার্নিং মডেল চালু হচ্ছে...",
                "সেরা ফসল নির্বাচন করা হচ্ছে...",
                "সার সুপারিশ প্রস্তুত করা হচ্ছে...",
            ]
            for i, msg in enumerate(messages):
                pct = int((i + 1) / len(messages) * 100)
                placeholder.markdown(f"""
                <div style="text-align:center; padding:1.5rem; background:#e8f5e2;
                            border-radius:14px; margin:1rem 0;">
                    <div style="font-size:2.2rem;">🌾</div>
                    <div style="color:#1a5c2a; font-weight:600; margin-top:0.5rem;
                                font-size:1.05rem;">{msg}</div>
                    <div style="margin-top:0.7rem; background:rgba(26,92,42,0.15);
                                border-radius:4px; height:6px; overflow:hidden;">
                        <div style="width:{pct}%; height:100%; background:#3a9e48;"></div>
                    </div>
                    <div style="color:#3a6b30; font-size:0.85rem; margin-top:6px;">{pct}%</div>
                </div>
                """, unsafe_allow_html=True)
                time.sleep(0.25)
            placeholder.empty()

            # Build feature vector
            sample = {f: 0 for f in features}
            weather_map = {
                'Rainfall (mm)':   rainfall,
                'Mean Temp. (*C)': temp,
                'RHmean (%)':      humidity,
                'SShr (hrs)':      sunshine,
                'WS (Km/hr)':      wind_speed,
                'WD (deg)':        wind_dir,
                'Week':            week,
            }
            for k, v in weather_map.items():
                if k in sample:
                    sample[k] = v
            zone_col  = f'Agricultural Zone_{district}'
            month_col = f'Month_{month}'
            if zone_col in sample:  sample[zone_col] = 1
            if month_col in sample: sample[month_col] = 1

            X_input = pd.DataFrame([sample])[features]
            proba = model.predict_proba(X_input)[0]
            top_i = int(proba.argmax())
            crop_label = encoder.inverse_transform([top_i])[0]
            confidence = round(float(proba[top_i]) * 100, 1)

            fert = get_fertilizer(crop_label, field_df, fruit_df, tree_age=10)

            st.session_state.result = {
                'crop': crop_label,
                'confidence': confidence,
                'is_fruit': is_fruit_tree(crop_label),
                'fert_field': fert if not is_fruit_tree(crop_label) else None,
            }
            st.session_state.inputs_snapshot = {
                'district': district, 'aez_num': aez_num,
                'month_bn': MONTHS[month_idx][1], 'week': week,
                'rainfall': rainfall, 'temp': temp, 'humidity': humidity,
                'sunshine': sunshine, 'wind_dir': wind_dir, 'wind_speed': wind_speed,
                'month_en': month,
            }
            st.rerun()

# ================================================================
# RESULT VIEW
# ================================================================
else:
    res = st.session_state.result
    snap = st.session_state.inputs_snapshot
    crop_label = res['crop']
    emoji, bn_name = crop_meta(crop_label)

    # Success banner
    st.markdown("""
    <div class="info-box">
        ✅ <b>বিশ্লেষণ সম্পন্ন!</b> আপনার এলাকা ও আবহাওয়ার উপর ভিত্তি করে সেরা ফসল নির্বাচন করা হয়েছে।
    </div>
    """, unsafe_allow_html=True)

    # Result hero
    st.markdown(f"""
    <div class="result-hero">
        <div class="result-emoji">{emoji}</div>
        <div class="result-name">{bn_name}</div>
        <div class="result-name-en">{crop_label} &nbsp;·&nbsp; বিশ্বাসযোগ্যতা: {res['confidence']}%</div>
    </div>
    """, unsafe_allow_html=True)

    # Context badges
    district_bn = DISTRICT_BANGLA.get(snap['district'], snap['district'])
    badges_html = (
        f'<span class="badge">📍 {district_bn}</span>'
        f'<span class="badge">🗺️ AEZ-{snap["aez_num"]}</span>'
        f'<span class="badge">📅 {snap["month_bn"]}, {snap["week"]} সপ্তাহ</span>'
        f'<span class="badge">🌡️ {snap["temp"]}°C</span>'
        f'<span class="badge">💧 {snap["humidity"]}%</span>'
        f'<span class="badge">🌧️ {snap["rainfall"]} মিমি</span>'
    )
    st.markdown(f'<div class="badges">{badges_html}</div>', unsafe_allow_html=True)

    # Fertilizer section
    st.markdown('<div class="section-title">🧪 প্রয়োজনীয় সারের পরিমাণ</div>', unsafe_allow_html=True)

    if res['is_fruit']:
        # Fruit tree — age-group selector
        age_groups_bn = {
            'Before planting': 'রোপণের আগে',
            '0-1':   '০-১ বছর',
            '2-4':   '২-৪ বছর',
            '5-7':   '৫-৭ বছর',
            '8-10':  '৮-১০ বছর',
            '11-15': '১১-১৫ বছর',
            '16-20': '১৬-২০ বছর',
            '>20':   '২০ বছরের বেশি',
        }
        st.markdown('<div class="soil-pill-label">🌳 গাছের বয়স / পর্যায় নির্বাচন করুন:</div>', unsafe_allow_html=True)
        age_choices = list(age_groups_bn.keys())
        age_default = age_choices.index('8-10') if '8-10' in age_choices else 0
        age_sel = st.selectbox(
            "গাছের বয়স",
            options=age_choices,
            format_func=lambda a: age_groups_bn.get(a, a),
            index=age_default,
            label_visibility="collapsed",
        )
        # Map Bangla age to numeric for lookup
        age_to_num = {'Before planting': 0, '0-1': 1, '2-4': 3, '5-7': 6,
                      '8-10': 10, '11-15': 13, '16-20': 18, '>20': 25}
        fert = get_fertilizer(crop_label, field_df, fruit_df,
                              tree_age=age_to_num.get(age_sel, 10))
    else:
        # Field crop — soil-level pills
        soil_options_bn = {
            'Optimum':  '✅ অপ্টিমাম',
            'Medium':   '🟡 মাঝারি',
            'Low':      '🟠 কম',
            'Very low': '🔴 খুব কম',
        }
        st.markdown('<div class="soil-pill-label">🌍 মাটির উর্বরতা স্তর নির্বাচন করুন:</div>', unsafe_allow_html=True)
        soil_sel = st.radio(
            "মাটির স্তর",
            options=list(soil_options_bn.keys()),
            format_func=lambda s: soil_options_bn[s],
            index=1,
            horizontal=True,
            label_visibility="collapsed",
        )
        fert = get_fertilizer(crop_label, field_df, fruit_df, soil_level=soil_sel)

    # Render fertilizer table
    if 'error' in fert:
        st.markdown(f'<div class="warn-box">⚠️ {fert["error"]} — দয়া করে স্থানীয় কৃষি অফিসের সাথে যোগাযোগ করুন।</div>',
                    unsafe_allow_html=True)
    else:
        nutrients = fert.get('nutrients', {}) or {}
        # Bangla labels for nutrients
        bn_nutrients = {
            'N (Nitrogen)':   'নাইট্রোজেন (N)',
            'P (Phosphorus)': 'ফসফরাস (P)',
            'K (Potassium)':  'পটাশিয়াম (K)',
            'S (Sulphur)':    'সালফার (S)',
            'Zn (Zinc)':      'জিঙ্ক (Zn)',
            'B (Boron)':      'বোরন (B)',
            'Mg (Magnesium)': 'ম্যাগনেসিয়াম (Mg)',
            'Organic Matter': 'জৈব সার',
        }
        unit_default = fert.get('unit', '')
        unit_bn = 'কেজি/হেক্টর' if unit_default == 'kg/ha' else (
                  'গ্রাম/গাছ' if unit_default == 'g/tree' else unit_default)

        if nutrients:
            rows_html = ""
            for raw_name, val in nutrients.items():
                bn_label = bn_nutrients.get(raw_name, raw_name)
                # Organic Matter values may include their own unit suffix
                if isinstance(val, str) and any(u in val for u in ['t/ha', 'kg/tree']):
                    amount, unit_label = val.rsplit(' ', 1)
                    unit_label_bn = ('টন/হেক্টর' if unit_label == 't/ha'
                                     else 'কেজি/গাছ' if unit_label == 'kg/tree'
                                     else unit_label)
                else:
                    amount = str(val)
                    unit_label_bn = unit_bn
                rows_html += (
                    f'<tr><td>{bn_label}</td>'
                    f'<td class="fert-value">{amount}</td>'
                    f'<td>{unit_label_bn}</td></tr>'
                )
            variety = fert.get('variety', '-')
            meta_line = f'<b>জাত:</b> {variety}'
            if not res['is_fruit']:
                soil_bn_map = {'Optimum':'অপ্টিমাম', 'Medium':'মাঝারি',
                               'Low':'কম', 'Very low':'খুব কম'}
                meta_line += f' &nbsp;|&nbsp; <b>মাটির স্তর:</b> {soil_bn_map.get(fert.get("soil_level","Medium"), fert.get("soil_level","Medium"))}'
            else:
                meta_line += f' &nbsp;|&nbsp; <b>বয়সের গ্রুপ:</b> {age_groups_bn.get(fert.get("age_group", "8-10"), fert.get("age_group", "8-10"))}'
            if fert.get('is_proxy'):
                meta_line += ' &nbsp;|&nbsp; <i>(কাছাকাছি ফসলের তথ্য দেখানো হচ্ছে)</i>'

            st.markdown(f"""
            <div class="info-box" style="font-size:0.88rem; margin-bottom:0.7rem;">
                {meta_line}
            </div>
            <div class="fert-card">
              <table class="fert-table">
                <thead>
                  <tr><th>সারের নাম</th><th>পরিমাণ</th><th>একক</th></tr>
                </thead>
                <tbody>{rows_html}</tbody>
              </table>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown('<div class="warn-box">⚠️ এই ফসলের জন্য পুষ্টির ডেটা পাওয়া যায়নি।</div>',
                        unsafe_allow_html=True)

    # Advisory note
    st.markdown("""
    <div class="warn-box">
        💡 <b>পরামর্শ:</b> সার প্রয়োগের আগে স্থানীয় কৃষি অফিসারের সাথে পরামর্শ করুন।
        মাটি পরীক্ষা করালে আরও সঠিক ফলাফল পাওয়া যাবে।
    </div>
    """, unsafe_allow_html=True)

    # Reset button (centered, outline style)
    st.markdown('<div class="reset-btn">', unsafe_allow_html=True)
    if st.button("🔄 আবার নতুন করে চেষ্টা করুন", key="reset_btn"):
        st.session_state.result = None
        st.session_state.inputs_snapshot = None
        st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

    # About card at the bottom
    st.markdown("""
    <div class="about-card">
        <div class="about-card-title">📖 এই অ্যাপ সম্পর্কে</div>
        এই অ্যাপটি <b>BARC FRG-2024</b> ডেটা ও মেশিন লার্নিং মডেলের উপর ভিত্তি করে তৈরি।
        আবহাওয়ার তথ্য ও AEZ ডেটা বিশ্লেষণ করে সর্বোত্তম ফসল ও সারের সুপারিশ দেওয়া হয়।
        <br><br>
        <b>তথ্যসূত্র:</b> বাংলাদেশ কৃষি গবেষণা কাউন্সিল (BARC) | কৃষি সম্প্রসারণ অধিদপ্তর (DAE)
    </div>
    """, unsafe_allow_html=True)
