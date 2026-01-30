# nepalpy/geographical/provinces.py

from .mappings import PROVINCES
from .randomizer import random_items

def provience(count=1):
    return random_items(PROVINCES, count)

def provience_all():
    return PROVINCES
