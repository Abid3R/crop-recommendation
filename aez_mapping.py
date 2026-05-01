# ================================================================
# aez_mapping.py - District to AEZ mapping (BARC FRG-2024)
# ================================================================

DISTRICT_TO_AEZ = {
    'Thakurgaon': 1, 'Panchagar': 1, 'Dinajpur': 1,
    'Kurigram': 2, 'Lalmonirhat': 2,
    'Rangpur': 3, 'Nilphamari': 3, 'Gaibandha': 3,
    'Bogra': 4, 'Bogura': 4, 'Joypurhat': 4, 'Naogaon': 4,
    'Natore': 5,
    'Sirajganj': 7, 'Jamalpur': 7, 'Tangail': 7, 'Manikganj': 7,
    'Mymensingh': 8, 'Kishoreganj': 8, 'Sherpur': 8, 'Netrokona': 8,
    'Dhaka': 9, 'Narsingdi': 9, 'Munshiganj': 9, 'Gazipur': 9,
    'Rajshahi': 11, 'Chapainawabganj': 11, 'Pabna': 11,
    'Kushtia': 11, 'Jashore': 11, 'Jhenaidah': 11, 'Faridpur': 11,
    'Khulna': 12, 'Satkhira': 12, 'Bagerhat': 12,
    'Barisal': 13, 'Pirojpur': 13, 'Jhalokati': 13, 'Barguna': 13,
    'Gopalganj': 14, 'Madaripur': 14, 'Shariatpur': 14,
    'Cumilla': 18, 'Brahmanbaria': 18, 'Chandpur': 18,
    'Sylhet': 21, 'Moulvibazar': 21, 'Habiganj': 21, 'Sunamganj': 21,
    'Chittagonj': 23, 'Chittagong': 23, 'Feni': 23, 'Noakhali': 23,
    'Rangamati': 24, 'Bandarban': 24, 'Khagrachhari': 24,
}

AEZ_NAMES = {
    1: 'Old Himalayan Piedmont Plain', 2: 'Active Tista Floodplain',
    3: 'Tista Meander Floodplain', 4: 'Karatoya-Bangali Floodplain',
    5: 'Lower Atrai Basin', 7: 'Active Brahmaputra-Jamuna Floodplain',
    8: 'Young Brahmaputra and Jamuna Floodplain', 9: 'Old Brahmaputra Floodplain',
    11: 'High Ganges River Floodplain', 12: 'Low Ganges River Floodplain',
    13: 'Ganges Tidal Floodplain', 14: 'Gopalganj-Khulna Bils',
    18: 'Meghna Floodplain', 21: 'Sylhet Basin',
    23: 'Chittagong Coastal Plain', 24: 'Chittagong Hill Tracts',
}

def get_aez(district):
    if district in DISTRICT_TO_AEZ:
        return DISTRICT_TO_AEZ[district]
    for key, val in DISTRICT_TO_AEZ.items():
        if key.lower() == district.lower():
            return val
    return 9

def get_aez_name(aez_num):
    return AEZ_NAMES.get(aez_num, f'AEZ {aez_num}')
