"""Integration test for JSON -> Split -> Embed pipeline using PrepareVectorStore.

Creates small JSON fixtures, runs PrepareVectorStore in SETUP mode with mocked
embeddings/FAISS, and asserts split counts, latest flag preservation, and FAISS
index creation.
"""

import json


def test_embedding_pipeline_creates_splits_and_faiss(tmp_path, monkeypatch):
    from statschat.embedding import preprocess

    data_dir = tmp_path / "data"
    json_dir = data_dir / "json_conversions"
    split_dir = data_dir / "json_split"
    faiss_dir = data_dir / "db_langchain"
    json_dir.mkdir(parents=True)

    # Create fixtures with one valid page each
    pub1 = {
        "id": "pub_1",
        "title": "Publication 1",
        "release_date": "2025-01-01",
        "latest": True,
        "content": [
            {
                "page_number": 1,
                "page_url": "u#page=1",
                "page_text": "Valid content for pub 1",
            }
        ],
    }
    pub2 = {
        "id": "pub_2",
        "title": "Publication 2",
        "release_date": "2025-01-02",
        "latest": True,
        "content": [
            {
                "page_number": 1,
                "page_url": "u#page=1",
                "page_text": "Valid content for pub 2",
            }
        ],
    }
    pub3 = {
        "id": "pub_3",
        "title": "Publication 3",
        "release_date": "2025-01-03",
        "latest": True,
        "content": [
            {
                "page_number": 1,
                "page_url": "u#page=1",
                "page_text": "   ",
            }
        ],
    }

    (json_dir / "pub_1.json").write_text(json.dumps(pub1))
    (json_dir / "pub_2.json").write_text(json.dumps(pub2))
    (json_dir / "pub_3.json").write_text(json.dumps(pub3))

    # Mock embeddings to avoid model download
    class MockEmbeddings:
        def embed_documents(self, texts):
            return [[0.1] * 3 for _ in texts]

        def embed_query(self, text):
            return [0.1] * 3

    monkeypatch.setattr(
        preprocess, "HuggingFaceEmbeddings", lambda *a, **k: MockEmbeddings()
    )

    # Mock FAISS to create index files
    class MockFAISS:
        def __init__(self):
            self.docstore = type("obj", (object,), {"_dict": {}})

        def save_local(self, path):
            path = str(path)
            (tmp_path / "data" / "db_langchain").mkdir(parents=True, exist_ok=True)
            (tmp_path / "data" / "db_langchain" / "index.faiss").write_bytes(b"x")
            (tmp_path / "data" / "db_langchain" / "index.pkl").write_bytes(b"y")

    monkeypatch.setattr(preprocess.FAISS, "from_documents", lambda *a, **k: MockFAISS())

    # Run PrepareVectorStore in SETUP mode
    preprocess.PrepareVectorStore(
        data_dir=f"{data_dir}/",
        directory="json_conversions",
        split_directory="json_split",
        download_dir="pdf_downloads",
        split_length=1000,
        split_overlap=200,
        embedding_model_name="sentence-transformers/all-mpnet-base-v2",
        faiss_db_root="db_langchain",
        latest_only=False,
        mode="SETUP",
    )

    # Assert split JSONs created and latest flag preserved
    split_files = list(split_dir.glob("*.json"))
    assert len(split_files) == 2
    for sf in split_files:
        data = json.loads(sf.read_text())
        assert data["latest"] is True
        assert data["title"].startswith("Publication ")
        assert data["page_number"] == 1
        assert data["page_url"] == "u#page=1"
        assert "page_text" in data
        assert "content" not in data

    # Assert FAISS index files created
    assert (faiss_dir / "index.faiss").exists()
    assert (faiss_dir / "index.pkl").exists()


def test_embedding_pipeline_latest_only_filters_non_latest(tmp_path, monkeypatch):
    from statschat.embedding import preprocess

    data_dir = tmp_path / "data"
    json_dir = data_dir / "json_conversions"
    split_dir = data_dir / "json_split"
    json_dir.mkdir(parents=True)

    latest_pub = {
        "id": "pub_latest",
        "title": "Latest Publication",
        "release_date": "2025-01-01",
        "latest": True,
        "content": [
            {
                "page_number": 1,
                "page_url": "u#page=1",
                "page_text": "Latest content",
            }
        ],
    }
    old_pub = {
        "id": "pub_old",
        "title": "Old Publication",
        "release_date": "2024-12-31",
        "latest": False,
        "content": [
            {
                "page_number": 1,
                "page_url": "u#page=1",
                "page_text": "Old content",
            }
        ],
    }

    (json_dir / "pub_latest.json").write_text(json.dumps(latest_pub))
    (json_dir / "pub_old.json").write_text(json.dumps(old_pub))

    class MockEmbeddings:
        def embed_documents(self, texts):
            return [[0.1] * 3 for _ in texts]

        def embed_query(self, text):
            return [0.1] * 3

    monkeypatch.setattr(
        preprocess, "HuggingFaceEmbeddings", lambda *a, **k: MockEmbeddings()
    )

    class MockFAISS:
        def __init__(self):
            self.docstore = type("obj", (object,), {"_dict": {}})

        def save_local(self, path):
            return None

    monkeypatch.setattr(preprocess.FAISS, "from_documents", lambda *a, **k: MockFAISS())

    preprocess.PrepareVectorStore(
        data_dir=f"{data_dir}/",
        directory="json_conversions",
        split_directory="json_split",
        download_dir="pdf_downloads",
        split_length=1000,
        split_overlap=200,
        embedding_model_name="sentence-transformers/all-mpnet-base-v2",
        faiss_db_root="db_langchain",
        latest_only=True,
        mode="SETUP",
    )

    split_files = list(split_dir.glob("*.json"))
    assert len(split_files) == 1
    data = json.loads(split_files[0].read_text())
    assert data["title"] == "Latest Publication"
    assert data["latest"] is True
