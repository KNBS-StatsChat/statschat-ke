"""
Tests for PrepareVectorStore._merge_faiss_db with FAISS mocked.
"""

import os
from unittest.mock import MagicMock


def test_merge_faiss_db_merges_and_cleans(tmp_path, monkeypatch):
    """Merges latest FAISS DB into original and cleans the latest directory."""
    from statschat.embedding import preprocess

    latest_dir = tmp_path / "db_langchain_latest"
    latest_dir.mkdir(parents=True, exist_ok=True)
    (latest_dir / "dummy").write_text("x")

    original_dir = tmp_path / "db_langchain"
    original_dir.mkdir()

    mock_loaded = MagicMock()
    monkeypatch.setattr(preprocess.FAISS, "load_local", lambda *a, **k: mock_loaded)

    instance = type("Dummy", (), {})()
    instance.db = MagicMock()
    instance.embeddings = MagicMock()
    instance.faiss_db_root = str(latest_dir)
    instance.original_faiss_db_root = str(original_dir)
    instance.logger = MagicMock()

    preprocess.PrepareVectorStore._merge_faiss_db(instance)

    mock_loaded.merge_from.assert_called_once_with(instance.db)
    mock_loaded.save_local.assert_called_once_with(str(original_dir))
    # Latest dir should be emptied
    assert list(os.scandir(latest_dir)) == []
