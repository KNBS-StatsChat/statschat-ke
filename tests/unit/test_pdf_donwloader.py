"""
Refined unit tests for statschat.pdf_processing.pdf_downloader

- Mocks network + config; isolates filesystem via tmp_path.
- Uses VALID <a href> anchors so BeautifulSoup selectors match downloader logic.
- Asserts the expected URL call flow (listing → report → PDF).
- Enforces url_dict.json schema: { "sample.pdf": {"pdf_url", "report_page"} }.
- In UPDATE: writes only new entries to latest_pdf_downloads/ and saves the new PDF there.
- Negative path: UPDATE with no original dict exits/returns cleanly without artifacts.

Run:
    pytest -s -v tests/unit/test_pdf_downloader.py
"""
import pytest
import json
import importlib
import logging
from unittest.mock import MagicMock

# Configure logging for the test module
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def _build_side_effect(report_listing_html, report_page_html, pdf_bytes):
    """
    Creates a side effect function for mocking `requests.get` in unit tests.

    This function returns a callable that simulates HTTP responses based on the requested URL.
    It is intended to be used as the `side_effect` for a mocked `requests.get` call, allowing
    different responses for specific URLs during testing.

    Args:
        report_listing_html (str): The HTML content to return for the report listing page.
        report_page_html (str): The HTML content to return for an individual report page.
        pdf_bytes (bytes): The binary content to return for the PDF file download.

    Returns:
        Callable: A function that takes a URL and returns a mock response object with
        appropriate `status_code` and `content` attributes based on the URL.
    """
    def side_effect(url, *a, **k):
        url = str(url)
        resp = MagicMock()
        if url.endswith("/all-reports/page/1/"):
            resp.status_code = 200
            resp.content = report_listing_html.encode()
        elif url.endswith("/reports/report-1/"):
            resp.status_code = 200
            resp.content = report_page_html.encode()
        elif url.endswith("/files/sample.pdf"):
            resp.status_code = 200
            resp.content = pdf_bytes
        else:
            resp.status_code = 404
            resp.content = b""
        return resp
    return side_effect

def _assert_calls(mock_get):
    """
    Checks that the mock 'get' method was called with specific URLs during the test.

    Args:
        mock_get (unittest.mock.Mock): The mocked 'get' method whose call arguments are to be checked.

    Raises:
        AssertionError: If any of the expected URLs were not called.
    """
    called = [c.args[0] for c in mock_get.call_args_list]
    logger.info(f"URLs called: {called}")
    assert any(str(u).endswith("/all-reports/page/1/") for u in called)
    assert any(str(u).endswith("/reports/report-1/") for u in called)
    assert any(str(u).endswith("/files/sample.pdf") for u in called)

def _assert_schema_and_values(d, filename="sample.pdf"):
    """
    Assert that the given dictionary `d` contains the expected schema and values for a PDF file entry.

    Args:
        d (dict): The dictionary to validate, expected to contain file information keyed by filename.
        filename (str, optional): The filename to check within the dictionary. Defaults to "sample.pdf".

    Raises:
        AssertionError: If the dictionary does not contain the expected filename, schema, or value formats.
    """
    assert filename in d
    assert set(d[filename].keys()) == {"pdf_url","report_page"}
    assert d[filename]["pdf_url"].endswith("/files/sample.pdf")
    assert d[filename]["report_page"].endswith("/reports/report-1/")

def _silence_tqdm(monkeypatch):
    """
    Temporarily replaces the tqdm progress bar in the pdf_downloader module with a no-op during tests.

    This function uses pytest's monkeypatch fixture to substitute the tqdm function in
    the statschat.pdf_processing.pdf_downloader module, ensuring that progress bars do not
    appear in test output.

    Args:
        monkeypatch: The pytest monkeypatch fixture used to modify or replace attributes for testing.
    """
    import statschat.pdf_processing.pdf_downloader as dl
    monkeypatch.setattr(dl, "tqdm", lambda it, **k: it)

def test_pdf_download_and_url_dict_setup(tmp_path, monkeypatch):
    """
    Test the SETUP mode of the PDF downloader.
    This test verifies that when the application is run in SETUP mode:
    - A PDF file is downloaded from a mock URL and saved in the expected directory.
    - The url_dict.json file is created in the pdf_downloads directory with the correct schema and values.
    - The correct configuration and working directory are used via monkeypatching.
    - The requests to external URLs are mocked to return predefined HTML and PDF content.
    - The number and content of downloaded PDFs, as well as the contents of url_dict.json, are validated.
    Args:
        tmp_path (pathlib.Path): Temporary directory provided by pytest for file operations.
        monkeypatch (pytest.MonkeyPatch): Pytest fixture for patching and mocking.
    Raises:
        AssertionError: If the PDF is not downloaded correctly, or url_dict.json does not match the expected schema and values.
    """
    logger.info("Running SETUP mode test...")
    mock_config = {"preprocess":{"mode":"SETUP"},"app":{"page_start":1,"page_end":1}}
    monkeypatch.setattr("statschat.load_config", lambda *a, **k: mock_config)
    monkeypatch.setattr("pathlib.Path.cwd", lambda: tmp_path)
    _silence_tqdm(monkeypatch)

    listing = '<a href="https://www.knbs.or.ke/reports/report-1/">Report 1</a>'
    report = '<a href="https://www.knbs.or.ke/files/sample.pdf">Download PDF</a>'
    pdf_bytes = b"%PDF-1.4 sample"

    mock_get = MagicMock()
    mock_get.side_effect = _build_side_effect(listing, report, pdf_bytes)
    monkeypatch.setattr("statschat.pdf_processing.pdf_downloader.requests.get", mock_get)

    import statschat.pdf_processing.pdf_downloader as dl
    importlib.reload(dl)
    dl.main()

    _assert_calls(mock_get)
    data_dir = tmp_path / "data" / "pdf_downloads"
    pdfs = list(data_dir.glob("*.pdf"))
    logger.info(f"PDFs found in SETUP: {[str(p) for p in pdfs]}")
    assert len(pdfs) == 1
    assert pdfs[0].read_bytes() == pdf_bytes
    url_dict = json.loads((data_dir / "url_dict.json").read_text())
    logger.info(f"url_dict.json contents: {url_dict}")
    _assert_schema_and_values(url_dict)

def test_pdf_update_mode_writes_only_new_entries(tmp_path, monkeypatch):
    """
    Test that in UPDATE mode, only new PDF entries are written to the latest_pdf_downloads directory.
    This test sets up a mock configuration for UPDATE mode and simulates an environment where one PDF
    ("existing.pdf") already exists in the original url_dict.json. It mocks HTTP requests to simulate
    the discovery and download of a new PDF ("sample.pdf"). After running the downloader's main function,
    the test asserts that:
        - The latest_pdf_downloads/url_dict.json contains only the new entry ("sample.pdf").
        - The downloaded PDF file matches the expected content.
        - The schema and values of the new entry are correct.
    """
    logger.info("Running UPDATE mode test (writes only new entries)...")
    mock_config = {"preprocess":{"mode":"UPDATE"},"app":{"page_start":1,"page_end":1}}
    monkeypatch.setattr("statschat.load_config", lambda *a, **k: mock_config)
    monkeypatch.setattr("pathlib.Path.cwd", lambda: tmp_path)
    _silence_tqdm(monkeypatch)

    base = tmp_path / "data"
    orig = base / "pdf_downloads"
    latest = base / "latest_pdf_downloads"
    orig.mkdir(parents=True); latest.mkdir(parents=True)
    (orig / "url_dict.json").write_text(json.dumps({
        "existing.pdf":{
            "pdf_url":"https://www.knbs.or.ke/files/existing.pdf",
            "report_page":"https://www.knbs.or.ke/reports/report-0/"
        }
    }))

    listing = '<a href="https://www.knbs.or.ke/reports/report-1/">Report 1</a>'
    report = '<a href="https://www.knbs.or.ke/files/sample.pdf">Download PDF</a>'
    pdf_bytes = b"%PDF-1.4 sample"

    mock_get = MagicMock()
    mock_get.side_effect = _build_side_effect(listing, report, pdf_bytes)
    monkeypatch.setattr("statschat.pdf_processing.pdf_downloader.requests.get", mock_get)

    import statschat.pdf_processing.pdf_downloader as dl
    importlib.reload(dl)
    dl.main()

    _assert_calls(mock_get)

    # Expect latest url_dict.json
    latest_dict_path = latest / "url_dict.json"
    logger.info(f"Checking for {latest_dict_path}")
    assert latest_dict_path.exists()
    latest_dict = json.loads(latest_dict_path.read_text())
    logger.info(f"url_dict.json contents in UPDATE: {latest_dict}")
    assert list(latest_dict.keys()) == ["sample.pdf"]
    _assert_schema_and_values(latest_dict,"sample.pdf")
    assert (latest / "sample.pdf").read_bytes() == pdf_bytes

def test_update_mode_no_original_dict_exits_cleanly(tmp_path, monkeypatch):
    """
    Test that the PDF downloader exits cleanly in UPDATE mode when no original url_dict.json exists.
    This test simulates running the downloader in UPDATE mode without an existing url_dict.json file.
    It mocks configuration loading, current working directory, and HTTP requests. The test asserts that
    the program exits (raises SystemExit) and does not create a new url_dict.json file in the latest
    downloads directory.
    """
    logger.info("Running UPDATE mode test (no original dict, should exit)...")
    mock_config = {"preprocess":{"mode":"UPDATE"},"app":{"page_start":1,"page_end":1}}
    monkeypatch.setattr("statschat.load_config", lambda *a, **k: mock_config)
    monkeypatch.setattr("pathlib.Path.cwd", lambda: tmp_path)
    _silence_tqdm(monkeypatch)

    base = tmp_path / "data"
    latest = base / "latest_pdf_downloads"
    latest.mkdir(parents=True)

    listing = '<a href="https://www.knbs.or.ke/reports/report-1/">Report 1</a>'
    report = '<a href="https://www.knbs.or.ke/files/sample.pdf">Download PDF</a>'
    pdf_bytes = b"%PDF-1.4 sample"
    mock_get = MagicMock()
    mock_get.side_effect = _build_side_effect(listing, report, pdf_bytes)
    monkeypatch.setattr("statschat.pdf_processing.pdf_downloader.requests.get", mock_get)

    import statschat.pdf_processing.pdf_downloader as dl
    importlib.reload(dl)
    with pytest.raises(SystemExit):
        dl.main()

    # No latest url_dict.json should be created (since original does not exist)
    logger.info(f"Checking that {latest / 'url_dict.json'} does not exist")
    assert not (latest / "url_dict.json").exists()