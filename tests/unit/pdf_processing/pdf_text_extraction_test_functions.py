"""Script to check text extraction word matches between PDFs and their JSON conversions with different extraction methods."""

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
OUTPUT_TESTS_DIR = Path.cwd().joinpath("outputs/tests")
OUTPUT_TESTS_DIR.mkdir(exist_ok=True, parents=True)

# %%
# Initialize spell checker
spell = SpellChecker()

def extract_pdf_text(pdf_path: Path, method: str = "pypdf2") -> dict:
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


def compare_texts(json_text, pdf_text, page_num=None, pdf_file=None, json_file=None, log_dir=None):
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

    Returns:
        list or None: A list of differing lines (excluding numeric ones), or None if no differences.
    """
    header = f"\nComparing Page {page_num} of PDF: {pdf_file} vs JSON: {json_file}\n"
    pdf_section = f"----- PDF Text -----\n{pdf_text.strip() or '[Empty]'}\n"
    json_section = f"----- JSON Text -----\n{json_text.strip() or '[Empty]'}\n"

    # Print to console
    print(header + pdf_section + json_section)

    if log_dir:
    # Create a single log file per PDF
        log_path = log_dir / f"{pdf_file}_comparison.txt"
        with log_path.open("a", encoding="utf-8") as log_file:  # Use "a" to append
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


def check_file_pair_text(pdf_path: Path, json_path: Path, max_diff_examples: int = 5):
    """
    Compares the text content of a PDF file and its corresponding JSON file.
    Generates a structured report including:
        - Differences (excluding numeric lines)
        - Misspelled words
        - Irregular characters
        - Word-level extraction accuracy (%)
    Saves the report to outputs/tests/ as a JSON file.

    Args:
        pdf_path (Path): Path to the PDF file.
        json_path (Path): Path to the corresponding JSON file.
        max_diff_examples (int): Maximum number of diff lines to include per page.
    """
    print(f"\n🔍 Checking: {pdf_path.name} and {json_path.name}")
    pdf_texts = extract_pdf_text(pdf_path)

    with json_path.open('r', encoding='utf-8') as f:
        json_data = json.load(f)

    # Clear existing log file for this PDF
    log_path = OUTPUT_TESTS_DIR / f"{pdf_path.name}_comparison.txt"
    log_path.write_text("")

    file_report = {
        "pdf_file": pdf_path.name,
        "json_file": json_path.name,
        "pages": {}
    }

    for page in json_data['content']:
        page_num = page['page_number']
        json_text = page['page_text']
        pdf_text = pdf_texts.get(page_num, '')

        page_report = {
            "diff_count": 0,
            "diff_examples": [],
            "diff_occurrences": {},
            "misspelled": [],
            "irregular_chars": [],
            "accuracy_percent": None
        }

        # Compare text and record differences
        diff = compare_texts(
            json_text=json_text,
            pdf_text=pdf_text,
            page_num=page_num,
            pdf_file=pdf_path.name,
            json_file=json_path.name,
            log_dir=OUTPUT_TESTS_DIR
        )
        if diff:
            page_report["diff_count"] = len(diff)
            page_report["diff_examples"] = diff[:max_diff_examples]
            for line in diff:
                page_report["diff_occurrences"][line] = page_report["diff_occurrences"].get(line, 0) + 1

        # Check spelling and irregular characters
        misspelled, irregular = check_json_text(json_text)
        page_report["misspelled"] = list(misspelled)
        page_report["irregular_chars"] = irregular

        # Calculate word-level matches
        json_words = json_text.split()
        pdf_words = set(pdf_text.split())
        matched = [word for word in json_words if word in pdf_words]
        total = len(json_words)
        accuracy = (len(matched) / total * 100) if total > 0 else 0
        page_report["accuracy_percent"] = round(accuracy, 2)

        # Add page report to file report
        file_report["pages"][str(page_num)] = page_report

    output_path = OUTPUT_TESTS_DIR / f"{pdf_path.stem}_report.json"
    with output_path.open("w", encoding="utf-8") as out:
        json.dump(file_report, out, indent=2, ensure_ascii=False)

    print(f"✅ Saved report to {output_path}")


def check_folders_text_extraction(data_dir: Path, json_dir: Path, max_files: int | str = 2):
    """
    Iterates through PDF files in a directory and checks them against their
    corresponding JSON files. Limits processing to `max_files` pairs unless set to 'all'.

    Args:
        data_dir (Path): Directory containing PDF files.
        json_dir (Path): Directory containing JSON files.
        max_files (int or str): Maximum number of PDF–JSON pairs to process.
                                Use 'all' to process everything.
    """
    pdf_files = list(data_dir.glob('*.pdf'))
    processed_count = 0

    for pdf_file in pdf_files:
        if max_files != "all" and processed_count >= int(max_files):
            print(f"⏹️ Limit reached: Only processing {max_files} PDF files.")
            break

        json_file = json_dir / (pdf_file.stem + '.json')
        if json_file.exists():
            check_file_pair_text(pdf_path=pdf_file, json_path=json_file, max_diff_examples=3)
            processed_count += 1
        else:
            print(f"⚠️ JSON file missing for {pdf_file.name}")
            

def json_to_csv(json_dir: Path, output_dir: Path, pdf_extractor_name: str = "fitz"):
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
                "page": page_num,
                "diff_count": page_data["diff_count"],
                "misspelled": ", ".join(page_data["misspelled"]),
                "irregular_chars": ", ".join(page_data["irregular_chars"]),
                "word_matches_from_extraction": page_data.get("accuracy_percent", "")
            })

    # Define output filename using extractor name
    output_csv = output_dir / f"pdf_to_json_text_extraction_{pdf_extractor_name}_summary.csv"

    # Convert to DataFrame and save as CSV
    df = pd.DataFrame(rows)
    df.to_csv(output_csv, index=False)
    print(f"✅ Saved combined CSV to {output_csv}")
  
# %%
def combine_json_reports_to_markdown(json_dir: Path, output_md: Path):
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
        output_md (Path): Path to the combined Markdown file to be created.

    Returns:
        None. Writes the combined Markdown file to disk.
    """
    all_lines = ["# Combined Audit Report\n"]  # Start with a top-level heading

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
            all_lines.append(f"- **Word Matches**: {page_data.get('accuracy_percent', 'N/A')}%")

            # Include diff examples if available
            if page_data['diff_examples']:
                all_lines.append("- **Examples:**")
                all_lines.append("```diff")
                for line in page_data['diff_examples']:
                    all_lines.append(line)
                all_lines.append("```")

            # Include misspelled words if any
            if page_data['misspelled']:
                all_lines.append(f"- **Misspelled Words**: {', '.join(page_data['misspelled'])}")

            # Include irregular characters if any
            if page_data['irregular_chars']:
                all_lines.append(f"- **Irregular Characters**: {', '.join(page_data['irregular_chars'])}")

    # Write all collected lines to the Markdown file
    with output_md.open("w", encoding="utf-8") as out:
        out.write("\n".join(all_lines))

    print(f"✅ Saved combined Markdown report to {output_md}")

def combine_json_reports_to_markdown(json_dir: Path, output_dir: Path, pdf_extractor_name: str = "fitz"):
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
    all_lines = [f"# Combined Audit Report ({pdf_extractor_name})\n"]  # Top-level heading with extractor name

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
            all_lines.append(f"- **Word Matches**: {page_data.get('accuracy_percent', 'N/A')}%")

            # Include diff examples if available
            if page_data['diff_examples']:
                all_lines.append("- **Examples:**")
                all_lines.append("```diff")
                for line in page_data['diff_examples']:
                    all_lines.append(line)
                all_lines.append("```")

            # Include misspelled words if any
            if page_data['misspelled']:
                all_lines.append(f"- **Misspelled Words**: {', '.join(page_data['misspelled'])}")

            # Include irregular characters if any
            if page_data['irregular_chars']:
                all_lines.append(f"- **Irregular Characters**: {', '.join(page_data['irregular_chars'])}")

    # Define output Markdown filename using extractor name
    output_md = output_dir / f"pdf_to_json_text_extraction_{pdf_extractor_name}_summary.md"

    # Write all collected lines to the Markdown file
    with output_md.open("w", encoding="utf-8") as out:
        out.write("\n".join(all_lines))

    print(f"✅ Saved combined Markdown report to {output_md}")


if __name__ == "__main__":
    
    # Process only 3 files
    check_folders_text_extraction(DATA_DIR, JSON_DIR, max_files=2)
    
    json_to_csv(
        json_dir=Path("outputs/tests"), 
        output_dir=Path("outputs/tests"), 
        pdf_extractor_name="pypdf2"
    )

    combine_json_reports_to_markdown(
        json_dir=Path("outputs/tests"),
        output_dir=Path("outputs/tests"),
        pdf_extractor_name='pypdf2'
    )
    
    # Cleanup: delete all JSON files in OUTPUT_TESTS_DIR
    OUTPUT_TESTS_DIR = Path("outputs/tests")
    for json_file in OUTPUT_TESTS_DIR.glob("*.json"):
        try:
            json_file.unlink()
            print(f"🗑️ Deleted {json_file.name}")
        except Exception as e:
            print(f"⚠️ Could not delete {json_file.name}: {e}")