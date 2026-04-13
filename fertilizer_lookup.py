# fertilizer_lookup.py
# Complete working version for CropSense BD

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
    'Tomato': 'Tomato (Winter)',
    'Brinjal': 'Brinjal',
    'Pointed gourd': 'Pointed Gourd',
    'Sweet gourd': 'Sweet Gourd',
    'Bitter gourd': 'Bitter Gourd',
    'Cucumber': 'Cucumber',
    'Pumpkin': 'Sweet Gourd',
    'Watermelon': 'Watermelon',
    'Musk melon': 'Netted melon',
    # Fruit trees (as they appear in fruit CSV)
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
    # Remove any extra quotes or hidden characters
    s = s.strip("'\"")
    # Handle ranges like "31-60" or "31 - 60"
    if '-' in s:
        parts = re.split(r'\s*-\s*', s)
        if len(parts) == 2:
            try:
                low = float(parts[0])
                high = float(parts[1])
                return round((low + high) / 2, 1)
            except:
                pass
    # Try direct conversion
    try:
        return float(s)
    except:
        return None


# -------------------------------------------------------------------
# Load CSV files (with column name cleanup)
# -------------------------------------------------------------------
def load_field_df(path):
    df = pd.read_csv(path)
    # Strip whitespace from column names
    df.columns = df.columns.str.strip()
    # Ensure numeric columns are treated as string for range parsing
    return df

def load_fruit_df(path):
    df = pd.read_csv(path)
    df.columns = df.columns.str.strip()
    return df


# -------------------------------------------------------------------
# Identify if a crop is a fruit tree (for unit display)
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
        return '>10'   # default mature
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
# Main function: get fertilizer recommendation
# -------------------------------------------------------------------
def get_fertilizer(crop, field_df, fruit_df, tree_age=None, soil_level='Medium'):
    """
    Returns a dictionary with fertilizer recommendation.
    
    Parameters:
        crop: str - name from model output (e.g., 'Aman')
        field_df: DataFrame - field crops CSV
        fruit_df: DataFrame - fruit trees CSV
        tree_age: int - age of fruit tree in years (if fruit)
        soil_level: str - 'Optimum', 'Medium', 'Low', 'Very low'
    
    Returns:
        dict with keys: type, unit, nutrients, variety, soil_level/age_group, note
        or {'error': message} if not found
    """
    # Map to CSV crop name
    mapped_crop = CROP_NAME_MAP.get(crop, crop)
    
    # Determine if fruit
    if is_fruit_tree(mapped_crop):
        # Filter fruit dataset
        fruit_rows = fruit_df[fruit_df['Crop'].str.lower() == mapped_crop.lower()]
        if fruit_rows.empty:
            return {'error': f'No fruit data for "{crop}"'}
        
        # Select age group
        age_group = age_to_group(tree_age)
        row = fruit_rows[fruit_rows['Age_Group_years'] == age_group]
        if row.empty:
            # Fallback to first available age group
            row = fruit_rows.iloc[0]
            age_group = row['Age_Group_years']
        else:
            row = row.iloc[0]
        
        # Extract nutrients
        nutrients = {}
        for nut, col in [
            ('N (g/tree)', 'N_g_tree'),
            ('P (g/tree)', 'P_g_tree'),
            ('K (g/tree)', 'K_g_tree'),
            ('S (g/tree)', 'S_g_tree'),
            ('Zn (g/tree)', 'Zn_g_tree'),
            ('B (g/tree)', 'B_g_tree'),
            ('OF (kg/tree)', 'OF_kg_tree')
        ]:
            val = parse_range(row.get(col))
            if val is not None:
                nutrients[nut] = val
        
        if not nutrients:
            return {'error': f'No nutrient values for {crop} (age {age_group})'}
        
        return {
            'type': 'fruit',
            'unit': 'g/tree',
            'nutrients': nutrients,
            'variety': row.get('Variety', '-'),
            'age_group': age_group,
            'note': 'For mature trees; adjust based on canopy size.'
        }
    
    else:
        # Field crop
        field_rows = field_df[field_df['Crop'].str.lower() == mapped_crop.lower()]
        if field_rows.empty:
            return {'error': f'No field crop data for "{crop}"'}
        
        # Select row by soil level
        row = field_rows[field_rows['Soil_Level'].str.lower() == soil_level.lower()]
        if row.empty:
            # Fallback to any row (prefer Medium if exists)
            if 'Medium' in field_rows['Soil_Level'].values:
                row = field_rows[field_rows['Soil_Level'] == 'Medium'].iloc[0]
            else:
                row = field_rows.iloc[0]
        else:
            row = row.iloc[0]
        
        # Extract nutrients
        nutrients = {}
        for nut, col in [
            ('N (kg/ha)', 'N_kg_ha'),
            ('P (kg/ha)', 'P_kg_ha'),
            ('K (kg/ha)', 'K_kg_ha'),
            ('S (kg/ha)', 'S_kg_ha'),
            ('Zn (kg/ha)', 'Zn_kg_ha'),
            ('B (kg/ha)', 'B_kg_ha'),
            ('Mg (kg/ha)', 'Mg_kg_ha'),
            ('OF (t/ha)', 'OF_t_per_ha')
        ]:
            val = parse_range(row.get(col))
            if val is not None:
                nutrients[nut] = val
        
        if not nutrients:
            return {'error': f'No nutrient values for {crop} (soil {soil_level})'}
        
        return {
            'type': 'field',
            'unit': 'kg/ha',
            'nutrients': nutrients,
            'variety': row.get('Variety_Group', '-'),
            'soil_level': soil_level,
            'note': 'Based on BARC FRG-2024 for medium soil fertility.'
        }
