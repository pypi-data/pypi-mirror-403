# nepalpy/name/name_generator.py
import random
from typing import List, Optional, Union

from .male_names import MALE_NAMES
from .female_names import FEMALE_NAMES
from .cast import CASTES, CASTE_CATEGORY_MAP

_ALL_FIRST_NAMES = [n.lower() for n in MALE_NAMES + FEMALE_NAMES]  # ← optional: store lowercase


def name(male: int = 1, female: Optional[int] = None) -> List[str]:
    result = []
    if female is None:
        selected = random.sample(_ALL_FIRST_NAMES, min(male, len(_ALL_FIRST_NAMES)))
    else:
        if male > 0:
            result += random.sample([n.lower() for n in MALE_NAMES], min(male, len(MALE_NAMES)))
        if female is not None and female > 0:
            result += random.sample([n.lower() for n in FEMALE_NAMES], min(female, len(FEMALE_NAMES)))
        selected = result
        random.shuffle(selected)
    
    return [item.lower() for item in selected]   # ← force lowercase


def name_start_with(start: str, count: int = 10) -> List[str]:
    start = start.lower()
    matches = [n for n in _ALL_FIRST_NAMES if n.lower().startswith(start)]
    selected = random.sample(matches, min(count, len(matches))) if matches else []
    return [item.lower() for item in selected]   # ← lowercase


def name_end_with(end: str, count: int = 10) -> List[str]:
    end = end.lower()
    matches = [n for n in _ALL_FIRST_NAMES if n.lower().endswith(end)]
    selected = random.sample(matches, min(count, len(matches))) if matches else []
    return [item.lower() for item in selected]   # ← lowercase


def last_name() -> str:
    return random.choice(CASTES).lower()   # ← lowercase


def full_name() -> str:
    first = random.choice(_ALL_FIRST_NAMES)
    last = random.choice(CASTES)
    return f"{first} {last}".lower()      # ← lowercase whole string


def cast(count: int = 1) -> Union[str, List[str]]:
    if count == 1:
        return random.choice(CASTES).lower()
    
    selected = random.sample(CASTES, min(count, len(CASTES)))
    return [item.lower() for item in selected]   # ← lowercase list


def cast_category(cast_name: str) -> str:
    key = cast_name.strip().title()
    result = CASTE_CATEGORY_MAP.get(key, "Unknown")
    return result.lower()   # ← lowercase category