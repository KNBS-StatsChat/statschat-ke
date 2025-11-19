'''
This script organizes and updates data folders after new documents 
have been downloaded and processed in 'UPDATE' mode only.
    
Moves files from "latest" folders to their corresponding permanent locations:
    - PDFs: Moves .pdf files from latest_pdf_downloads to pdf_downloads
    - JSON conversions: Moves .json files from latest_json_conversions to json_conversions
    - Split JSONs: Moves .json files from latest_json_split to json_split
    
Updates url_dict.json file that maps PDF filenames to their source URLs & report pages:
    - Loads existing url_dict.json from 'pdf_downloads'
    - Loads new url_dict.json from 'latest_pdf_downloads'
    
Merges - adds only new entries from the latest dictionary (avoiding duplicates)

Saves - writes updated dictionary back to original location

Cleans up - deletes latest url_dict.json from 'latest_pdf_downloads' to prepare for the next UPDATE batch
'''

# %%
# import packages
from pathlib import Path
import json

# %%
# Database directories
DATA_DIR = Path.cwd().joinpath("data/pdf_downloads")
JSON_DIR = Path.cwd().joinpath("data/json_conversions")
JSON_SPLIT_DIR = Path.cwd().joinpath("data/json_split")

# Latest directories
LATEST_JSON_SPLIT_DIR = Path.cwd().joinpath("data/latest_json_split")
LATEST_JSON_DIR = Path.cwd().joinpath("data/latest_json_conversions")
LATEST_DATA_DIR = Path.cwd().joinpath("data/latest_pdf_downloads")

# %%
# Moves latest json conversions files 'json_conversions' folder
for json_file in LATEST_JSON_DIR.glob("*.json"):
    source_file = json_file

    destination_file = JSON_DIR.joinpath(json_file.name)

    source_file.rename(destination_file)

    print(f"{json_file.name} has been moved to {JSON_DIR}")

# %%
# Moves latest json split files to all 'json_split' folder

for json_split_file in LATEST_JSON_SPLIT_DIR.glob("*.json"):
    source_file = json_split_file

    destination_file = JSON_SPLIT_DIR.joinpath(json_split_file.name)

    source_file.rename(destination_file)

print(f"json_splits have been moved to {JSON_SPLIT_DIR}")

# %%
# Moves latest PDF file downloads to 'pdf_downloads' folder

for pdf_file in LATEST_DATA_DIR.glob("*.pdf"):
    source_file = pdf_file

    destination_file = DATA_DIR.joinpath(pdf_file.name)

    source_file.rename(destination_file)

    print(f"{pdf_file.name} has been moved to {DATA_DIR}")
    
# %%
# Update url_dict.json with new pdf files - removing the latest url_dict
# Load original and latest URL dictionaries
ORIGINAL_URL_DICT_PATH = DATA_DIR.joinpath("url_dict.json")
LATEST_URL_DICT_PATH = LATEST_DATA_DIR.joinpath("url_dict.json")

with open(ORIGINAL_URL_DICT_PATH, "r") as file:
    original_url_dict = json.load(file)

with open(LATEST_URL_DICT_PATH, "r") as file:
    latest_url_dict = json.load(file)

# Merge: Add only new entries
new_entries = {
    key: value for key, value in latest_url_dict.items() if key not in original_url_dict
}
original_url_dict.update(new_entries)

# Save updated original url_dict
with open(ORIGINAL_URL_DICT_PATH, "w") as file:
    json.dump(original_url_dict, file, indent=4)
print(f"Added {len(new_entries)} new entries to {ORIGINAL_URL_DICT_PATH}")

# Remove latest url_dict to reset for the next run
LATEST_URL_DICT_PATH.unlink()
print(f"Deleted {LATEST_URL_DICT_PATH} to reset for next update.")
