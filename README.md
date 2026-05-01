# 🌾 ফসল সাজেস্টার (Fasal Suggester)

**AI-Powered Crop & Fertilizer Recommendation for Bangladeshi Farmers**

A Bangla-language Streamlit application that recommends the best crop to grow based on local weather conditions and provides BARC FRG-2024 fertilizer doses for each recommendation.

## ✨ Features

- 🇧🇩 **Fully Bangla interface** — designed for Bangladeshi farmers
- 📍 **All 56+ districts** mapped to their Agro-Ecological Zones (AEZ) per BARC
- 🤖 **XGBoost ML model** trained on historical BAMIS weather data
- 🧪 **Official BARC FRG-2024 fertilizer schedules** — kg/ha for field crops, g/tree for fruit trees
- 🌍 **Soil-fertility level selector** (Optimum / Medium / Low / Very low)
- 🌳 **Age-group selector** for fruit trees
- 📱 **Mobile-friendly** with responsive design
- 💚 **Farmer-friendly UI** with large fonts, big buttons, generous whitespace

## 🚀 Quick start

```bash
git clone <your-repo-url>
cd fasal-suggester
pip install -r requirements.txt
streamlit run app.py
```

Then open the URL Streamlit prints (usually `http://localhost:8501`).

## 📁 Repository structure

```
fasal-suggester/
├── app.py                          # Main Streamlit app
├── aez_mapping.py                  # District → AEZ mapping (BARC FRG-2024)
├── fertilizer_lookup.py            # Fertilizer schedule lookup
├── requirements.txt                # Python dependencies
├── README.md                       # This file
│
├── crop_model.pkl                  # Trained XGBoost classifier
├── label_encoder.pkl               # Crop label encoder
├── feature_names.pkl               # Ordered feature list
│
├── field_crops_fertilizer.csv      # BARC field-crop fertilizer table
└── fruit_trees_fertilizer.csv      # BARC fruit-tree fertilizer table
```

## 🎨 Design

- **Color palette**: Deep green (`#1a5c2a`) sidebar gradient, cream background (`#f5f1ea`), warm earth-tone accents
- **Typography**: Hind Siliguri for Bangla rendering, with Noto Sans Bengali fallback
- **Layout**: Sidebar (district + AEZ + about) + main content (hero banner + form / results)

## 🧠 How it works

1. The user selects their **district** in the sidebar — the AEZ number and full name appear automatically.
2. They enter the current **weather conditions** (rainfall, temperature, humidity, sunshine, wind direction & speed) plus the target **month** and **week**.
3. Pressing **"ফসল সাজেস্ট করুন ✨"** runs the XGBoost model:
   - Builds a 32-feature vector matching the training schema (numeric weather + one-hot encoded zone + month).
   - Returns the most probable crop label with its confidence score.
4. The result page shows:
   - The crop name in **Bangla + English + emoji**.
   - **Pill badges** with the input context.
   - A **soil-level pill selector** (for field crops) or **age-group dropdown** (for fruit trees).
   - The **BARC fertilizer schedule** for that crop in a clean table (N, P, K, S, Zn, B, Organic Matter).

## 📊 Model

- **Algorithm**: XGBoost (gradient-boosted decision trees)
- **Features**: 6 weather variables + Week + one-hot encoded District + Month
- **Training data**: Historical BAMIS records across 14 districts
- **Accuracy**: 79.25% on held-out test set

## ⚠️ Disclaimer

These recommendations are an AI-generated advisory tool and should **supplement** — not replace — advice from local agricultural extension officers. Soil conditions, irrigation availability, and farmer experience all play a role in crop selection that weather data alone cannot capture.

সারের পরিমাণ প্রয়োগের আগে সর্বদা স্থানীয় কৃষি অফিসারের সাথে পরামর্শ করুন।

## 🙏 Acknowledgements

- **Bangladesh Agricultural Research Council (BARC)** — Fertilizer Recommendation Guide 2024
- **Bangladesh Meteorological Department** — BAMIS weather data
- **Department of Agricultural Extension (DAE)**

## 📜 License

MIT License — feel free to fork and adapt for your region.
