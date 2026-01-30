# nepalpy/geographical/districts.py

from .mappings import DISTRICTS, DISTRICT_PROVINCE_MAP
from .randomizer import random_items

def district(count=1):
    return random_items(DISTRICTS, count)

def district_all():
    return DISTRICTS

def district_provience(district_name):
    if not district_name:
        raise ValueError("District name is required")

    district_name = district_name.lower()
    return DISTRICT_PROVINCE_MAP.get(district_name, "District not found")
