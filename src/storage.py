import json
import os
from config import STICKER_DATA_FILE

# Function to load data when bot starts
def load_data():
    if os.path.exists(STICKER_DATA_FILE):
        with open(STICKER_DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

# Function to save data when it changes
def save_data():
    with open(STICKER_DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(user_sticker_packs, f, indent=4, ensure_ascii=False)

# Load data when bot starts
user_sticker_packs = load_data()