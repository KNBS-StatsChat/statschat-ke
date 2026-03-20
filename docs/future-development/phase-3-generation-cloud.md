# Phase 3: Generation (Cloud)

This file tracks future ideas for improving cloud-based generation in the StatsChat-KE pipeline.

## Scope

- Prompt design
- Model choice
- Output validation
- Cost and latency management
- Provider reliability and fallback behaviour
- User-facing answer quality

## Candidate Improvements

- Review prompt structure for cleaner grounded answers and better highlighting behaviour.

## Questions to Explore

- Which model gives the best balance of cost, factuality, and formatting consistency for KNBS-style questions?
- Should the project support explicit model fallback choices in config?


## Notes

Current free experimentation default: `mistralai/mistral-small-3.1-24b-instruct:free`

Current low-cost paid model to evaluate later: `mistralai/mistral-nemo`

Use this file to record future model trials, prompt experiments, and provider decisions.
