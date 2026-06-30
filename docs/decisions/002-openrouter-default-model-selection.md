# ADR-002: OpenRouter Default Model Selection for Free Experimentation

**Status:** Accepted
**Date:** 2026-03-11

## Context

StatsChat-KE uses OpenRouter as the default cloud provider for testing the retrieval and generation pipeline. The previously configured model, `mistralai/Mistral-7B-Instruct-v0.3`, began failing in production-style runs with an OpenRouter `404` response stating that no endpoints were available.

Investigation showed that:
- the OpenRouter model page still existed,
- but the model was not currently routable through the API,
- which created a confusing failure mode for local testing and operator workflows.

At this stage of the project, the priority is to keep experimentation free where possible while preserving a clear path to higher-quality low-cost models later.

## Decision

Adopt `mistralai/mistral-small-3.1-24b-instruct:free` as the default OpenRouter model for current experimentation.

Also document `mistralai/mistral-nemo` as a preferred low-cost paid candidate for future evaluation once the project is ready to spend on model usage.

## Rationale

### Why the free Mistral Small 3.1 variant now?

- It is currently routable through the OpenRouter API.
- It keeps the project on a zero-cost path during experimentation.
- It remains within the Mistral family, reducing the conceptual jump from the prior default.
- It supports continued prompt, retrieval, and answer-shaping iteration without introducing immediate API spend.

### Why note Nemo for later?

- `mistralai/mistral-nemo` is currently available and low-cost on OpenRouter.
- It is likely a stronger long-term evaluation candidate once model spending is acceptable.
- It provides a clearer upgrade path than waiting for the older 7B model to become routable again.

## Consequences

### Positive

- The default cloud path works again for free experimentation.
- Operators receive a clearer error message if OpenRouter cannot route a model.
- Documentation now explains the difference between a visible model page and a live routable model.

### Trade-offs

- Free models may have more variability in availability, performance, or rate limits than paid ones.
- The chosen free model may behave differently from the older 7B default, so output quality should be re-observed during normal testing.

## Follow-up Notes

- Re-evaluate `mistralai/mistral-nemo` once the project is ready for modest paid usage.
- Consider documenting additional fallback models if OpenRouter availability changes again.
- Consider a future config option or model fallback list if model routing becomes a recurring operational issue.

## Local Override Note

The shared repository default remains the free OpenRouter model configured in `statschat/config/main.toml`.

Developers who want to use a paid model locally can set `STATSCHAT_GENERATIVE_MODEL` in their `.env` file without changing shared config. Removing that environment variable reverts local runs back to the repository default.
