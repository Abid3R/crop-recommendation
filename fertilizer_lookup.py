# fertilizer_lookup.py
# Complete version for CropSense BD – includes nutrient-based lookup AND farmer-friendly recommendations

import pandas as pd
import re

# -------------------------------------------------------------------
# Mapping from model output crop names to exact names in the CSV files
# -------------------------------------------------------------------
CROP_NAME_MAP = {
    # Field crops
    'Aman': 'T. Aman rice',
    'Boro': 'Boro rice',
    'Aush': 'Aus rice',
    'Wheat': 'Wheat',
    'Maize': 'Maize',
    'Potato': 'Potato',
    'Tomato': 'Tomato (Winter)',
    'Brinjal(Robi)': 'Brinjal',
    'Brinjal(Khorip)': 'Brinjal',
    'Red Lentil': 'Lentil',
    'Mungbean': 'Mungbean',
    'Grasspea': 'Grasspea',
    'Mustard': 'Mustard',
    'Sugarcane': 'Sugarcane',
    'Jute': 'Jute (C. capsularis)',
    'Okra': 'Okra',
    'Onion': 'Onion',
    'Garlic': 'Garlic',
    'Chilli': 'Chilli',
    'Coriander': 'Coriander',
    'Turmeric': 'Turmeric',
    'Ginger': 'Ginger',
    'Sweet potato': 'Sweet potato',
    'Radish': 'Radish',
    'Cabbage': 'Cabbage',
    'Cauliflower': 'Cauliflower',
    'Brinjal': 'Brinjal',
    'Pointed gourd': 'Pointed Gourd',
    'Sweet gourd': 'Sweet Gourd',
    'Bitter gourd': 'Bitter Gourd',
    'Cucumber': 'Cucumber',
    'Pumpkin': 'Sweet Gourd',
    'Watermelon': 'Watermelon',
    'Musk melon': 'Netted melon',
    # Fruit trees
    'Banana': 'Banana',
    'Mango': 'Mango',
    'Jackfruit': 'Jackfruit',
    'Guava': 'Guava',
    'Papaya': 'Papaya',
    'Litchi': 'Litchi',
    'Pineapple': 'Pineapple',
    'Coconut': 'Coconut',
    'Lemon': 'Lemon',
    'Dragon fruit': 'Dragon fruit',
    'Strawberry': 'Strawberry',
    'Longan': 'Longan',
    'Cashew nut': 'Cashew nut',
    'Aonla': 'Aonla',
    'Jamun': 'Jamun',
    'Tamarind': 'Tamarind',
}

# -------------------------------------------------------------------
# Helper: parse range strings like "31-60" to midpoint float
# -------------------------------------------------------------------
def parse_range(value):
    """Convert a string like '31-60' or '0-1.3' to a float (midpoint)."""
    if pd.isna(value) or value == '' or value == '-':
        return None
    if isinstance(value, (int, float)):
        return float(value)
    s = str(value).strip()
    s = s.strip("'\"")
    if '-' in s:
        parts = re.split(r'\s*-\s*', s)
        if len(parts) == 2:
            try:
                low = float(parts[0])
                high = float(parts[1])
                return round((low + high) / 2, 1)
            except:
                pass
    try:
        return float(s)
    except:
        return None

# -------------------------------------------------------------------
# Load CSV files (with column name cleanup)
# -------------------------------------------------------------------
def load_field_df(path):
    df = pd.read_csv(path)
    df.columns = df.columns.str.strip()
    return df

def load_fruit_df(path):
    df = pd.read_csv(path)
    df.columns = df.columns.str.strip()
    return df

# -------------------------------------------------------------------
# Identify if a crop is a fruit tree (for unit handling)
# -------------------------------------------------------------------
def is_fruit_tree(crop_name):
    fruit_list = [
        'banana', 'mango', 'jackfruit', 'guava', 'papaya', 'litchi',
        'pineapple', 'coconut', 'lemon', 'dragon fruit', 'strawberry',
        'longan', 'cashew nut', 'aonla', 'jamun', 'tamarind',
        'pummelo', 'mandarin', 'sweet orange', 'satkara', 'golden apple',
        'burmese grape', 'wax apple', 'bael', 'wood apple', 'bullock\'s heart',
        'custard apple', 'velvet apple', 'fig', 'indian olive'
    ]
    return crop_name.lower() in fruit_list

# -------------------------------------------------------------------
# Map age in years to the age group string used in fruit CSV
# -------------------------------------------------------------------
def age_to_group(age):
    if age is None:
        return '>10'
    if age <= 1:
        return '0-1'
    elif age <= 4:
        return '2-4'
    elif age <= 7:
        return '5-7'
    elif age <= 10:
        return '8-10'
    elif age <= 15:
        return '11-15'
    elif age <= 20:
        return '16-20'
    else:
        return '>20'

# -------------------------------------------------------------------
# Main nutrient‑based lookup (returns N, P, K, etc. in kg/ha or g/tree)
# -------------------------------------------------------------------
def get_fertilizer(crop, field_df, fruit_df, tree_age=None, soil_level='Medium'):
    mapped_crop = CROP_NAME_MAP.get(crop, crop)

    if is_fruit_tree(mapped_crop):
        fruit_rows = fruit_df[fruit_df['Crop'].str.lower() == mapped_crop.lower()]
        if fruit_rows.empty:
            return {'error': f'No fruit data for "{crop}"'}
        age_group = age_to_group(tree_age)
        row = fruit_rows[fruit_rows['Age_Group_years'] == age_group]
        if row.empty:
            row = fruit_rows.iloc[0]
            age_group = row['Age_Group_years']
        else:
            row = row.iloc[0]
        nutrients = {}
        for nut, col in [
            ('N (g/tree)', 'N_g_tree'), ('P (g/tree)', 'P_g_tree'),
            ('K (g/tree)', 'K_g_tree'), ('S (g/tree)', 'S_g_tree'),
            ('Zn (g/tree)', 'Zn_g_tree'), ('B (g/tree)', 'B_g_tree'),
            ('OF (kg/tree)', 'OF_kg_tree')
        ]:
            val = parse_range(row.get(col))
            if val is not None:
                nutrients[nut] = val
        if not nutrients:
            return {'error': f'No nutrient values for {crop} (age {age_group})'}
        return {
            'type': 'fruit', 'unit': 'g/tree', 'nutrients': nutrients,
            'variety': row.get('Variety', '-'), 'age_group': age_group,
            'note': 'For mature trees; adjust based on canopy size.'
        }
    else:
        field_rows = field_df[field_df['Crop'].str.lower() == mapped_crop.lower()]
        if field_rows.empty:
            return {'error': f'No field crop data for "{crop}"'}
        row = field_rows[field_rows['Soil_Level'].str.lower() == soil_level.lower()]
        if row.empty:
            if 'Medium' in field_rows['Soil_Level'].values:
                row = field_rows[field_rows['Soil_Level'] == 'Medium'].iloc[0]
            else:
                row = field_rows.iloc[0]
        else:
            row = row.iloc[0]
        nutrients = {}
        for nut, col in [
            ('N (kg/ha)', 'N_kg_ha'), ('P (kg/ha)', 'P_kg_ha'),
            ('K (kg/ha)', 'K_kg_ha'), ('S (kg/ha)', 'S_kg_ha'),
            ('Zn (kg/ha)', 'Zn_kg_ha'), ('B (kg/ha)', 'B_kg_ha'),
            ('Mg (kg/ha)', 'Mg_kg_ha'), ('OF (t/ha)', 'OF_t_per_ha')
        ]:
            val = parse_range(row.get(col))
            if val is not None:
                nutrients[nut] = val
        if not nutrients:
            return {'error': f'No nutrient values for {crop} (soil {soil_level})'}
        return {
            'type': 'field', 'unit': 'kg/ha', 'nutrients': nutrients,
            'variety': row.get('Variety_Group', '-'), 'soil_level': soil_level,
            'note': 'Based on BARC FRG-2024 for medium soil fertility.'
        }

# -------------------------------------------------------------------
# Farmer‑friendly recommendation (converts nutrients to actual fertilizers,
# shows amount per decimal, and includes timing)
# -------------------------------------------------------------------
def get_farmer_fertilizer(crop, field_df, fruit_df, tree_age=None, soil_level='Medium'):
    """
    Returns a list of fertilizers with amount in kg/decimal and simple timing instructions.
    """
    # First get the nutrient-based recommendation
    fert = get_fertilizer(crop, field_df, fruit_df, tree_age, soil_level)
    if 'error' in fert:
        return {'error': fert['error']}
    
    # For fruit trees, we keep the per‑tree recommendation (easier for farmers)
    if fert['type'] == 'fruit':
        nutrients = fert['nutrients']
        items = []
        for name, amount in nutrients.items():
            if amount > 0:
                items.append({
                    'name': name.split('(')[0].strip(),  # "N" -> "N"
                    'amount': amount,
                    'unit': 'গ্রাম/গাছ',
                    'timing': 'বছরে দুবার – ফাল্গুন ও ভাদ্র মাসে প্রয়োগ করুন'
                })
        return items if items else {'error': 'No fertilizer data available for this fruit.'}
    
    # For field crops: convert from kg/ha to kg/decimal
    # 1 decimal = 40.5 m², 1 hectare = 247 decimals
    n = fert['nutrients'].get('N (kg/ha)', 0)
    p = fert['nutrients'].get('P (kg/ha)', 0)
    k = fert['nutrients'].get('K (kg/ha)', 0)
    s = fert['nutrients'].get('S (kg/ha)', 0)
    zn = fert['nutrients'].get('Zn (kg/ha)', 0)
    
    # Conversion factors: nutrient to fertilizer material
    # Urea (46% N): kg = N / 0.46
    # TSP (20% P): kg = P / 0.20
    # MOP (50% K): kg = K / 0.50
    # Gypsum (18% S): kg = S / 0.18
    # ZnSO4 (21% Zn): kg = Zn / 0.21
    
    urea_kg = n / 0.46 if n else 0
    tsp_kg  = p / 0.20 if p else 0
    mop_kg  = k / 0.50 if k else 0
    gypsum_kg = s / 0.18 if s else 0
    zinc_kg = zn / 0.21 if zn else 0
    
    # Convert to per decimal (divide by 247)
    def to_decimal(kg_ha):
        return round(kg_ha / 247, 2)
    
    recommendations = []
    
    if urea_kg > 0:
        urea_dec = to_decimal(urea_kg)
        recommendations.append({
            'name': 'ইউরিয়া (Urea)',
            'amount': urea_dec,
            'unit': 'কেজি',
            'timing': 'অর্ধেক জমি তৈরির সময়, বাকি অর্ধেক ১৫-২০ দিন পর উপরি প্রয়োগ'
        })
    if tsp_kg > 0:
        tsp_dec = to_decimal(tsp_kg)
        recommendations.append({
            'name': 'টিএসপি (TSP)',
            'amount': tsp_dec,
            'unit': 'কেজি',
            'timing': 'জমি তৈরির সময় মাটির সাথে ভালোভাবে মিশিয়ে দিন'
        })
    if mop_kg > 0:
        mop_dec = to_decimal(mop_kg)
        recommendations.append({
            'name': 'এমওপি (MOP)',
            'amount': mop_dec,
            'unit': 'কেজি',
            'timing': 'জমি তৈরির সময় প্রয়োগ করুন (হালকা দোআঁশ মাটিতে অর্ধেক পরে প্রয়োগ করতে পারেন)'
        })
    if gypsum_kg > 0:
        gypsum_dec = to_decimal(gypsum_kg)
        recommendations.append({
            'name': 'জিপসাম (Gypsum)',
            'amount': gypsum_dec,
            'unit': 'কেজি',
            'timing': 'জমি তৈরির সময় প্রয়োগ করুন'
        })
    if zinc_kg > 0:
        zinc_dec = to_decimal(zinc_kg)
        recommendations.append({
            'name': 'জিংক সালফেট (Zinc)',
            'amount': zinc_dec,
            'unit': 'কেজি',
            'timing': 'জমি তৈরির সময় প্রয়োগ করুন'
        })
    
    if not recommendations:
        return {'error': 'সারের পরিমাণ নির্ণয় করা সম্ভব হয়নি।'}
    
    return recommendations
