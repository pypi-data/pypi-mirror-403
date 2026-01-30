# nepalpy/geographical/mappings.py

DISTRICT_PROVINCE_MAP = {

    # 🟦 Koshi Province (14)
    "bhojpur": "Koshi",
    "dhankuta": "Koshi",
    "ilam": "Koshi",
    "jhapa": "Koshi",
    "khotang": "Koshi",
    "morang": "Koshi",
    "okhaldhunga": "Koshi",
    "panchthar": "Koshi",
    "sankhuwasabha": "Koshi",
    "solukhumbu": "Koshi",
    "sunsari": "Koshi",
    "taplejung": "Koshi",
    "terhathum": "Koshi",
    "udayapur": "Koshi",

    # 🟨 Madhesh Province (8)
    "bara": "Madhesh",
    "dhanusha": "Madhesh",
    "mahottari": "Madhesh",
    "parsa": "Madhesh",
    "rautahat": "Madhesh",
    "saptari": "Madhesh",
    "sarlahi": "Madhesh",
    "siraha": "Madhesh",

    # 🟥 Bagmati Province (13)
    "bhaktapur": "Bagmati",
    "chitwan": "Bagmati",
    "dhading": "Bagmati",
    "dolakha": "Bagmati",
    "kathmandu": "Bagmati",
    "kavrepalanchok": "Bagmati",
    "lalitpur": "Bagmati",
    "makwanpur": "Bagmati",
    "nuwakot": "Bagmati",
    "ramechhap": "Bagmati",
    "rasuwa": "Bagmati",
    "sindhuli": "Bagmati",
    "sindhupalchok": "Bagmati",

    # 🟩 Gandaki Province (11)
    "baglung": "Gandaki",
    "gorkha": "Gandaki",
    "kaski": "Gandaki",
    "lamjung": "Gandaki",
    "manang": "Gandaki",
    "mustang": "Gandaki",
    "myagdi": "Gandaki",
    "nawalpur": "Gandaki",
    "parbat": "Gandaki",
    "syangja": "Gandaki",
    "tanahun": "Gandaki",

    # 🟪 Lumbini Province (12)
    "arghakhanchi": "Lumbini",
    "banke": "Lumbini",
    "bardiya": "Lumbini",
    "dang": "Lumbini",
    "gulmi": "Lumbini",
    "kapilvastu": "Lumbini",
    "palpa": "Lumbini",
    "pyuthan": "Lumbini",
    "rolpa": "Lumbini",
    "rupandehi": "Lumbini",
    "rukum east": "Lumbini",
    "nawalparasi west": "Lumbini",

    # 🟫 Karnali Province (10)
    "dailekh": "Karnali",
    "dolpa": "Karnali",
    "humla": "Karnali",
    "jajarkot": "Karnali",
    "jumla": "Karnali",
    "kalikot": "Karnali",
    "mugu": "Karnali",
    "rukum west": "Karnali",
    "salyan": "Karnali",
    "surkhet": "Karnali",

    # ⬛ Sudurpashchim Province (9)
    "achham": "Sudurpashchim",
    "baitadi": "Sudurpashchim",
    "bajhang": "Sudurpashchim",
    "bajura": "Sudurpashchim",
    "dadeldhura": "Sudurpashchim",
    "darchula": "Sudurpashchim",
    "doti": "Sudurpashchim",
    "kailali": "Sudurpashchim",
    "kanchanpur": "Sudurpashchim",
}


DISTRICTS = list(DISTRICT_PROVINCE_MAP.keys())
PROVINCES = sorted(set(DISTRICT_PROVINCE_MAP.values()))
