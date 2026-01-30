# nepalpy 🇳🇵

**Nepali Name & Caste Generator** – A lightweight, zero-dependency Python library to generate realistic Nepali names, surnames (castes), and caste/ethnic group categories.

`nepalpy` is designed for developers, researchers, and students who need **realistic Nepali demographic data** for testing, simulations, analytics, or educational projects.

---

## ✨ Why nepalpy?

Nepali names and caste systems are **culturally rich and diverse**, but most fake-data libraries don’t support Nepal properly.

`nepalpy` fills this gap by providing:

* Authentic Nepali first names (male & female)
* Large, curated caste/surname datasets
* Accurate caste category mapping
* Simple, fast, dependency-free API

---

## 🚀 Features

* ✅ Generate random Nepali first names
* ✅ Generate male, female, or mixed names
* ✅ Filter names by starting or ending letters
* ✅ Generate surnames (castes)
* ✅ Generate full names (first + last)
* ✅ Access **100+ Nepali castes/surnames**
* ✅ Identify caste category:

  * khas-arya
  * janajati
  * newar
  * dalit
  * madhesi
* ✅ All outputs normalized to **lowercase**
* ✅ Zero external dependencies

---

## 📦 Installation

```bash
pip install nepalpy
```

Python 3.7+ supported.

---

## 🧠 Basic Usage

```python
from nepalpy.name import name, last_name, full_name, cast, cast_category
```

---

## 🧑 First Name Generator

### Generate random names (mixed)

```python
name(5)
```

**Output:**

```text
['sushil', 'dibisha', 'rama', 'gita', 'dipesh']
```

---

### Generate male & female names separately

```python
name(male=3, female=2)
```

**Output:**

```text
['ram', 'suman', 'binod', 'gita', 'sita']
```

---

## 🔠 Filter Names

### Names starting with a letter

```python
name_start_with('s', count=5)
```

**Output:**

```text
['suresh', 'suman', 'sunita', 'sagar', 'sita']
```

---

### Names ending with a letter

```python
name_end_with('a', count=5)
```

**Output:**

```text
['gita', 'sita', 'anita', 'rekha', 'laxmita']
```

---

## 👨‍👩‍👧 Surname / Caste Generator

### Generate a random caste (surname)

```python
last_name()
```

**Output:**

```text
'maharjan'
```

---

### Generate multiple castes

```python
cast(5)
```

**Output:**

```text
['thapa', 'kami', 'tamang', 'shrestha', 'yadav']
```

---

## 🧾 Full Name Generator

```python
full_name()
```

**Output:**

```text
'sushil shrestha'
```

---

## 🏷️ Caste Category Detection

Identify the caste/ethnic group for a given surname.

```python
cast_category('Kami')
```

**Output:**

```text
'dalit'
```

More examples:

```python
cast_category('Thapa')      # khas-arya
cast_category('Maharjan')   # janajati
cast_category('Yadav')      # madhesi
```

---

## 📚 Supported Caste Categories

* **khas-arya** (bahun, chhetri, thakuri, sanyasi)
* **janajati** (tamang, gurung, magar, rai, limbu, etc.)
* **newar** (shrestha, maharjan, sakya, bajracharya, etc.)
* **dalit** (kami, damai, sarki, bishwokarma, etc.)
* **madhesi** (yadav, kurmi, teli, chamar, etc.)

All mappings are configurable and expandable.

---

## 🧪 Use Cases

* Fake data generation for Nepali apps
* Backend testing & QA automation
* Academic & demographic simulations
* Machine learning datasets
* Forms & validation testing
* Government / NGO software prototyping

---

## 🛠️ Design Philosophy

* 🔹 Simple API
* 🔹 Human-readable outputs
* 🔹 Culturally aware data
* 🔹 No third-party dependencies
* 🔹 Easy to extend

---

## 🤝 Contributing

Contributions are welcome!

You can help by:

* Adding more names
* Improving caste mappings
* Adding aliases & spelling variants
* Writing tests
* Improving documentation

---

## 📄 License

MIT License © 2026

---

## 🇳🇵 Made for Nepal

Built with ❤️ to support Nepali developers and researchers.
