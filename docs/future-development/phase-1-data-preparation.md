# Phase 1: Data Preparation

This file tracks future ideas for improving the data preparation stage of the StatsChat-KE pipeline.

## Scope

- PDF discovery and download
- File auditing and recovery
- PDF-to-JSON conversion
- Metadata quality
- Batch processing reliability

## Candidate Improvements

- Improve download retry and backoff behaviour for intermittent KNBS availability issues.
- Track provenance more explicitly for each downloaded file and conversion output.
- Add stronger validation for extracted metadata such as publication dates, titles, and source URLs.
- Expand automated checks for corrupted, zero-byte, or partially downloaded PDFs.
- Improve extraction quality benchmarking for tables and statistical layouts.

## Questions to Explore

- Which KNBS document types still produce poor text extraction results?
- Should there be a standard reprocessing workflow for problematic PDFs?
- Would separate handling for bulletins, abstracts, and surveys improve downstream retrieval quality?

## Notes

Use this file to record concrete proposals, links to investigations, and implementation ideas as they arise.
