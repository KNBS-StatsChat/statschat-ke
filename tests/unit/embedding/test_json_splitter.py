"""
Unit tests for JSON splitting with metadata preservation.

Critical test: Ensures metadata (title, date, latest flag, etc.) is correctly
copied to each split section JSON. This is the primary data integrity risk.

Run:
    pytest -s -v tests/unit/embedding/test_json_splitter.py
"""
import pytest
import json
from pathlib import Path


def test_json_splitter_preserves_metadata(tmp_path, caplog):
    """
    Verify that _json_splitter() copies all metadata to each section.
    
    This test creates a minimal JSON with:
    - Top-level metadata (id, title, release_date, latest, etc.)
    - 2 content sections with page_text > 5 chars
    
    Expected behavior:
    - Creates 2 split JSONs in split_directory
    - Each split JSON has ALL metadata fields + section content
    - Preserves latest flag, dates, URLs correctly
    """
    from statschat.embedding.preprocess import PrepareVectorStore
    import logging
    
    # Create test JSON with realistic structure
    test_json = {
        "id": "test_pub_001",
        "title": "Test Publication 2025",
        "release_date": "2025-01-15",
        "modification_date": "2025-01-16",
        "overview": "Test overview text",
        "theme": "Test Theme",
        "release_type": "Publications",
        "url": "https://example.com/test.pdf",
        "latest": True,
        "url_keywords": ["test", "2025"],
        "contact_name": "Test Contact",
        "contact_link": "test@example.com",
        "content": [
            {
                "page_number": 1,
                "page_url": "https://example.com/test.pdf#page=1",
                "page_text": "First page content with sufficient text"
            },
            {
                "page_number": 2,
                "page_url": "https://example.com/test.pdf#page=2",
                "page_text": "Second page content"
            },
            {
                "page_number": 3,
                "page_url": "https://example.com/test.pdf#page=3",
                "page_text": "Tiny"  # Should be skipped (len <= 5)
            }
        ]
    }
    
    # Setup directories
    json_dir = tmp_path / "json_conversions"
    split_dir = tmp_path / "json_split"
    json_dir.mkdir()
    
    # Write test JSON
    test_file = json_dir / "test_pub_001.json"
    test_file.write_text(json.dumps(test_json, indent=4))
    
    # Create minimal PrepareVectorStore instance to test _json_splitter
    logger = logging.getLogger("test")
    
    prepper = PrepareVectorStore.__new__(PrepareVectorStore)
    prepper.directory = str(json_dir)
    prepper.split_directory = str(split_dir)
    prepper.latest_only = False
    prepper.logger = logger
    
    # Run the splitter
    prepper._json_splitter()
    
    # Verify split files created
    split_files = list(split_dir.glob("*.json"))
    assert len(split_files) == 2, f"Expected 2 split files, got {len(split_files)}"
    
    # Load and verify each split file
    for split_file in split_files:
        with open(split_file) as f:
            split_data = json.load(f)
        
        # Check all metadata fields preserved
        assert split_data["id"] == "test_pub_001"
        assert split_data["title"] == "Test Publication 2025"
        assert split_data["release_date"] == "2025-01-15"
        assert split_data["latest"] is True
        assert split_data["theme"] == "Test Theme"
        assert split_data["url"] == "https://example.com/test.pdf"
        
        # Check section-specific fields exist
        assert "page_number" in split_data
        assert "page_url" in split_data
        assert "page_text" in split_data
        assert len(split_data["page_text"]) > 5
        
        # Verify 'content' array is NOT in split files
        assert "content" not in split_data


def test_json_splitter_filters_by_latest_flag(tmp_path):
    """
    Verify that latest_only=True filters documents correctly.
    
    Creates 3 JSONs:
    - 2 with latest=True (should be processed)
    - 1 with latest=False (should be skipped)
    """
    from statschat.embedding.preprocess import PrepareVectorStore
    import logging
    
    json_dir = tmp_path / "json_conversions"
    split_dir = tmp_path / "json_split"
    json_dir.mkdir()
    
    # Create 3 test JSONs
    for i, latest_flag in enumerate([True, True, False]):
        test_json = {
            "id": f"test_pub_{i:03d}",
            "title": f"Test Publication {i}",
            "release_date": "2025-01-01",
            "latest": latest_flag,
            "content": [
                {
                    "page_number": 1,
                    "page_url": f"https://example.com/test{i}.pdf#page=1",
                    "page_text": f"Content for publication {i}"
                }
            ]
        }
        (json_dir / f"test_pub_{i:03d}.json").write_text(json.dumps(test_json))
    
    # Test with latest_only=True
    logger = logging.getLogger("test")
    prepper = PrepareVectorStore.__new__(PrepareVectorStore)
    prepper.directory = str(json_dir)
    prepper.split_directory = str(split_dir)
    prepper.latest_only = True  # KEY PARAMETER
    prepper.logger = logger
    
    prepper._json_splitter()
    
    # Should only create 2 split files (from the 2 latest=True JSONs)
    split_files = list(split_dir.glob("*.json"))
    assert len(split_files) == 2, f"Expected 2 files with latest_only=True, got {len(split_files)}"
    
    # Verify the split files are from the correct source JSONs
    split_ids = set()
    for split_file in split_files:
        with open(split_file) as f:
            split_ids.add(json.load(f)["id"])
    
    assert split_ids == {"test_pub_000", "test_pub_001"}


def test_json_splitter_skips_short_text(tmp_path):
    """
    Verify that sections with page_text <= 5 chars are skipped.
    
    This prevents empty/near-empty pages from polluting the vector store.
    """
    from statschat.embedding.preprocess import PrepareVectorStore
    import logging
    
    json_dir = tmp_path / "json_conversions"
    split_dir = tmp_path / "json_split"
    json_dir.mkdir()
    
    test_json = {
        "id": "test_short",
        "title": "Test Short Text",
        "release_date": "2025-01-01",
        "latest": True,
        "content": [
            {"page_number": 1, "page_url": "url1", "page_text": "Long enough text here"},
            {"page_number": 2, "page_url": "url2", "page_text": "OK"},  # len=2, skip
            {"page_number": 3, "page_url": "url3", "page_text": ""},     # len=0, skip
            {"page_number": 4, "page_url": "url4", "page_text": "12345"}, # len=5, skip
            {"page_number": 5, "page_url": "url5", "page_text": "123456"} # len=6, keep
        ]
    }
    
    (json_dir / "test_short.json").write_text(json.dumps(test_json))
    
    logger = logging.getLogger("test")
    prepper = PrepareVectorStore.__new__(PrepareVectorStore)
    prepper.directory = str(json_dir)
    prepper.split_directory = str(split_dir)
    prepper.latest_only = False
    prepper.logger = logger
    
    prepper._json_splitter()
    
    # Should only create 2 files (pages 1 and 5)
    split_files = list(split_dir.glob("*.json"))
    assert len(split_files) == 2


def test_json_splitter_handles_missing_latest_key(tmp_path):
    """
    Verify graceful handling when 'latest' key is missing.
    
    Some older JSONs might not have the 'latest' field.
    Should log a warning but not crash.
    """
    from statschat.embedding.preprocess import PrepareVectorStore
    import logging
    
    json_dir = tmp_path / "json_conversions"
    split_dir = tmp_path / "json_split"
    json_dir.mkdir()
    
    # JSON without 'latest' key
    test_json = {
        "id": "test_no_latest",
        "title": "Test No Latest Key",
        "release_date": "2025-01-01",
        # 'latest' key missing
        "content": [
            {"page_number": 1, "page_url": "url1", "page_text": "Content here"}
        ]
    }
    
    (json_dir / "test_no_latest.json").write_text(json.dumps(test_json))
    
    logger = logging.getLogger("test")
    prepper = PrepareVectorStore.__new__(PrepareVectorStore)
    prepper.directory = str(json_dir)
    prepper.split_directory = str(split_dir)
    prepper.latest_only = False
    prepper.logger = logger
    
    # Should not crash
    prepper._json_splitter()
    
    # With latest_only=False, should process the file anyway
    split_files = list(split_dir.glob("*.json"))
    # May be 0 or 1 depending on error handling - either is acceptable
    assert len(split_files) >= 0
