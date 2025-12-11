"""
Shared fixtures for embedding tests.

This file provides common test fixtures and utilities used across
multiple embedding test modules.
"""
import pytest
import os


@pytest.fixture(autouse=True)
def set_test_env():
    """
    Set environment variables for all embedding tests.
    
    - Prevents HuggingFace model downloads during tests
    - Disables progress bars and verbose output
    """
    original_env = os.environ.copy()
    
    # Prevent model downloads
    os.environ["TRANSFORMERS_OFFLINE"] = "1"
    os.environ["HF_DATASETS_OFFLINE"] = "1"
    
    # Disable progress bars
    os.environ["TQDM_DISABLE"] = "1"
    
    yield
    
    # Restore original environment
    os.environ.clear()
    os.environ.update(original_env)


@pytest.fixture
def minimal_json_structure():
    """
    Returns the minimal required JSON structure for a KNBS publication.
    
    Use this as a base and modify as needed for specific tests.
    """
    return {
        "id": "test_pub",
        "title": "Test Publication",
        "release_date": "2025-01-01",
        "modification_date": "2025-01-01",
        "overview": "Test overview",
        "theme": "Test Theme",
        "release_type": "Publications",
        "url": "https://www.knbs.or.ke/test.pdf",
        "latest": True,
        "url_keywords": ["test"],
        "contact_name": "KNBS",
        "contact_link": "test@knbs.or.ke",
        "content": [
            {
                "page_number": 1,
                "page_url": "https://www.knbs.or.ke/test.pdf#page=1",
                "page_text": "Minimal content that is longer than 5 characters"
            }
        ]
    }
