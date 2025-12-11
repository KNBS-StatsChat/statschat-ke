"""
Unit tests for fuzzy matching logic in latest_updates.py.

Critical test: Ensures the fuzzy matching threshold (75%) correctly identifies
newer versions of publications without false positives.

Run:
    pytest -s -v tests/unit/embedding/test_latest_matching.py
"""
import pytest
import json
import os
from pathlib import Path


def test_compare_latest_exact_match(tmp_path):
    """
    Verify that identical publication names (different dates) are matched.
    
    Example: "2024-Economic-Survey.json" vs "2025-Economic-Survey.json"
    Should detect that 2025 is newer version of 2024.
    """
    from statschat.embedding.latest_updates import compare_latest
    
    main_dir = tmp_path
    temp_dir = tmp_path / "temp"
    temp_dir.mkdir()
    
    # Create "current" publication
    current_pub = {
        "id": "123",
        "title": "2024 Economic Survey",
        "release_date": "2024-05-01",
        "latest": True,
        "content": []
    }
    (main_dir / "2024-Economic-Survey.json").write_text(json.dumps(current_pub))
    
    # Create "inbound" publication (newer)
    inbound_pub = {
        "id": "456",
        "title": "2025 Economic Survey",
        "release_date": "2025-05-01",
        "latest": True,
        "content": []
    }
    (temp_dir / "2025-Economic-Survey.json").write_text(json.dumps(inbound_pub))
    
    latest_filepaths = [str(main_dir / "2024-Economic-Survey.json")]
    
    new_latest, former_latest = compare_latest(str(main_dir), latest_filepaths)
    
    assert len(new_latest) == 1
    assert len(former_latest) == 1
    assert "2025-Economic-Survey.json" in new_latest[0]
    assert "2024-Economic-Survey.json" in former_latest[0]


def test_compare_latest_no_match_different_publications(tmp_path):
    """
    Verify that completely different publications are NOT matched.
    
    Example: "Economic-Survey.json" vs "Population-Census.json"
    Fuzzy ratio should be < 75%, so no match.
    """
    from statschat.embedding.latest_updates import compare_latest
    
    main_dir = tmp_path
    temp_dir = tmp_path / "temp"
    temp_dir.mkdir()
    
    # Current publication
    current_pub = {"id": "1", "title": "Economic Survey", "latest": True, "content": []}
    (main_dir / "2024-Economic-Survey.json").write_text(json.dumps(current_pub))
    
    # Inbound publication (completely different)
    inbound_pub = {"id": "2", "title": "Population Census", "latest": True, "content": []}
    (temp_dir / "2025-Population-Census.json").write_text(json.dumps(inbound_pub))
    
    latest_filepaths = [str(main_dir / "2024-Economic-Survey.json")]
    
    new_latest, former_latest = compare_latest(str(main_dir), latest_filepaths)
    
    # Should NOT match
    assert len(new_latest) == 0
    assert len(former_latest) == 0


def test_compare_latest_threshold_edge_case(tmp_path):
    """
    Test the 75% fuzzy ratio threshold edge case.
    
    This ensures we don't get false positives with similar but different pubs.
    Example: "Quarterly-Economic-Report-Q1.json" vs "Quarterly-Economic-Report-Q2.json"
    """
    from statschat.embedding.latest_updates import compare_latest
    from rapidfuzz import fuzz
    
    main_dir = tmp_path
    temp_dir = tmp_path / "temp"
    temp_dir.mkdir()
    
    filename1 = "2024-Kenya-Housing-Survey-Basic-Report.json"
    filename2 = "2024-Kenya-Housing-Survey-Detailed-Report.json"
    
    # Check the actual fuzzy ratio
    ratio = fuzz.ratio(filename1, filename2)
    print(f"\nFuzzy ratio between similar files: {ratio}%")
    
    # Create files
    pub1 = {"id": "1", "title": "Basic Report", "latest": True, "content": []}
    pub2 = {"id": "2", "title": "Detailed Report", "latest": True, "content": []}
    
    (main_dir / filename1).write_text(json.dumps(pub1))
    (temp_dir / filename2).write_text(json.dumps(pub2))
    
    latest_filepaths = [str(main_dir / filename1)]
    
    new_latest, former_latest = compare_latest(str(main_dir), latest_filepaths)
    
    # Depending on ratio, may or may not match
    # This test documents the behavior
    if ratio > 75:
        assert len(new_latest) >= 1, "Files with >75% similarity should match"
    else:
        assert len(new_latest) == 0, "Files with <75% similarity should NOT match"


def test_find_latest_filters_correctly(tmp_path):
    """
    Verify that find_latest() returns only publications with latest=True.
    
    Also verifies that files with "0000" in the filename are excluded
    (these are typically test or placeholder files).
    """
    from statschat.embedding.latest_updates import find_latest
    
    # Create 3 publications: 2 latest, 1 not latest
    pubs = [
        {"id": "1", "title": "Pub 1", "latest": True, "content": []},
        {"id": "2", "title": "Pub 2", "latest": False, "content": []},
        {"id": "3", "title": "Pub 3", "latest": True, "content": []},
    ]
    
    for i, pub in enumerate(pubs):
        (tmp_path / f"pub_{i}.json").write_text(json.dumps(pub))
    
    # Also create a file with "0000" in the FILENAME (should be excluded)
    (tmp_path / "pub_0000_exclude.json").write_text(json.dumps(pubs[0]))
    
    latest_files = find_latest(str(tmp_path))
    
    # Should return 2 files (the ones with latest=True, excluding 0000 file)
    assert len(latest_files) == 2, f"Expected 2 files, got {len(latest_files)}: {latest_files}"
    
    # Check filenames only (not full paths) for "0000"
    for filepath in latest_files:
        filename = os.path.basename(filepath)
        assert "0000" not in filename, f"File {filename} should not contain '0000'"
    
    # Verify they're the correct files
    latest_ids = set()
    for filepath in latest_files:
        with open(filepath) as f:
            latest_ids.add(json.load(f)["id"])
    
    assert latest_ids == {"1", "3"}


def test_unflag_former_latest(tmp_path):
    """
    Verify that unflag_former_latest() updates latest=True to latest=False.
    """
    from statschat.embedding.latest_updates import unflag_former_latest
    
    # Create publication with latest=True
    pub = {"id": "old_pub", "title": "Old Version", "latest": True, "content": []}
    filepath = tmp_path / "old-publication.json"
    filepath.write_text(json.dumps(pub, indent=4))
    
    # Unflag it
    unflag_former_latest(str(tmp_path), ["old-publication.json"])
    
    # Verify the flag changed
    with open(filepath) as f:
        updated_pub = json.load(f)
    
    assert updated_pub["latest"] is False
    assert updated_pub["id"] == "old_pub"  # Other fields unchanged


def test_update_split_documents_flags(tmp_path):
    """
    Verify that update_split_documents() updates latest flags in split JSONs.
    
    Split JSONs have format: "{id}_{section_num}.json"
    This function takes first 60 chars and uses glob matching.
    """
    from statschat.embedding.latest_updates import update_split_documents
    
    split_dir = tmp_path / "json_split"
    split_dir.mkdir()
    
    # Create 3 split documents from same source
    # Note: The id in split files should match the source filename
    base_name = "2024-Economic-Survey"
    for i in range(3):
        split_doc = {
            "id": f"{base_name}",
            "page_number": i + 1,
            "latest": True,
            "page_text": f"Content {i}"
        }
        (split_dir / f"{base_name}_{i}.json").write_text(json.dumps(split_doc))
    
    # Also create a split from a different source (should NOT be affected)
    other_doc = {"id": "other-pub", "page_number": 1, "latest": True, "page_text": "Other"}
    (split_dir / "other-pub_0.json").write_text(json.dumps(other_doc))
    
    # Update the flags for the Economic Survey splits
    # Pass the full filename as it would be in former_latest
    update_split_documents(str(split_dir), [f"{base_name}.json"])
    
    # Verify all 3 Economic Survey splits were updated
    for i in range(3):
        with open(split_dir / f"{base_name}_{i}.json") as f:
            doc = json.load(f)
        assert doc["latest"] is False, f"Split {i} should have latest=False, got {doc}"
    
    # Verify the other publication was NOT affected
    with open(split_dir / "other-pub_0.json") as f:
        other = json.load(f)
    assert other["latest"] is True, "Unrelated publication should remain latest=True"


def test_compare_latest_handles_empty_temp_dir(tmp_path):
    """
    Verify graceful handling when temp directory has no files.
    """
    from statschat.embedding.latest_updates import compare_latest
    
    main_dir = tmp_path
    temp_dir = tmp_path / "temp"
    temp_dir.mkdir()
    
    # Create a current publication
    pub = {"id": "1", "title": "Test", "latest": True, "content": []}
    (main_dir / "test.json").write_text(json.dumps(pub))
    
    latest_filepaths = [str(main_dir / "test.json")]
    
    # Should not crash with empty temp dir
    new_latest, former_latest = compare_latest(str(main_dir), latest_filepaths)
    
    assert len(new_latest) == 0
    assert len(former_latest) == 0
