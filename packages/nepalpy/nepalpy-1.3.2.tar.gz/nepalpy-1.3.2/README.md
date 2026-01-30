# NepalPy 🇳🇵

[![PyPI version](https://badge.fury.io/py/nepalpy.svg)](https://pypi.org/project/nepalpy/)  
[![Python Version](https://img.shields.io/pypi/pyversions/nepalpy)](https://pypi.org/project/nepalpy/)  
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

**Nepali Name, Caste & Location Generator** – A lightweight, zero-dependency Python library to generate **realistic Nepali names, surnames, caste/ethnic group categories, districts, and provinces**.

`nepalpy` is designed for developers, researchers, and students who need **authentic Nepali demographic and geographic data** for testing, simulations, analytics, or educational projects.

---

## Features

| Feature | Description |
|---------|-------------|
| `name()` | Generate random first names (male, female, or mixed) |
| `name_start_with(letter, count)` | Generate names starting with a given letter |
| `name_end_with(letter, count)` | Generate names ending with a given letter |
| `last_name()` | Generate a random surname/caste |
| `cast(count)` | Generate multiple surnames |
| `full_name()` | Generate full names (first + last) |
| `cast_category(surname)` | Identify caste/ethnic group category |
| `district(count=1)` | Generate 1 or multiple random districts |
| `district_all()` | Get all 77 districts of Nepal |
| `province(count=1)` | Generate 1 or multiple random provinces |
| `province_all()` | Get all provinces of Nepal |
| `district_province(district_name)` | Return the province of a given district |

**Supported Caste Categories:**  
- **khas-arya** (bahun, chhetri, thakuri, sanyasi)  
- **janajati** (tamang, gurung, magar, rai, limbu, etc.)  
- **newar** (shrestha, maharjan, sakya, bajracharya, etc.)  
- **dalit** (kami, damai, sarki, bishwokarma, etc.)  
- **madhesi** (yadav, kurmi, teli, chamar, etc.)  

All mappings and geographic data are configurable and expandable.

---

## Installation

```bash
pip install nepalpy
