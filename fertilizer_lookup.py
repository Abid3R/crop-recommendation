import pandas as pd
import re

# Mapping from model output crop names to CSV crop names
CROP_NAME_MAP = {
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
    'Banana': 'Banana',
    'Mango': 'Mango',
    'Jackfruit': 'Jackfruit',
    'Guava': 'Guava',
    'Papaya': 'Papaya',
    'Litchi': 'Litchi',
    'Pineapple': 'Pineapple',
    'Coconut': 'Coconut',
    # Add more as needed
}

def parse_range(value):
    """Convert a string like '31-60' or '0-1.3' to a float (midpoint)."""
    if pd.isna(value) or value == '' or value == '-':
        return None
    if isinstance(value, (int, float)):
        return float(value)
    value = str(value).strip()
    # Check if it's a range like '31-60'
    if '-' in value:
        parts = value.split('-')
        try:
            low = float(parts[0])
            high = float(parts[1])
            return round((low + high) / 2, 1)
        except:
            return None
    # Otherwise try direct conversion
    try:
        return float(value)
    except:
        return None

def load_field_df(path):
    """Load field crops CSV and clean column names."""
    df = pd.read_csv(path)
    # Strip any leading/trailing spaces from column names
    df.columns = df.columns.str.strip()
    return df

def load_fruit_df(path):
    """Load fruit trees CSV and clean column names."""
    df = pd.read_csv(path)
    df.columns = df.columns.str.strip()
    return df

def is_fruit_tree(crop_name):
    """Determine if crop is a fruit tree (for unit handling)."""
    # List of fruit crops from your fruit CSV (case-insensitive)
    fruits = ['mango', 'banana', 'guava', 'jackfruit', 'papaya', 'litchi', 
              'pineapple', 'coconut', 'pummelo', 'mandarin', 'lemon', 
              'dragon fruit', 'strawberry', 'longan', 'cashew nut']
    return crop_name.lower() in fruits

def get_fertilizer(crop, field_df, fruit_df, tree_age=None, soil_level='Medium'):
    """
    Return fertilizer recommendation for a given crop.
    
    Parameters:
        crop (str): crop name (model output, e.g., 'Aman')
        field_df (DataFrame): field crops CSV
        fruit_df (DataFrame): fruit trees CSV
        tree_age (int): age of fruit tree in years (if fruit)
        soil_level (str): 'Optimum', 'Medium', 'Low', 'Very low'
    
    Returns:
        dict with keys: type, unit, nutrients, variety, soil_level, age_group, note
    """
    # Map crop name to the one used in CSV
    mapped_crop = CROP_NAME_MAP.get(crop, crop)
    
    # Check if it's a fruit tree
    if is_fruit_tree(mapped_crop):
        # For fruit trees, filter by crop and age group
        fruit_rows = fruit_df[fruit_df['Crop'].str.lower() == mapped_crop.lower()]
        if fruit_rows.empty:
            return {'error': f'No data for {crop}'}
        
        # Determine age group
        if tree_age is None:
            age_group = '>10'  # default mature
        else:
            if tree_age <= 1:
                age_group = '0-1'
            elif tree_age <= 4:
                age_group = '2-4'
            elif tree_age <= 7:
                age_group = '5-7'
            elif tree_age <= 10:
                age_group = '8-10'
            elif tree_age <= 15:
                age_group = '11-15'
            elif tree_age <= 20:
                age_group = '16-20'
            else:
                age_group = '>20'
        
        # Find row matching age group (exact string match)
        row = fruit_rows[fruit_rows['Age_Group_years'] == age_group]
        if row.empty:
            row = fruit_rows.iloc[0]  # fallback to first row
        
        row = row.iloc[0]
        nutrients = {
            'N (g/tree)': parse_range(row.get('N_g_tree')),
            'P (g/tree)': parse_range(row.get('P_g_tree')),
            'K (g/tree)': parse_range(row.get('K_g_tree')),
            'S (g/tree)': parse_range(row.get('S_g_tree')),
            'Zn (g/tree)': parse_range(row.get('Zn_g_tree')),
            'B (g/tree)': parse_range(row.get('B_g_tree')),
            'OF (kg/tree)': parse_range(row.get('OF_kg_tree')),
        }
        # Remove None values
        nutrients = {k: v for k, v in nutrients.items() if v is not None}
        
        return {
            'type': 'fruit',
            'unit': 'g/tree',
            'nutrients': nutrients,
            'variety': row.get('Variety', '-'),
            'age_group': age_group,
            'note': 'For mature trees, adjust based on canopy size.'
        }
    
    else:
        # Field crop
        # Filter by crop and soil level (case-insensitive)
        field_rows = field_df[field_df['Crop'].str.lower() == mapped_crop.lower()]
        if field_rows.empty:
            return {'error': f'No fertilizer data for {crop}'}
        
        # Choose the row with the specified soil level (case-insensitive)
        row = field_rows[field_rows['Soil_Level'].str.lower() == soil_level.lower()]
        if row.empty:
            # Fallback to first row (usually Medium or Optimum)
            row = field_rows.iloc[0]
        else:
            row = row.iloc[0]
        
        # Extract nutrient values (they are ranges like '31-60')
        nutrients = {
            'N (kg/ha)': parse_range(row.get('N_kg_ha')),
            'P (kg/ha)': parse_range(row.get('P_kg_ha')),
            'K (kg/ha)': parse_range(row.get('K_kg_ha')),
            'S (kg/ha)': parse_range(row.get('S_kg_ha')),
            'Zn (kg/ha)': parse_range(row.get('Zn_kg_ha')),
            'B (kg/ha)': parse_range(row.get('B_kg_ha')),
            'Mg (kg/ha)': parse_range(row.get('Mg_kg_ha')),
            'OF (t/ha)': parse_range(row.get('OF_t_per_ha')),
        }
        nutrients = {k: v for k, v in nutrients.items() if v is not None}
        
        return {
            'type': 'field',
            'unit': 'kg/ha',
            'nutrients': nutrients,
            'variety': row.get('Variety_Group', '-'),
            'soil_level': soil_level,
            'note': 'Based on medium soil fertility; adjust if soil test available.'
        }
