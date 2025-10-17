# %%
from pathlib import Path
from statschat import load_config
import json
import fitz  # PyMuPDF
from spellchecker import SpellChecker
import unicodedata
from difflib import unified_diff

#source statschat_global_env/bin/activate    

# %% Configuration
# Load configuration
config = load_config(name="main")
PDF_FILES = config["preprocess"]["mode"].upper()

# Set directories
BASE_DIR = Path.cwd().joinpath("data")

# For PDF files
DATA_DIR = BASE_DIR.joinpath(
    "pdf_downloads" if PDF_FILES == "SETUP" else "latest_pdf_downloads"
)

# %%
# For JSON conversion
if PDF_FILES == "SETUP":
    JSON_DIR = Path.cwd().joinpath("data/json_conversions")
else:
    JSON_DIR = Path.cwd().joinpath("data/latest_json_conversions")

# %%
# Initialize spell checker
spell = SpellChecker()

# %%
def extract_pdf_text(pdf_path):
    """
    Extracts text from each page of a PDF file.

    Args:
        pdf_path (str or Path): Path to the PDF file.

    Returns:
        dict: A dictionary mapping page numbers (1-based) to their extracted text.
    """
    doc = fitz.open(pdf_path)
    # Use dictionary comprehension to map page number to text
    return {page.number + 1: page.get_text() for page in doc}

# %%
def compare_texts(json_text, pdf_text):
    """
    Compares two text strings and returns their differences.

    Args:
        json_text (str): Text from the JSON file.
        pdf_text (str): Text extracted from the PDF.

    Returns:
        list or None: List of differences if any, otherwise None.
    """
    # Generate unified diff between the two texts
    diff = list(unified_diff(pdf_text.splitlines(), json_text.splitlines()))
    return diff if diff else None

# %%
def check_json_text(text):
    """
    Checks text in json for spelling errors and irregular characters.

    Args:
        text (str): Text to check.

    Returns:
        tuple: A set of misspelled words and a list of irregular characters.
    """
    words = text.split()
    misspelled = spell.unknown(words)
    
    # Identify non-ASCII characters that aren't Latin
    irregular_chars = [c for c in text if ord(c) > 127 and not unicodedata.name(c, '').startswith('LATIN')]
    return misspelled, irregular_chars

# %%
def check_file_pair_text(pdf_path: Path, json_path: Path):
    """
    Checks a corresponding pair of PDF and JSON files by comparing their text content.

    Args:
        pdf_path (Path): Path to the PDF file.
        json_path (Path): Path to the corresponding JSON file.
    """
    print(f"\n🔍 Checking: {pdf_path.name} and {json_path.name}")
    pdf_texts = extract_pdf_text(pdf_path=pdf_path)

    # Load JSON content
    with json_path.open('r', encoding='utf-8') as f:
        json_data = json.load(f)

    # Iterate through each page in the JSON content
    for page in json_data['content']:
        page_num = page['page_number']
        json_text = page['page_text']
        pdf_text = pdf_texts.get(page_num, '')

        print(f"\n📄 Page {page_num}:")

        # Compare texts and show differences
        diff = compare_texts(json_text=json_text, pdf_text=pdf_text)
        if diff:
            print("  🔍 Differences found:")
            for line in diff[:5]:  # Show only first 5 lines of diff
                print("   ", line)

        # Checks spelling and character encoding
        misspelled, irregular = check_json_text(text=json_text)
        if misspelled:
            print("  ❌ Misspelled words:", misspelled)
        if irregular:
            print("  ⚠️ Irregular characters:", irregular)

# %%
def check_folders_text_extraction(data_dir: Path, json_dir: Path):
    """
    Checks all PDF files in a directory against their corresponding JSON files.

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

# %%
# Run the test
check_folders_text_extraction(data_dir=DATA_DIR, json_dir=JSON_DIR)


# %%
