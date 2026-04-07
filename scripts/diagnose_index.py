"""
Diagnose FAISS index coverage without loading the embedding model.
Loads index.pkl directly to inspect chunk metadata, then cross-references
against the QA test set to find missing/sparse documents.
"""

import pickle
import json
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
INDEX_PKL = ROOT / "data/db_langchain_rebuild_v1/index.pkl"
URL_DICT = ROOT / "data/pdf_downloads/url_dict.json"
JSON_DIR = ROOT / "data/json_conversions"
QA_FILE = ROOT / "tests/accuracy/KNBS_Verified_QA_Examples_CorpusAligned.xlsx"


def load_docstore():
    print(f"Loading docstore from {INDEX_PKL} ...")
    with open(INDEX_PKL, "rb") as f:
        docstore, index_to_docstore_id = pickle.load(f)
    return docstore, index_to_docstore_id


def analyse_index(docstore, index_to_docstore_id):
    chunks_by_source = defaultdict(list)
    missing_source = 0

    for doc_id, doc in docstore._dict.items():
        source = doc.metadata.get("source", "").strip()
        if not source:
            missing_source += 1
            continue
        chunks_by_source[source].append(
            {
                "title": doc.metadata.get("title", ""),
                "date": doc.metadata.get("date", ""),
                "page_number": doc.metadata.get("page_number", ""),
                "latest": doc.metadata.get("latest", ""),
            }
        )

    print("\n=== INDEX OVERVIEW ===")
    print(f"Total chunks        : {len(docstore._dict)}")
    print(f"Total index vectors : {len(index_to_docstore_id)}")
    print(f"Unique sources      : {len(chunks_by_source)}")
    print(f"Chunks with no source metadata: {missing_source}")

    # Sparse documents (< 3 chunks — likely extraction failures)
    sparse = {s: c for s, c in chunks_by_source.items() if len(c) < 3}
    print(f"\nDocuments with < 3 chunks (likely extraction failures): {len(sparse)}")
    for source, chunks in sorted(sparse.items(), key=lambda x: len(x[1])):
        print(f"  [{len(chunks):2d} chunk(s)]  {source}")

    return chunks_by_source


def cross_reference_qa(docstore):
    """Cross-reference QA expected docs against the index using PDF filename from URL."""
    try:
        import pandas as pd
    except ImportError:
        print("\nPandas not available — skipping QA cross-reference.")
        return

    if not QA_FILE.exists():
        print(f"\nQA file not found: {QA_FILE}")
        return

    # Build a lookup: pdf_filename (lowercase, no .pdf) → list of source IDs in index
    filename_to_sources = defaultdict(set)
    source_chunk_count = defaultdict(int)
    for doc_id, doc in docstore._dict.items():
        url = doc.metadata.get("url", "")
        source = doc.metadata.get("source", "")
        source_chunk_count[source] += 1
        if url:
            fname = url.rstrip("/").split("/")[-1].lower()
            fname = fname.replace(".pdf.pdf", ".pdf")  # fix double extension
            filename_to_sources[fname].add(source)

    print("\n=== QA CROSS-REFERENCE ===")
    df = pd.read_excel(QA_FILE)
    print(f"QA questions loaded: {len(df)}")
    print(f"Columns: {df.columns.tolist()}")

    if "relevant_doc_ids" not in df.columns:
        print("Column 'relevant_doc_ids' not found in QA file.")
        return

    missing_docs = []
    sparse_docs = []
    found_docs = []

    for _, row in df.iterrows():
        qid = row.get("query_id", "?")
        query = str(row.get("query_text", ""))
        doc_ids_raw = str(row.get("relevant_doc_ids", ""))
        doc_ids = [d.strip() for d in doc_ids_raw.split(",") if d.strip()]

        for doc_id in doc_ids:
            lookup = doc_id.lower()
            if not lookup.endswith(".pdf"):
                lookup += ".pdf"

            sources = filename_to_sources.get(lookup, set())
            if not sources:
                missing_docs.append((qid, query[:70], doc_id))
            else:
                total_chunks = sum(source_chunk_count[s] for s in sources)
                if total_chunks < 3:
                    sparse_docs.append((qid, query[:70], doc_id, total_chunks))
                else:
                    found_docs.append((qid, doc_id, total_chunks))

    print(f"\nDocs fully present     : {len(found_docs)}")
    print(f"Docs sparse (<3 chunks): {len(sparse_docs)}")
    print(f"Docs MISSING from index: {len(missing_docs)}")

    if missing_docs:
        print("\n--- MISSING DOCUMENTS ---")
        for qid, query, doc_id in missing_docs:
            print(f"  Q{qid}: '{query}'")
            print(f"         → missing: {doc_id}")

    if sparse_docs:
        print("\n--- SPARSE DOCUMENTS (likely partial extraction) ---")
        for qid, query, doc_id, n in sparse_docs:
            print(f"  Q{qid}: '{query}'")
            print(f"         → {doc_id}  [{n} chunk(s)]")

    if found_docs:
        print("\n--- FOUND DOCUMENTS ---")
        for qid, doc_id, n in found_docs:
            print(f"  Q{qid}: {doc_id}  [{n} chunks]")


def compare_json_vs_index(docstore):
    """Compare JSON files (by URL-derived filename) vs what's actually in the index."""
    if not JSON_DIR.exists():
        print(f"\nJSON dir not found: {JSON_DIR}")
        return

    # Build set of PDF filenames referenced in the index (from URL metadata)
    indexed_filenames = set()
    for doc_id, doc in docstore._dict.items():
        url = doc.metadata.get("url", "")
        if url:
            fname = url.rstrip("/").split("/")[-1].lower()
            fname = fname.replace(".pdf.pdf", ".pdf")
            indexed_filenames.add(fname)

    # Build set of PDF filenames from the url_dict (all downloaded PDFs)
    if URL_DICT.exists():
        with open(URL_DICT) as f:
            url_dict = json.load(f)
        downloaded_filenames = {k.lower() for k in url_dict.keys()}
    else:
        downloaded_filenames = set()

    not_indexed = downloaded_filenames - indexed_filenames
    orphaned = indexed_filenames - downloaded_filenames

    print("\n=== PDF DOWNLOAD vs INDEX COVERAGE ===")
    print(f"PDFs downloaded : {len(downloaded_filenames)}")
    print(f"PDFs in index   : {len(indexed_filenames)}")
    print(f"Downloaded but NOT in index: {len(not_indexed)}")
    for f in sorted(not_indexed)[:30]:
        print(f"  {f}")
    if len(not_indexed) > 30:
        print(f"  ... and {len(not_indexed) - 30} more")
    print(f"In index but NOT in download list (orphaned): {len(orphaned)}")


if __name__ == "__main__":
    if not INDEX_PKL.exists():
        print(f"ERROR: Index not found at {INDEX_PKL}")
        sys.exit(1)

    docstore, index_to_docstore_id = load_docstore()
    chunks_by_source = analyse_index(docstore, index_to_docstore_id)
    compare_json_vs_index(docstore)
    cross_reference_qa(docstore)
