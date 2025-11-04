# %%
from pathlib import Path
from statschat import load_config
import PyPDF2
import json

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
def get_pdf_page_counts(directory: Path):
    """
    Loop through all PDF files in a directory and return a dictionary
    with filenames and their page counts using PyPDF2.

    Args:
        directory (Path): Path to the directory containing PDF files.

    Returns:
        dict: Dictionary with PDF filenames as keys and page counts as values.
    """
    # Initialize an empty dictionary to store page counts for each PDF
    pdf_page_counts = {}

    # Iterate over all PDF files in the specified directory
    for pdf_file in directory.glob("*.pdf"):
        print(f"Getting page count for: {pdf_file.name}")
        try:
            # Open the PDF file in binary read mode
            with open(pdf_file, "rb") as f:
                # Create a PdfReader object to read the PDF
                reader = PyPDF2.PdfReader(f)
                # Store the number of pages in the dictionary using the filename as the key
                pdf_page_counts[pdf_file.name] = len(reader.pages)
        except Exception as e:
            # Print an error message if the file couldn't be read
            print(f"Error reading {pdf_file.name}: {e}")

    # Return the dictionary containing filenames and their corresponding page counts
    return pdf_page_counts

# %%
def validate_page_splitting(json_folder: Path, expected_page_counts: dict):
    """
    Validates a collection of JSON files that describe PDF documents by performing two checks:
    
    1. Verifies that the filename extracted from the 'url' field in each JSON file matches (via substring) 
       one of the expected PDF filenames provided in the expected_page_counts dictionary.
    2. Confirms that the last 'page_number' listed in the 'content' array matches the expected total page count.

    This function is useful for ensuring consistency between metadata stored in JSON files and known PDF properties.

    Args:
        json_folder (Path): Path to the directory containing JSON files.
        expected_page_counts (dict): A dictionary mapping expected PDF filenames (with '.pdf' extension)
                                     to their correct total page counts.

    Returns:
        List[dict]: A list of dictionaries summarizing the validation results for each JSON file.
                    Each dictionary includes:
                        - 'json_file': Name of the JSON file.
                        - 'pdf_filename_in_json': Filename extracted from the 'url' field in converted JSON.
                        - 'matched_expected_filename': Confirms if pdf filename from expected_page_counts dictionary is in the json converted file.
                        - 'filename_match_found': Boolean indicating whether a match was found.
                        - 'last_page_number_from_json_content': The last page number found in JSON's 'content' list.
                        - 'expected_page_count_from_pdf': The expected page count from the dictionary.
                        - 'page_count_matches': Boolean indicating whether the page count matches in JSON and pdf.
                        - 'error': Present only if an exception occurred during processing.
    """
    results = []

    # Iterate over all JSON files in the specified folder
    for json_file in json_folder.glob("*.json"):
        print(f"Checking page splitting for JSON file: {json_file.name}")
        try:
            # Open and load the JSON file
            with open(json_file, "r", encoding="utf-8") as f:
                data = json.load(f)

            # Extract the 'url' and 'content' fields from the JSON
            url = data.get("url", "")
            content = data.get("content", [])

            # Get the last page number from the 'content' list, if available
            last_page = content[-1]["page_number"] if content else None

            # Extract the filename from the URL (assumes it's the last segment)
            filename_from_url = url.split("/")[-1]

            # Attempt to find a matching expected filename using substring logic
            matched_filename = None
            for expected_name in expected_page_counts:
                base_name = expected_name.replace(".pdf", "")
                if base_name in filename_from_url:
                    matched_filename = expected_name
                    break  # Stop at the first match

            # Retrieve the expected page count for the matched filename
            expected_pages = expected_page_counts.get(matched_filename)

            # Append the validation result for this JSON file
            results.append({
                "json_file": json_file.name,
                "pdf_filename_in_json": filename_from_url,
                "matched_expected_filename": matched_filename,
                "filename_match_found": matched_filename is not None,
                "last_page_number_from_json_content": last_page,
                "expected_page_count_from_pdf": expected_pages,
                "page_count_matches": last_page == expected_pages
            })

        except Exception as e:
            # If an error occurs, record it in the results
            results.append({
                "json_file": json_file.name,
                "error": str(e)
            })

    # Return the list of validation results
    return results


# %%
if __name__ == "__main__":
    # Get expected page counts from PDF files before conversion to JSON files
    expected_page_counts = get_pdf_page_counts(DATA_DIR)

    # Checking JSON conversions against expected page counts
    validation_results = validate_page_splitting(JSON_DIR, expected_page_counts)

    # Print results
    for result in validation_results:
        print(result)