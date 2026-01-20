# Cloud LLM Table Parsing Inconsistency

**Date identified:** 19 January 2026
**Status:** Open
**Priority:** Medium

## Issue Summary

The cloud LLM produces inconsistent answers when the retrieved context contains table data extracted from PDFs. The same question can return a correct answer on one run and "cannot answer" on the next.

## Example

**Question:** "What was inflation in Kenya in 2022?"

**Retrieved context:**
```
KENYA FACTS AND FIGURES 202525Figure 3: Inflation, 2020 - 2024YEARPER CENT20232024202220212020012345678 97.77.74.56.15.4
```

**Expected:** 7.7% (for 2022)

**Observed behaviour:**
- Run 1: Correctly extracted "7.7%"
- Run 2: "The year 2022 is not answered directly in the provided context"

## Root Cause

PDF table extraction concatenates values without clear delimiters. The string `7.77.74.56.15.4` represents the inflation values (7.7, 7.7, 4.5, 6.1, 5.4) for years 2023-2020, but without spacing or structure, the LLM struggles to parse it consistently.

## Potential Solutions

1. **Improve PDF text extraction** - Better handling of tables during the JSON conversion stage (`statschat/pdf_processing/`)
2. **Prompt engineering** - Add instructions to the cloud prompt about interpreting concatenated numerical data
3. **Post-processing** - Add heuristics to detect and reformat table-like data before sending to LLM

## Notes

- The local LLM (`local_llm.py`) successfully parsed this same data and returned "7.7%"
- This may be due to differences in the prompts or the model's training
- The `response_model.py` was updated to make `highlighting1/2/3` fields optional (default to empty list) to prevent crashes when LLM omits them
