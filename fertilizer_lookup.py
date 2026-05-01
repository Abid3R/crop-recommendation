# ================================================================
# fertilizer_lookup.py — BARC FRG-2024 fertilizer lookup
# ================================================================
import pandas as pd

# ----------------------------------------------------------------
# Fruit tree crops (lowercase) — used for routing to the right CSV
# ----------------------------------------------------------------
FRUIT_CROPS = {
    'mango', 'banana', 'guava', 'jackfruit', 'licchi', 'litchi',
    'papaya', 'pineapple', 'indian jujube', 'jamun',
    'coconut', 'orange', 'lemon', 'pomelo', 'watermelon',
    'aonla', 'bael', 'lotkon', 'longan', 'mandarin',
    'tamarind', 'dragon fruit', 'sugar beet',
    'sugarcane',        # BARC groups this with fruit trees in FRG-2024
}

# ----------------------------------------------------------------
# Crop name mapping: model-output label → BARC CSV crop name
#
# The deployed model was trained on 41 ORIGINAL labels; the research
# pipeline also works on 31 MERGED labels. Both naming schemes are
# listed below so the app works in either case.
#
# `True` as the value of PROXY_CROPS means "no direct BARC entry —
# using this crop as a closest-match proxy". The app surfaces this
# to the user so they know the fertilizer schedule is approximate.
# ----------------------------------------------------------------
CROP_NAME_MAP = {
    # ========== Original 41-label names ==========
    'Aman':             'T. Aman rice',
    'Boro':             'Boro rice',
    'Aush':             'Aus rice',
    'Wheat':            'Wheat',
    'Potato':           'Potato',
    'Tomato':           'Tomato (Winter)',
    'Brinjal(Robi)':    'Brinjal',
    'Brinjal(Khorip)':  'Brinjal',
    'Sugarcane':        'Sugarcane',
    'Red Lentil':       'Lentil',
    'Soybean':          'Soybean',
    'jute':             'Jute (C. capsularis)',
    'Tula':             'Cotton',
    'garlic':           'Garlic',
    'robi onion':       'Onion',
    'khorip onion':     'Onion',
    'robi green chilli': 'Chilli',
    'robi green chilli ': 'Chilli',           # trailing-space variant
    'khorip green chilli': 'Chilli',
    'masterd seed':     'Mustard',
    'Khorip Mug 1':     'Mungbean',
    'Robi Mug':         'Mungbean',
    'Badam robi':       'Groundnut',
    'Badam Kharip - 1': 'Groundnut',
    'Corn(Robi)':       'Maize',
    'corn khorip-1':    'Maize',

    # Cucurbits — no direct BARC entry, using Okra as closest proxy
    'Rabi Cucumber':           'Okra',
    'Kharif cucumber':         'Okra',
    'robi pumpkin Cucurbita':  'Okra',
    'khorip pumpkin Cucurbita': 'Okra',
    'robi lau (gourd)':        'Okra',
    'khorip lau (grourd)':     'Okra',
    'robi pointed gourd':      'Okra',
    'khorip pointed grourd':   'Okra',

    # Fruit trees (original labels)
    'Mango':         'Mango',
    'Banana':        'Banana',
    'Guava':         'Guava',
    'jackfruit':     'Jackfruit',
    'licchi':        'Litchi',
    'papaya':        'Papaya',
    'pineapple':     'Pineapple',
    'indian jujube': 'Jamun',

    # ========== Merged 31-label names (from research pipeline) ==========
    'Brinjal':       'Brinjal',
    'Corn':          'Maize',
    'Green Chilli':  'Chilli',
    'Lau Gourd':     'Okra',
    'Onion':         'Onion',
    'Cucumber':      'Okra',
    'Mug Bean':      'Mungbean',
    'Groundnut':     'Groundnut',
    'Pointed Gourd': 'Okra',
    'Pumpkin':       'Okra',
}

# Model-output labels whose BARC reference is a proxy (not exact).
# Keyed by the cleaned/normalized model-label (case-insensitive match done at runtime).
PROXY_LABELS = {
    'rabi cucumber', 'kharif cucumber', 'cucumber',
    'robi pumpkin cucurbita', 'khorip pumpkin cucurbita', 'pumpkin',
    'robi lau (gourd)', 'khorip lau (grourd)', 'lau gourd',
    'robi pointed gourd', 'khorip pointed grourd', 'pointed gourd',
    'indian jujube',           # Jamun is not the same species
}


# ----------------------------------------------------------------
# Utilities
# ----------------------------------------------------------------
def is_fruit_tree(crop_label: str) -> bool:
    """Return True if the crop is a fruit tree."""
    mapped = CROP_NAME_MAP.get(crop_label, crop_label)
    return (
        mapped.lower() in FRUIT_CROPS
        or crop_label.lower() in FRUIT_CROPS
    )


def parse_range(val):
    """Parse range strings like '59-116' → midpoint float."""
    if pd.isna(val) or val == '' or val == 0:
        return 0.0
    s = str(val).replace("'", "").strip()
    if '-' in s:
        try:
            parts = s.split('-')
            nums = [float(p) for p in parts if p.strip()]
            if len(nums) == 2:
                return round((nums[0] + nums[1]) / 2, 1)
            return float(parts[-1])
        except Exception:
            return 0.0
    try:
        return float(s)
    except Exception:
        return 0.0


def map_age_to_group(age):
    """Map a numeric tree age to a BARC age-group bucket label."""
    if age is None: return '>20'
    if age == 0:    return 'Before planting'
    if age <= 1:    return '0-1'
    if age <= 4:    return '2-4'
    if age <= 7:    return '5-7'
    if age <= 10:   return '8-10'
    if age <= 15:   return '11-15'
    if age <= 20:   return '16-20'
    return '>20'


# ----------------------------------------------------------------
# CSV loaders
# ----------------------------------------------------------------
def load_field_df(csv_path: str) -> pd.DataFrame:
    df = pd.read_csv(csv_path)
    df.columns = df.columns.str.strip()
    df['Crop'] = df['Crop'].str.strip()
    if 'Soil_Level' in df.columns:
        df['Soil_Level'] = df['Soil_Level'].astype(str).str.strip()
    return df


def load_fruit_df(csv_path: str) -> pd.DataFrame:
    df = pd.read_csv(csv_path)
    df.columns = df.columns.str.strip()
    df['Crop'] = df['Crop'].str.strip()
    if 'Age_Group_years' in df.columns:
        df['Age_Group_years'] = df['Age_Group_years'].astype(str).str.strip()
    return df


# ----------------------------------------------------------------
# Field crop fertilizer lookup
# ----------------------------------------------------------------
def get_field_fertilizer(crop_label, field_df, soil_level='Medium'):
    mapped = CROP_NAME_MAP.get(crop_label, crop_label)
    crop_df = field_df[field_df['Crop'].str.lower() == mapped.lower()]
    if crop_df.empty:
        # Loose partial match on first token
        first_token = mapped.lower().split()[0]
        crop_df = field_df[
            field_df['Crop'].str.lower().str.contains(first_token, na=False)
        ]
    if crop_df.empty:
        return None

    # Prefer the requested soil fertility level
    if 'Soil_Level' in crop_df.columns:
        sub = crop_df[crop_df['Soil_Level'].str.lower() == soil_level.lower()]
        row = sub.iloc[0] if not sub.empty else crop_df.iloc[0]
    else:
        row = crop_df.iloc[0]

    nutrient_cols = {
        'N_kg_ha':    'N (Nitrogen)',
        'P_kg_ha':    'P (Phosphorus)',
        'K_kg_ha':    'K (Potassium)',
        'S_kg_ha':    'S (Sulphur)',
        'Zn_kg_ha':   'Zn (Zinc)',
        'B_kg_ha':    'B (Boron)',
        'Mg_kg_ha':   'Mg (Magnesium)',
        'OF_t_per_ha': 'Organic Matter',
    }
    nutrients = {}
    for col, label in nutrient_cols.items():
        if col in row.index:
            val = parse_range(row[col])
            if val > 0:
                if col == 'OF_t_per_ha':
                    nutrients[label] = f"{val} t/ha"
                else:
                    nutrients[label] = val

    return {
        'crop':           mapped,
        'original_label': crop_label,
        'variety':        row.get('Variety_Group', '-'),
        'soil_level':     row.get('Soil_Level', soil_level),
        'unit':           'kg/ha',
        'nutrients':      nutrients,
        'type':           'field',
        'is_proxy':       crop_label.lower() in PROXY_LABELS,
    }


# ----------------------------------------------------------------
# Fruit tree fertilizer lookup
# ----------------------------------------------------------------
def get_fruit_fertilizer(crop_label, fruit_df, tree_age=None):
    mapped = CROP_NAME_MAP.get(crop_label, crop_label)
    crop_df = fruit_df[fruit_df['Crop'].str.lower() == mapped.lower()]
    if crop_df.empty:
        first_token = mapped.lower().split()[0]
        crop_df = fruit_df[
            fruit_df['Crop'].str.lower().str.contains(first_token, na=False)
        ]
    if crop_df.empty:
        return None

    age_group = map_age_to_group(tree_age)

    # Crops with split (basal + top-dressing) applications — sum them
    split_crops = ['banana', 'papaya', 'pineapple']
    is_split = any(sc in mapped.lower() for sc in split_crops)

    nutrient_cols = {
        'N_g_tree':    'N (Nitrogen)',
        'P_g_tree':    'P (Phosphorus)',
        'K_g_tree':    'K (Potassium)',
        'S_g_tree':    'S (Sulphur)',
        'Zn_g_tree':   'Zn (Zinc)',
        'B_g_tree':    'B (Boron)',
        'OF_kg_tree':  'Organic Matter',
    }

    if is_split:
        nutrients = {}
        for col, label in nutrient_cols.items():
            if col in crop_df.columns:
                total = pd.to_numeric(crop_df[col], errors='coerce').sum()
                if total > 0:
                    if col == 'OF_kg_tree':
                        nutrients[label] = f"{round(float(total),1)} kg/tree"
                    else:
                        nutrients[label] = round(float(total), 1)
        return {
            'crop':           mapped,
            'original_label': crop_label,
            'variety':        crop_df['Variety'].iloc[0] if 'Variety' in crop_df.columns else '-',
            'age_group':      'Total across all applications',
            'unit':           'g/tree',
            'nutrients':      nutrients,
            'type':           'fruit',
            'note':           'Total across basal + top-dressing applications',
            'is_proxy':       crop_label.lower() in PROXY_LABELS,
        }

    # Regular fruit trees — match by age group
    if 'Age_Group_years' in crop_df.columns:
        age_df = crop_df[crop_df['Age_Group_years'] == age_group]
        if age_df.empty:
            # Check if Age_Group_years actually contains soil fertility labels
            # (as it does for Sugarcane in FRG-2024: Optimum/Medium/Low/Very low)
            soil_levels = {'optimum', 'medium', 'low', 'very low'}
            col_vals = crop_df['Age_Group_years'].str.lower().unique()
            if any(v in soil_levels for v in col_vals):
                # Default to Medium fertility
                age_df = crop_df[crop_df['Age_Group_years'].str.lower() == 'medium']
                if age_df.empty:
                    age_df = crop_df.iloc[[0]]
            else:
                # Fallback to the most mature age-group entry
                valid = crop_df[crop_df['Age_Group_years'].str.match(r'^\d|^>', na=False)]
                age_df = valid.iloc[[-1]] if not valid.empty else crop_df.iloc[[-1]]
    else:
        age_df = crop_df

    row = age_df.iloc[0]
    nutrients = {}
    for col, label in nutrient_cols.items():
        if col in row.index:
            val = parse_range(row[col])
            if val > 0:
                if col == 'OF_kg_tree':
                    nutrients[label] = f"{val} kg/tree"
                else:
                    nutrients[label] = val

    return {
        'crop':           mapped,
        'original_label': crop_label,
        'variety':        row.get('Variety', '-'),
        'age_group':      age_group,
        'unit':           'g/tree',
        'nutrients':      nutrients,
        'type':           'fruit',
        'is_proxy':       crop_label.lower() in PROXY_LABELS,
    }


# ----------------------------------------------------------------
# Public entry point
# ----------------------------------------------------------------
def get_fertilizer(crop_label, field_df, fruit_df,
                   tree_age=None, soil_level='Medium'):
    """Return a structured fertilizer recommendation for a crop label."""
    if is_fruit_tree(crop_label):
        result = get_fruit_fertilizer(crop_label, fruit_df, tree_age)
    else:
        result = get_field_fertilizer(crop_label, field_df, soil_level)

    if result is None:
        return {
            'error': f'No fertilizer data available for "{crop_label}".',
            'type':  'none',
        }
    return result
