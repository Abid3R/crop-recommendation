# ================================================================
# fertilizer_lookup.py - Fertilizer lookup from BARC FRG-2024
# ================================================================
import pandas as pd
import re

# Fruit tree crops set (lowercase)
FRUIT_CROPS = {
    'mango', 'banana', 'guava', 'jackfruit', 'licchi', 'litchi',
    'papaya', 'pineapple', 'indian jujube', 'coconut', 'orange',
    'lemon', 'pomelo', 'watermelon', 'sugarcane'
}

# Crop name mapping: weather dataset label → fertilizer dataset crop name
CROP_NAME_MAP = {
    # Field crops
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
    'robi green chilli ': 'Chilli',
    'khorip green chilli': 'Chilli',
    'masterd seed':     'Mustard',
    'Khorip Mug 1':     'Mungbean',
    'Robi Mug':         'Mungbean',
    'Badam robi':       'Groundnut',
    'Badam Kharip - 1': 'Groundnut',
    'Corn(Robi)':       'Maize',
    'corn khorip-1':    'Maize',
    'Rabi Cucumber':    'Okra',       # closest match
    'Kharif cucumber':  'Okra',
    'robi pumpkin Cucurbita':   'Okra',
    'khorip pumpkin Cucurbita': 'Okra',
    'robi lau (gourd)':         'Okra',
    'khorip lau (grourd)':      'Okra',
    'robi pointed gourd':       'Okra',
    'khorip pointed grourd':    'Okra',
    # Fruit trees
    'Mango':        'Mango',
    'Banana':       'Banana',
    'Guava':        'Guava',
    'jackfruit':    'Jackfruit',
    'licchi':       'Litchi',
    'papaya':       'Papaya',
    'pineapple':    'Pineapple',
    'indian jujube':'Jamun',
}

def is_fruit_tree(crop_label):
    mapped = CROP_NAME_MAP.get(crop_label, crop_label)
    return mapped.lower() in FRUIT_CROPS or crop_label.lower() in FRUIT_CROPS

def parse_range(val):
    """Parse range values like '''59-116 → take midpoint."""
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
        except:
            return 0.0
    try:
        return float(s)
    except:
        return 0.0

def map_age_to_group(age):
    if age is None: return '>20'
    if age == 0:    return 'Before planting'
    if age <= 1:    return '0-1'
    if age <= 4:    return '2-4'
    if age <= 7:    return '5-7'
    if age <= 10:   return '8-10'
    if age <= 15:   return '11-15'
    if age <= 20:   return '16-20'
    return '>20'

def load_field_df(csv_path):
    df = pd.read_csv(csv_path)
    df.columns = df.columns.str.strip()
    df['Crop'] = df['Crop'].str.strip()
    if 'Soil_Level' in df.columns:
        df['Soil_Level'] = df['Soil_Level'].str.strip()
    return df

def load_fruit_df(csv_path):
    df = pd.read_csv(csv_path)
    df.columns = df.columns.str.strip()
    df['Crop'] = df['Crop'].str.strip()
    if 'Age_Group_years' in df.columns:
        df['Age_Group_years'] = df['Age_Group_years'].str.strip()
    return df

def get_field_fertilizer(crop_label, field_df, soil_level='Medium'):
    mapped = CROP_NAME_MAP.get(crop_label, crop_label)
    crop_df = field_df[field_df['Crop'].str.lower() == mapped.lower()]
    if crop_df.empty:
        # Partial match
        crop_df = field_df[field_df['Crop'].str.lower().str.contains(
            mapped.lower().split()[0], na=False)]
    if crop_df.empty:
        return None

    # Filter soil level
    if 'Soil_Level' in crop_df.columns:
        med = crop_df[crop_df['Soil_Level'].str.lower() == soil_level.lower()]
        row = med.iloc[0] if not med.empty else crop_df.iloc[0]
    else:
        row = crop_df.iloc[0]

    nutrients = {}
    cols = {
        'N_kg_ha': 'N (kg/ha)', 'P_kg_ha': 'P (kg/ha)',
        'K_kg_ha': 'K (kg/ha)', 'S_kg_ha': 'S (kg/ha)',
        'Zn_kg_ha': 'Zn (kg/ha)', 'B_kg_ha': 'B (kg/ha)',
        'Mg_kg_ha': 'Mg (kg/ha)', 'OF_t_per_ha': 'Organic Matter (t/ha)',
    }
    for col, label in cols.items():
        if col in row.index:
            val = parse_range(row[col])
            if val > 0:
                nutrients[label] = val

    return {
        'crop': mapped,
        'original_label': crop_label,
        'variety': row.get('Variety_Group', '-'),
        'soil_level': row.get('Soil_Level', soil_level),
        'unit': 'kg/ha',
        'nutrients': nutrients,
        'type': 'field',
    }

def get_fruit_fertilizer(crop_label, fruit_df, tree_age=None):
    mapped = CROP_NAME_MAP.get(crop_label, crop_label)
    crop_df = fruit_df[fruit_df['Crop'].str.lower() == mapped.lower()]
    if crop_df.empty:
        crop_df = fruit_df[fruit_df['Crop'].str.lower().str.contains(
            mapped.lower().split()[0], na=False)]
    if crop_df.empty:
        return None

    age_group = map_age_to_group(tree_age)
    split_crops = ['banana', 'papaya', 'pineapple']
    is_split = any(sc in mapped.lower() for sc in split_crops)

    cols = {
        'N_g_tree': 'N (g/tree)', 'P_g_tree': 'P (g/tree)',
        'K_g_tree': 'K (g/tree)', 'S_g_tree': 'S (g/tree)',
        'Zn_g_tree': 'Zn (g/tree)', 'B_g_tree': 'B (g/tree)',
        'OF_kg_tree': 'Organic Matter (kg/tree)',
    }

    if is_split:
        # Sum all rows for total
        nutrients = {}
        for col, label in cols.items():
            if col in crop_df.columns:
                total = pd.to_numeric(crop_df[col], errors='coerce').sum()
                if total > 0:
                    nutrients[label] = round(total, 1)
        return {
            'crop': mapped, 'original_label': crop_label,
            'variety': crop_df['Variety'].iloc[0] if 'Variety' in crop_df.columns else '-',
            'age_group': 'Total (all applications)', 'unit': 'g/tree',
            'nutrients': nutrients, 'type': 'fruit',
            'note': 'Total across all split applications (basal + top dressing)',
        }
    else:
        # Match age group
        if 'Age_Group_years' in crop_df.columns:
            age_df = crop_df[crop_df['Age_Group_years'] == age_group]
            if age_df.empty:
                # fallback to most mature
                valid = crop_df[crop_df['Age_Group_years'].str.match(r'^\d|^>', na=False)]
                age_df = valid.iloc[[-1]] if not valid.empty else crop_df.iloc[[-1]]
        else:
            age_df = crop_df

        row = age_df.iloc[0]
        nutrients = {}
        for col, label in cols.items():
            if col in row.index:
                val = parse_range(row[col])
                if val > 0:
                    nutrients[label] = val
        return {
            'crop': mapped, 'original_label': crop_label,
            'variety': row.get('Variety', '-'),
            'age_group': age_group, 'unit': 'g/tree',
            'nutrients': nutrients, 'type': 'fruit',
        }

def get_fertilizer(crop_label, field_df, fruit_df, tree_age=None, soil_level='Medium'):
    if is_fruit_tree(crop_label):
        result = get_fruit_fertilizer(crop_label, fruit_df, tree_age)
    else:
        result = get_field_fertilizer(crop_label, field_df, soil_level)
    if result is None:
        return {'error': f'No fertilizer data available for {crop_label}', 'type': 'none'}
    return result
