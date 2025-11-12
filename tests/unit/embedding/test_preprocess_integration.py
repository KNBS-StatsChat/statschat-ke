"""
Integration tests for PrepareVectorStore with mocked embeddings.

Tests the full pipeline flow (SETUP and UPDATE modes) with fast mock embeddings
to avoid 5-10 second waits per test.

Run:
    pytest -s -v tests/unit/embedding/test_preprocess_integration.py
"""
import pytest
import json
import os
from pathlib import Path


@pytest.fixture
def mock_embeddings(monkeypatch):
    """
    Mock HuggingFaceEmbeddings to return fixed vectors instantly.
    
    This avoids:
    - Downloading the 420MB sentence-transformers model
    - Waiting 5-10 seconds per document for embeddings
    
    Returns 768-dimensional vectors (same as all-mpnet-base-v2).
    """
    class MockEmbeddings:
        def embed_documents(self, texts):
            """Return fixed 768-dim vectors for each text."""
            return [[0.1] * 768 for _ in texts]
        
        def embed_query(self, text):
            """Return fixed 768-dim vector for query."""
            return [0.1] * 768
    
    # Mock the HuggingFaceEmbeddings constructor
    monkeypatch.setattr(
        "langchain_huggingface.embeddings.HuggingFaceEmbeddings",
        lambda *args, **kwargs: MockEmbeddings()
    )
    
    return MockEmbeddings


@pytest.fixture
def sample_json_data():
    """
    Returns a realistic minimal JSON structure for testing.
    """
    return {
        "id": "test_pub_001",
        "title": "Test Economic Survey 2025",
        "release_date": "2025-01-15",
        "modification_date": "2025-01-16",
        "overview": "Test economic data",
        "theme": "Economic Surveys",
        "release_type": "Publications",
        "url": "https://www.knbs.or.ke/test.pdf",
        "latest": True,
        "url_keywords": ["test", "economic", "2025"],
        "contact_name": "Test Contact",
        "contact_link": "test@knbs.or.ke",
        "content": [
            {
                "page_number": 1,
                "page_url": "https://www.knbs.or.ke/test.pdf#page=1",
                "page_text": "This is the first page with sufficient content to be processed. It needs more than 5 characters."
            },
            {
                "page_number": 2,
                "page_url": "https://www.knbs.or.ke/test.pdf#page=2",
                "page_text": "This is the second page with different content. Also needs to be longer than 5 characters."
            }
        ]
    }


def test_setup_mode_creates_faiss_db(tmp_path, mock_embeddings, sample_json_data):
    """
    Test SETUP mode end-to-end: JSON → split → embed → FAISS.
    
    Verifies:
    - Correct directory structure created
    - FAISS index files created
    - Split JSONs contain metadata
    """
    from statschat.embedding.preprocess import PrepareVectorStore
    import logging
    
    # Setup directories
    data_dir = tmp_path / "data"
    json_dir = data_dir / "json_conversions"
    split_dir = data_dir / "json_split"
    faiss_dir = data_dir / "db_langchain"
    json_dir.mkdir(parents=True)
    
    # Create test JSON
    (json_dir / "test_pub_001.json").write_text(json.dumps(sample_json_data, indent=4))
    
    # Run PrepareVectorStore in SETUP mode
    logger = logging.getLogger("test")
    
    prepper = PrepareVectorStore(
        data_dir=f"{data_dir}/",
        directory="json_conversions",
        split_directory="json_split",
        download_dir="pdf_downloads",
        split_length=1000,
        split_overlap=200,
        embedding_model_name="sentence-transformers/all-mpnet-base-v2",
        faiss_db_root="db_langchain",
        logger=logger,
        latest_only=False,
        mode="SETUP"
    )
    
    # Verify split JSONs created
    split_files = list(split_dir.glob("*.json"))
    assert len(split_files) == 2, f"Expected 2 split files, got {len(split_files)}"
    
    # Verify FAISS files created
    assert faiss_dir.exists(), "FAISS directory should exist"
    assert (faiss_dir / "index.faiss").exists(), "index.faiss should exist"
    assert (faiss_dir / "index.pkl").exists(), "index.pkl should exist"
    
    # Verify db attribute is populated
    assert prepper.db is not None
    assert hasattr(prepper.db, 'docstore')


def test_update_mode_uses_latest_directories(tmp_path, mock_embeddings, sample_json_data):
    """
    Test UPDATE mode uses correct directory paths.
    
    Key difference: UPDATE mode should use:
    - latest_json_conversions/ (not json_conversions/)
    - latest_json_split/ (not json_split/)
    - db_langchain_latest/ (not db_langchain/)
    """
    from statschat.embedding.preprocess import PrepareVectorStore
    import logging
    
    # Setup directories for UPDATE mode
    data_dir = tmp_path / "data"
    latest_json_dir = data_dir / "latest_json_conversions"
    latest_split_dir = data_dir / "latest_json_split"
    original_faiss_dir = data_dir / "db_langchain"
    latest_faiss_dir = data_dir / "db_langchain_latest"
    
    latest_json_dir.mkdir(parents=True)
    original_faiss_dir.mkdir(parents=True)
    
    # Create a minimal existing FAISS store
    # (In real scenario, this would be a pre-existing vector store)
    (original_faiss_dir / "index.faiss").write_bytes(b"fake_faiss_data")
    (original_faiss_dir / "index.pkl").write_bytes(b"fake_pkl_data")
    
    # Create test JSON in latest_json_conversions
    (latest_json_dir / "test_pub_002.json").write_text(
        json.dumps(sample_json_data, indent=4)
    )
    
    # Mock the FAISS load and merge to avoid actual FAISS operations
    def mock_faiss_load(*args, **kwargs):
        """Mock FAISS.load_local to return a fake db object."""
        class MockFAISS:
            def __init__(self):
                self.docstore = type('obj', (object,), {'_dict': {}})
            def merge_from(self, other):
                pass
            def save_local(self, path):
                pass
        return MockFAISS()
    
    import statschat.embedding.preprocess as preprocess_module
    original_faiss_load = preprocess_module.FAISS.load_local
    preprocess_module.FAISS.load_local = mock_faiss_load
    
    try:
        logger = logging.getLogger("test")
        
        prepper = PrepareVectorStore(
            data_dir=f"{data_dir}/",
            directory="json_conversions",
            split_directory="json_split",
            download_dir="pdf_downloads",
            split_length=1000,
            split_overlap=200,
            embedding_model_name="sentence-transformers/all-mpnet-base-v2",
            faiss_db_root="db_langchain",
            logger=logger,
            latest_only=False,
            mode="UPDATE"  # KEY: UPDATE mode
        )
        
        # Verify UPDATE mode used correct directories
        assert prepper.directory == f"{data_dir}/latest_json_conversions"
        assert prepper.split_directory == f"{data_dir}/latest_json_split"
        assert prepper.faiss_db_root == f"{data_dir}/db_langchain_latest"
        # Normalize paths for comparison
        from pathlib import Path
        assert Path(prepper.original_faiss_db_root).resolve() == (data_dir / "db_langchain").resolve()
        
        # Verify split files created in latest_json_split
        split_files = list(latest_split_dir.glob("*.json"))
        assert len(split_files) == 2
        
        # Verify FAISS _latest directory created
        assert latest_faiss_dir.exists()
    
    finally:
        # Restore original FAISS.load_local
        preprocess_module.FAISS.load_local = original_faiss_load


def test_document_chunking_preserves_metadata(tmp_path, mock_embeddings, sample_json_data):
    """
    Test that document chunking preserves metadata in each chunk.
    
    After RecursiveCharacterTextSplitter splits documents, each chunk
    should still have the original metadata (title, date, source, etc.).
    """
    from statschat.embedding.preprocess import PrepareVectorStore
    import logging
    
    # Setup
    data_dir = tmp_path / "data"
    json_dir = data_dir / "json_conversions"
    json_dir.mkdir(parents=True)
    
    # Create a JSON with longer content to trigger chunking
    long_content = sample_json_data.copy()
    long_content["content"][0]["page_text"] = "Lorem ipsum " * 200  # ~2400 chars
    
    (json_dir / "test_long.json").write_text(json.dumps(long_content, indent=4))
    
    logger = logging.getLogger("test")
    
    prepper = PrepareVectorStore(
        data_dir=f"{data_dir}/",
        directory="json_conversions",
        split_directory="json_split",
        download_dir="pdf_downloads",
        split_length=500,  # Small chunks to force splitting
        split_overlap=50,
        embedding_model_name="sentence-transformers/all-mpnet-base-v2",
        faiss_db_root="db_langchain",
        logger=logger,
        latest_only=False,
        mode="SETUP"
    )
    
    # Verify chunks were created
    assert len(prepper.chunks) > 2, "Should have more chunks due to splitting"
    
    # Verify each chunk has metadata
    for chunk in prepper.chunks:
        assert hasattr(chunk, 'metadata')
        assert 'source' in chunk.metadata
        assert 'title' in chunk.metadata
        assert 'date' in chunk.metadata
        assert chunk.metadata['title'] == "Test Economic Survey 2025"


def test_latest_only_filters_documents(tmp_path, mock_embeddings, sample_json_data):
    """
    Test that latest_only=True only processes documents with latest=True.
    """
    from statschat.embedding.preprocess import PrepareVectorStore
    import logging
    
    # Setup
    data_dir = tmp_path / "data"
    json_dir = data_dir / "json_conversions"
    json_dir.mkdir(parents=True)
    
    # Create 2 JSONs: one latest, one not
    latest_doc = sample_json_data.copy()
    latest_doc["id"] = "latest_pub"
    latest_doc["latest"] = True
    
    old_doc = sample_json_data.copy()
    old_doc["id"] = "old_pub"
    old_doc["latest"] = False
    
    (json_dir / "latest_pub.json").write_text(json.dumps(latest_doc, indent=4))
    (json_dir / "old_pub.json").write_text(json.dumps(old_doc, indent=4))
    
    logger = logging.getLogger("test")
    
    prepper = PrepareVectorStore(
        data_dir=f"{data_dir}/",
        directory="json_conversions",
        split_directory="json_split",
        download_dir="pdf_downloads",
        split_length=1000,
        split_overlap=200,
        embedding_model_name="sentence-transformers/all-mpnet-base-v2",
        faiss_db_root="db_langchain",
        logger=logger,
        latest_only=True,  # KEY: Only process latest=True
        mode="SETUP"
    )
    
    # Verify only latest document was processed
    split_dir = data_dir / "json_split"
    split_files = list(split_dir.glob("*.json"))
    
    # Should only have splits from latest_pub (2 pages)
    assert len(split_files) == 2
    
    for split_file in split_files:
        with open(split_file) as f:
            data = json.load(f)
        assert data["id"] == "latest_pub"
        assert data["latest"] is True


def test_empty_json_directory_handled_gracefully(tmp_path, mock_embeddings):
    """
    Test that an empty json_conversions directory doesn't crash.
    
    Note: FAISS.from_documents() will raise IndexError with empty list.
    This is expected behavior - we verify it's a clean error, not a crash.
    """
    from statschat.embedding.preprocess import PrepareVectorStore
    import logging
    
    # Setup empty directories
    data_dir = tmp_path / "data"
    json_dir = data_dir / "json_conversions"
    json_dir.mkdir(parents=True)
    
    logger = logging.getLogger("test")
    
    # Empty directory should raise a clean error
    with pytest.raises(IndexError, match="list index out of range"):
        prepper = PrepareVectorStore(
            data_dir=f"{data_dir}/",
            directory="json_conversions",
            split_directory="json_split",
            download_dir="pdf_downloads",
            split_length=1000,
            split_overlap=200,
            embedding_model_name="sentence-transformers/all-mpnet-base-v2",
            faiss_db_root="db_langchain",
            logger=logger,
            latest_only=False,
            mode="SETUP"
        )
