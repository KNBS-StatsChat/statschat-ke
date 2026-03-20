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

- Compare the free OpenRouter default with low-cost paid models such as `mistralai/mistral-nemo`.
- Track answer quality differences across model options for fact extraction, citation behaviour, and numerical precision.
- Add a structured comparison process for free, low-cost, and premium model tiers.
- Improve handling of provider failures, unavailable models, and transient API issues.
- Review prompt structure for cleaner grounded answers and better highlighting behaviour.

## Questions to Explore

- Which model gives the best balance of cost, factuality, and formatting consistency for KNBS-style questions?
- Should the project support explicit model fallback choices in config?
- Would a small evaluation harness for cloud models help guide provider decisions?

## Notes

Current free experimentation default: `mistralai/mistral-small-3.1-24b-instruct:free`

Current low-cost paid model to evaluate later: `mistralai/mistral-nemo`

Use this file to record future model trials, prompt experiments, and provider decisions.
