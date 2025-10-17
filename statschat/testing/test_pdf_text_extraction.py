# %%
from pathlib import Path
from statschat import load_config
import json
import fitz  # PyMuPDF
from spellchecker import SpellChecker
import unicodedata
from difflib import unified_diff
import re

# %% Configuration
# Load configuration
config = load_config(name="main")
PDF_FILES = config["preprocess"]["mode"].upper()

# Set directories
BASE_DIR = Path.cwd().joinpath("data")

# Path for PDF files
DATA_DIR = BASE_DIR.joinpath(
    "pdf_downloads" if PDF_FILES == "SETUP" else "latest_pdf_downloads"
)

# %%
# Path for JSON conversion
if PDF_FILES == "SETUP":
    JSON_DIR = Path.cwd().joinpath("data/json_conversions")
else:
    JSON_DIR = Path.cwd().joinpath("data/latest_json_conversions")

# %%
# Path for output folder for test results
TEST_OUTPUT_DIR = Path.cwd().joinpath("outputs/tests")
TEST_OUTPUT_DIR.mkdir(exist_ok=True, parents=True)

# %%
# Initialize spell checker
spell = SpellChecker()

def extract_pdf_text(pdf_path):
    """
    Extracts text from each page of a PDF file using PyMuPDF.

    Args:
        pdf_path (Path): Path to the PDF file.

    Returns:
        dict: A dictionary mapping page numbers (1-based) to their extracted text.
    """
    doc = fitz.open(pdf_path)
    return {page.number + 1: page.get_text() for page in doc}

def compare_texts(json_text, pdf_text):
    """
    Compares two text strings line-by-line and returns their differences,
    excluding lines that contain numeric characters.

    Args:
        json_text (str): Text extracted from the JSON file.
        pdf_text (str): Text extracted directly from the PDF.

    Returns:
        list or None: A list of differing lines (excluding numeric ones), or None if no differences.
    """
    # Generate unified diff and filter out lines containing digits
    
    diff = list(unified_diff(pdf_text.splitlines(), json_text.splitlines()))
    filtered = [
        line for line in diff
        if not re.search(r'\d', line) and line.strip() not in ("---", "+++")
    ]
    return filtered if filtered else None

def check_json_text(text):
    """
    Checks a block of text for spelling errors and irregular (non-Latin) characters.

    Args:
        text (str): The text to analyze.

    Returns:
        tuple:
            - set: Misspelled words detected.
            - list: Irregular characters found (non-ASCII and non-Latin).
    """
    words = text.split()
    misspelled = spell.unknown(words)
    irregular_chars = [c for c in text if ord(c) > 127 and not unicodedata.name(c, '').startswith('LATIN')]
    return misspelled, irregular_chars

def check_file_pair_text(pdf_path: Path, json_path: Path):
    """
    Compares the text content of a PDF file and its corresponding JSON file.
    Generates a structured report including:
        - Differences (excluding numeric lines)
        - Misspelled words
        - Irregular characters
    Saves the report to tests/outputs/ as a JSON file.

    Args:
        pdf_path (Path): Path to the PDF file.
        json_path (Path): Path to the corresponding JSON file.
    """
    print(f"\n🔍 Checking: {pdf_path.name} and {json_path.name}")
    pdf_texts = extract_pdf_text(pdf_path)

    # Load JSON content
    with json_path.open('r', encoding='utf-8') as f:
        json_data = json.load(f)

    # Initialize report structure
    file_report = {
        "pdf_file": pdf_path.name,
        "json_file": json_path.name,
        "pages": {}
    }

    # Loop through each page in the JSON
    for page in json_data['content']:
        page_num = page['page_number']
        json_text = page['page_text']
        pdf_text = pdf_texts.get(page_num, '')

        # Initialize page-level report
        page_report = {
            "diff_count": 0,
            "diff_examples": [],
            "diff_occurrences": {},
            "misspelled": [],
            "irregular_chars": []
        }

        # Compare text and record differences
        diff = compare_texts(json_text, pdf_text)
        if diff:
            page_report["diff_count"] = len(diff)
            page_report["diff_examples"] = diff[:5]  # Limit to first 5 examples
            for line in diff:
                page_report["diff_occurrences"][line] = page_report["diff_occurrences"].get(line, 0) + 1

        # Check spelling and irregular characters
        misspelled, irregular = check_json_text(json_text)
        page_report["misspelled"] = list(misspelled)
        page_report["irregular_chars"] = irregular

        # Add page report to file report
        file_report["pages"][str(page_num)] = page_report

    # Save report to output directory
    output_path = TEST_OUTPUT_DIR / f"{pdf_path.stem}_report.json"
    with output_path.open("w", encoding="utf-8") as out:
        json.dump(file_report, out, indent=2, ensure_ascii=False)

    print(f"✅ Saved report to {output_path}")

def check_folders_text_extraction(data_dir: Path, json_dir: Path):
    """
    Iterates through all PDF files in a directory and checks them against their
    corresponding JSON files. Each pair is analyzed and a report is generated.

    Args:
        data_dir (Path): Directory containing PDF files.
        json_dir (Path): Directory containing JSON files.
    """
    pdf_files = list(data_dir.glob('*.pdf'))

    for pdf_file in pdf_files:
        json_file = json_dir / (pdf_file.stem + '.json')
        if json_file.exists():
            check_file_pair_text(pdf_path=pdf_file, json_path=json_file)
        else:
            print(f"⚠️ JSON file missing for {pdf_file.name}")

if __name__ == "__main__":
    check_folders_text_extraction(DATA_DIR, JSON_DIR)

