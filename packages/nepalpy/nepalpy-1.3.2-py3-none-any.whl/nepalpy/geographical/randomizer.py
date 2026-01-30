# nepalpy/geographical/randomizer.py

import random

def random_items(data, count=1):
    if not isinstance(data, list):
        raise TypeError("data must be a list")
    if count < 1:
        raise ValueError("count must be at least 1")
    return random.choice(data) if count == 1 else random.sample(data, min(count, len(data)))
