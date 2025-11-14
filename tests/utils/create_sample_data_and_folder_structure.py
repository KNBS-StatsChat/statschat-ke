"""
Script to create test data samples and folder structure for unit tests by copying a subset of existing data files.

Stored in tests/test_data

Uses permanent storage folders - created during SETUP:
    data/pdf_downloads: where all PDFs and url_dict.json are stored
    data/json_conversions: where full JSON representations of PDFs are stored
    data/json_split: where split JSON files (e.g., per-page/section) are stored
    

Run:
    python tests/utils/create_sample_data_and_folder_structure.py
"""

import json
import shutil
import random
from pathlib import Path

def create_test_samples_and_folder_structure(src_base="data", dest_base="tests/test_data", number_of_samples=2):
    src = Path(src_base)
    dest = Path(dest_base)

    # Reset destination
    if dest.exists():
        shutil.rmtree(dest)
    dest.mkdir(parents=True)

    # Define subfolders
    folders = [
        "pdf_downloads", "json_conversions", "json_split",
        "latest_pdf_downloads", "latest_json_conversions", "latest_json_split"
    ]
    for f in folders:
        (dest / f).mkdir(parents=True, exist_ok=True)

    # --- Permanent PDFs ---
    pdf_dir = src / "pdf_downloads"
    json_dir = src / "json_conversions"
    split_dir = src / "json_split"

    all_pdfs = sorted(pdf_dir.glob("*.pdf"))
    permanent_pdfs = all_pdfs[:number_of_samples]
    latest_pdfs = all_pdfs[number_of_samples:2*number_of_samples]  # next N, ensures they are different

    # Copy permanent PDFs + JSON conversions
    for pdf in permanent_pdfs:
        shutil.copy(pdf, dest / "pdf_downloads")
        json_name = pdf.with_suffix(".json").name
        if (json_dir / json_name).exists():
            shutil.copy(json_dir / json_name, dest / "json_conversions")

    # Copy random split JSONs for permanent
    split_files = list(split_dir.glob("*.json"))
    random_splits = random.sample(split_files, min(number_of_samples, len(split_files)))
    for split_file in random_splits:
        shutil.copy(split_file, dest / "json_split")

    # Filter url_dict.json for permanent PDFs
    url_dict_path = pdf_dir / "url_dict.json"
    if url_dict_path.exists():
        with open(url_dict_path) as f:
            url_dict = json.load(f)
        filtered_dict = {pdf.name: url_dict[pdf.name] for pdf in permanent_pdfs if pdf.name in url_dict}
        with open(dest / "pdf_downloads" / "url_dict.json", "w") as f:
            json.dump(filtered_dict, f, indent=4)

    # --- Latest PDFs (different ones) ---
    for pdf in latest_pdfs:
        shutil.copy(pdf, dest / "latest_pdf_downloads")
        json_name = pdf.with_suffix(".json").name
        if (json_dir / json_name).exists():
            shutil.copy(json_dir / json_name, dest / "latest_json_conversions")

    # Copy random split JSONs for latest
    latest_random_splits = random.sample(split_files, min(number_of_samples, len(split_files)))
    for split_file in latest_random_splits:
        shutil.copy(split_file, dest / "latest_json_split")

    # Filter url_dict.json for latest PDFs
    if url_dict_path.exists():
        with open(url_dict_path) as f:
            url_dict = json.load(f)
        filtered_latest = {pdf.name: url_dict[pdf.name] for pdf in latest_pdfs if pdf.name in url_dict}
        with open(dest / "latest_pdf_downloads" / "url_dict.json", "w") as f:
            json.dump(filtered_latest, f, indent=4)

    print(f"Samples created in {dest_base} now can run test_merge_database_files.py")

if __name__ == "__main__":
    create_test_samples_and_folder_structure()
