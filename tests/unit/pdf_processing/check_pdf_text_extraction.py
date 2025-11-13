"""
Checks text extraction word matches between PDFs and their JSON conversions.

- Can check with different extraction methods in LOCAL SCRIPT CONFIG.
- Normalizes text before comparison and ignores numeric differences.
- Saves detailed reports per file and combined summaries in CSV, Markdown and TXT formats.

Run:
    python tests/unit/pdf_processing/check_pdf_text_extraction.py
"""

# %%
from pathlib import Path
from statschat import load_config
import json
import fitz  # PyMuPDF
from spellchecker import SpellChecker
import unicodedata
from difflib import unified_diff
import re
import pandas as pd
import pdfplumber
from pypdf import PdfReader
import textwrap

#--------------------
# CONFIG - FROM MAIN.TOML
#--------------------
# Load configuration
config = load_config(name="main")
PDF_FILES = config["preprocess"]["mode"].upper()

#--------------------
# DIRECTORY PATHS
#--------------------
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
OUTPUT_TESTS_DIR = Path.cwd().joinpath("outputs/tests")
OUTPUT_TESTS_DIR.mkdir(exist_ok=True, parents=True)

# %%
# Initialize spell checker
spell = SpellChecker()

#--------------------
# LOCAL SCRIPT CONFIG
#--------------------
method = "pypdf2" # Options: 'fitz', 'pypdf2', 'pdfplumber'

max_files_to_process = "3" # Can be an integer to specify certain number or "all" to do whole directory

diff_lines_per_page = 15 # Controls how many diff lines per page are shown in the markdown report 
                        # If page has 20 differing lines, only first 2 shown in report
                        
number_pages_to_view = "all" # Can be an integer to specify certain number or "all" for whole document

#---------------
# PDF EXTRACTOR
#---------------
def extract_pdf_text(pdf_path: Path, method: str = method) -> dict:
    """
    Extracts text from each page of a PDF using the specified method.

    Supported methods:
        - 'fitz' (PyMuPDF)
        - 'pypdf2'
        - 'pdfplumber'

    Args:
        pdf_path (Path): Path to the PDF file.
        method (str): Extraction method to use.

    Returns:
        dict: Page number (1-based) mapped to extracted text.
    """
    if method == "fitz":
        doc = fitz.open(pdf_path)
        return {page.number + 1: page.get_text() for page in doc}

    elif method == "pypdf2":
        reader = PdfReader(str(pdf_path))
        return {i + 1: page.extract_text() or "" for i, page in enumerate(reader.pages)}

    elif method == "pdfplumber":
        with pdfplumber.open(pdf_path) as pdf:
            return {i + 1: page.extract_text() or "" for i, page in enumerate(pdf.pages)}

    else:
        raise ValueError(f"Unsupported extraction method: {method}")
    
#-------------------
# TEXT NORMALISER
#-------------------

def normalize_text(text: str) -> str:
    """
    Normalize text for fair comparison:
      - Unicode normalization (NFKC)
      - Lowercasing
      - Remove punctuation
      - Collapse whitespace
    """
    text = unicodedata.normalize("NFKC", text)
    text = text.lower()
    text = re.sub(r"[^\w\s]", "", text)   # strip punctuation
    text = re.sub(r"\s+", " ", text).strip()
    return text

#---------------
# COMPARISONS
#---------------
def compare_texts(
    json_text,
    pdf_text,
    page_num=None,
    pdf_file=None,
    json_file=None,
    log_dir=None,
    method = method
):
    """
    Compares two text strings line-by-line and returns their differences,
    excluding lines that contain numeric characters. Also prints and logs the source texts.

    Args:
        json_text (str): Text extracted from the JSON file.
        pdf_text (str): Text extracted directly from the PDF.
        page_num (int, optional): Page number being compared.
        pdf_file (str, optional): Name of the PDF file.
        json_file (str, optional): Name of the JSON file.
        log_dir (Path, optional): Directory to save the log file.
        method (str): Extraction method used (e.g., 'fitz', 'pypdf2', 'pdfplumber').

    Returns:
        list or None: A list of differing lines (excluding numeric ones), or None if no differences.
    """
    # Wrap JSON text to match PDF formatting
    wrapped_json = textwrap.fill(json_text, width=80)
    wrapped_pdf = textwrap.fill(pdf_text, width=80)

    header = f"\nComparing extracted text via {method.upper()} for Page {page_num} of PDF: {pdf_file.name} vs JSON: {json_file.name}\n"
    pdf_section = f"----- PDF Text -----\n{wrapped_pdf or '[Empty]'}\n"
    json_section = f"----- JSON Text -----\n{wrapped_json or '[Empty]'}\n"

    # print(header + pdf_section + json_section)

    if log_dir:
        log_path = log_dir / f"{pdf_file.name}_comparison_with_{method}.txt"
        with log_path.open("a", encoding="utf-8") as log_file:
            log_file.write(header + pdf_section + json_section + "\n\n")

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

def check_file_pair_text(pdf_path: Path, json_path: Path, method: str = method, number_pages_to_view: int | str = number_pages_to_view):
    """
    Compares the text content of a PDF file and its corresponding JSON file.
    Generates a structured report including:
        - Differences (excluding numeric lines)
        - Misspelled words
        - Irregular characters
        - Word-level extraction accuracy (%)
    Saves the report to outputs/tests/ as a JSON file.
    """
    print(f"\n🔍 Checking: {pdf_path.name} and {json_path.name} using method: {method}")
    pdf_texts = extract_pdf_text(pdf_path, method=method)

    with json_path.open('r', encoding='utf-8') as f:
        json_data = json.load(f)

    # Clear existing log file for this PDF and method
    log_path = OUTPUT_TESTS_DIR / f"{pdf_path.name}_comparison_with_{method}.txt"
    log_path.write_text("")

    file_report = {
        "pdf_file": pdf_path.name,
        "json_file": json_path.name,
        "pages": {}
    }

    # Handle integer vs "all"
    for i, page in enumerate(json_data['content']):
        if number_pages_to_view != "all" and i >= int(number_pages_to_view):
            break

        page_num = page['page_number']

        #  Normalize both JSON and PDF text before comparison
        raw_json_text = page['page_text']
        raw_pdf_text = pdf_texts.get(page_num, '')

        json_text = normalize_text(raw_json_text)
        pdf_text = normalize_text(raw_pdf_text)

        page_report = {
            "diff_count": 0,
            "diff_examples": [],
            "diff_occurrences": {},
            "misspelled": [],
            "irregular_chars": [],
            "word_match": None
        }

        # Compare text and record differences
        diff = compare_texts(
            json_text=json_text,
            pdf_text=pdf_text,
            page_num=page_num,
            pdf_file=pdf_path,
            json_file=json_path,
            log_dir=OUTPUT_TESTS_DIR,
            method=method
        )
        if diff:
            page_report["diff_count"] = len(diff)
            page_report["diff_examples"] = diff[:2]  # still limit diff lines per page
            for line in diff:
                page_report["diff_occurrences"][line] = page_report["diff_occurrences"].get(line, 0) + 1

        # Check spelling and irregular characters (on normalized JSON text)
        misspelled, irregular = check_json_text(json_text)
        page_report["misspelled"] = list(misspelled)
        page_report["irregular_chars"] = irregular

        # Calculate word-level matches
        json_words = json_text.split()
        pdf_words = set(pdf_text.split())
        matched = [word for word in json_words if word in pdf_words]
        total = len(json_words)
        accuracy = (len(matched) / total * 100) if total > 0 else 0
        page_report["word_match"] = round(accuracy, 2)

        # Add page report to file report
        file_report["pages"][str(page_num)] = page_report

    output_path = OUTPUT_TESTS_DIR / f"{pdf_path.stem}_report.json"
    with output_path.open("w", encoding="utf-8") as out:
        json.dump(file_report, out, indent=2, ensure_ascii=False)

    print(f"Saved report to {output_path}")


def check_folders_text_extraction(data_dir: Path, json_dir: Path, max_files_to_process: int | str = 2):
    """
    Iterates through PDF files in a directory and checks them against their
    corresponding JSON files. Limits processing to `max_files_to_process` pairs unless set to 'all'.

    Args:
        data_dir (Path): Directory containing PDF files.
        json_dir (Path): Directory containing JSON files.
        max_files_to_process (int or str): Maximum number of PDF–JSON pairs to process.
                                Use 'all' to process everything.
    """
    pdf_files = list(data_dir.glob('*.pdf'))
    processed_count = 0

    for pdf_file in pdf_files:
        if max_files_to_process != "all" and processed_count >= int(max_files_to_process):
            print(f"Limit reached: Only processing {max_files_to_process} PDF files.")
            break

        json_file = json_dir / (pdf_file.stem + '.json')
        if json_file.exists():
            check_file_pair_text(pdf_path=pdf_file, json_path=json_file, method=method, number_pages_to_view=number_pages_to_view)

            processed_count += 1
        else:
            print(f"⚠️ JSON file missing for {pdf_file.name}")
                    
#-----------------
# OUTPUT SUMMARIES
#-----------------
def json_to_csv(json_dir: Path, output_dir: Path, pdf_extractor_name: str = method):
    """
    Converts multiple JSON audit reports in a directory into a single CSV summary.

    Each row represents one page from one report and includes:
        - PDF and JSON filenames
        - Page number
        - Diff count
        - Misspelled words
        - Irregular characters
        - Accuracy percentage

    Args:
        json_dir (Path): Directory containing JSON files.
        output_dir (Path): Directory where the CSV file will be saved.
        pdf_extractor_name (str): Name of the extractor used (e.g., 'fitz', 'pypdf2', 'pdfplumber').

    Returns:
        None. Writes the combined CSV file to disk.
    """
    rows = []  # List to hold all page-level summary rows

    # Loop through each JSON file in the directory
    for json_file in json_dir.glob("*.json"):
        with json_file.open('r', encoding='utf-8') as f:
            data = json.load(f)

        # Loop through each page in the report
        for page_num, page_data in data['pages'].items():
            # Build a row with relevant metrics
            rows.append({
                "pdf_file": data["pdf_file"],
                "json_file": data["json_file"],
                "page_number": page_num,
                "difference_count": page_data["diff_count"],
                "word_match%": page_data.get("word_match", "")
            })

    # Define output filename using extractor name
    output_csv = output_dir / f"pdf_to_json_text_extraction_{pdf_extractor_name}_summary.csv"

    # Convert to DataFrame and save as CSV
    df = pd.DataFrame(rows)
    df.to_csv(output_csv, index=False)
    print(f"Saved combined CSV to {output_csv}")
  
def combine_json_reports_to_markdown(json_dir: Path, output_dir: Path, pdf_extractor_name: str = method):
    """
    Combines all JSON audit reports in a directory into a single Markdown file.

    Each report includes:
        - PDF and JSON filenames
        - Page-by-page summary of:
            - Diff count
            - Misspelled words
            - Irregular characters
            - Accuracy percentage
            - Sample diff lines (formatted as code blocks)

    Args:
        json_dir (Path): Directory containing JSON audit reports.
        output_dir (Path): Directory where the Markdown file will be saved.
        pdf_extractor_name (str): Name of the extractor used (e.g., 'fitz', 'pypdf2', 'pdfplumber').

    Returns:
        None. Writes the combined Markdown file to disk.
    """
    all_lines = [f"# Report using {pdf_extractor_name.upper()} for text extraction\n"]  # Top-level heading with extractor name

    # Loop through each JSON file in the directory
    for json_file in json_dir.glob("*.json"):
        with json_file.open('r', encoding='utf-8') as f:
            data = json.load(f)

        # Add file-level heading
        all_lines.append(f"\n---\n\n## File: `{data['pdf_file']}`")
        all_lines.append(f"**JSON Source**: `{data['json_file']}`")

        # Loop through each page in the report
        for page_num, page_data in data['pages'].items():
            all_lines.append(f"\n### Page {page_num}")
            all_lines.append(f"- **Differences Found**: {page_data['diff_count']}")
            all_lines.append(f"- **Word Matches**: {page_data.get('word_match', 'N/A')}%")

            # Include diff examples if available
            if page_data['diff_examples']:
                all_lines.append("- **Examples:**")
                all_lines.append("```diff")
                for line in page_data['diff_examples']:
                    all_lines.append(line)
                all_lines.append("```")

            # Include misspelled words if any
            if page_data['misspelled']:
                all_lines.append(f"- **Potential Misspelled Words Examples**: {', '.join(page_data['misspelled'])}")

            # Include irregular characters if any
            if page_data['irregular_chars']:
                all_lines.append(f"- **Irregular Characters**: {', '.join(page_data['irregular_chars'])}")

    # Define output Markdown filename using extractor name
    output_md = output_dir / f"pdf_to_json_text_extraction_{pdf_extractor_name}_summary.md"

    # Write all collected lines to the Markdown file
    with output_md.open("w", encoding="utf-8") as out:
        out.write("\n".join(all_lines))

    print(f"Saved combined Markdown report to {output_md}")

if __name__ == "__main__":
    
    check_folders_text_extraction(DATA_DIR, JSON_DIR, max_files_to_process=max_files_to_process)
    
    json_to_csv(
        json_dir=Path("outputs/tests"), 
        output_dir=Path("outputs/tests"), 
        pdf_extractor_name=method
    )

    combine_json_reports_to_markdown(
        json_dir=Path("outputs/tests"),
        output_dir=Path("outputs/tests"),
        pdf_extractor_name=method
    )
    
    # Cleanup: delete all JSON files in OUTPUT_TESTS_DIR
    OUTPUT_TESTS_DIR = Path("outputs/tests")
    for json_file in OUTPUT_TESTS_DIR.glob("*.json"):
        try:
            json_file.unlink()
            print(f"Deleted {json_file.name}")
        except Exception as e:
            print(f"⚠️ Could not delete {json_file.name}: {e}")