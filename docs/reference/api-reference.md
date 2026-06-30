# API Reference

StatsChat-KE exposes a FastAPI HTTP backend. There are two variants:

| Variant | Script | Generator |
|---|---|---|
| Cloud | `fast-api/main_api_cloud.py` | Remote LLM via OpenRouter / OpenAI |
| Local | `fast-api/main_api_local.py` | Mistral-7B loaded locally via Hugging Face |

Both variants expose the same endpoints. The only behavioural difference is the generation step — retrieval, reranking, and response structure are identical.

**Interactive docs** (Swagger UI) are available at `http://127.0.0.1:8000/docs` when the API is running locally.

---

## Authentication

Authentication is optional and controlled by the `STATSCHAT_API_KEY` environment variable.

- **If `STATSCHAT_API_KEY` is not set**: all endpoints are open (suitable for local development).
- **If `STATSCHAT_API_KEY` is set**: `/search` and `/feedback` require a key. `/health` remains public.

Provide the key in either of these request headers:

```
X-API-Key: your_api_key
```
```
Authorization: Bearer your_api_key
```

---

## Endpoints

### `GET /`

Redirects to `/openapi.json` (the machine-readable OpenAPI schema).

---

### `GET /health`

Returns liveness and non-secret runtime status. Always public — no authentication required.

**Response** `200 OK`

```json
{
  "status": "ok",
  "api_mode": "cloud",
  "model_name": "openai/gpt-5.4-mini",
  "provider": "openrouter",
  "model_loaded": true
}
```

| Field | Description |
|---|---|
| `status` | `"ok"` when the API is running |
| `api_mode` | `"cloud"` or `"local"` |
| `model_name` | Active generative model identifier |
| `provider` | LLM provider (`"openrouter"`, `"openai"`, or `"local"`) |
| `model_loaded` | `true` once the model is ready to serve requests (local API only has a startup delay) |

---

### `GET /search`

Search KNBS publications and return a grounded answer.

**Authentication**: required if `STATSCHAT_API_KEY` is set.

**Query parameters**

| Parameter | Type | Default | Description |
|---|---|---|---|
| `q` | string | required | The question to answer |
| `content_type` | string | `"latest"` | `"latest"` to restrict to recent bulletins; `"all"` to search the full corpus |
| `debug` | bool | `true` | If `true`, includes the full LLM response in the output |

**Example request**

```
GET /search?q=what+was+inflation+in+december+2023&content_type=all
```

```bash
curl "http://127.0.0.1:8000/search?q=what+was+inflation+in+december+2023&content_type=all"
```

With authentication:

```bash
curl -H "X-API-Key: your_key" \
     "http://127.0.0.1:8000/search?q=what+was+inflation+in+december+2023"
```

**Response** `200 OK`

```json
{
  "question": "what was inflation in december 2023",
  "content_type": "latest",
  "answer": "Inflation in Kenya in December 2023 was 6.6%, according to the Consumer Price Index report.",
  "references": [...],
  "response_time_seconds": 3.42,
  "debug_response": {...}
}
```

| Field | Description |
|---|---|
| `question` | The sanitised input question |
| `content_type` | The effective content type used (`"latest"` or `"all"`) |
| `answer` | Generated answer text. **Empty string** if no answer meets the `answer_threshold` or the question was refused by the guardrail |
| `references` | List of retrieved source documents (cloud) or a single URL string (local) |
| `response_time_seconds` | Wall-clock time for the full search and generation |
| `debug_response` | Full LLM response object; only present when `debug=true` |

**Notes**

- If `content_type=latest` is requested but the question contains an explicit date, year, or quarter, the API automatically widens the search to the full corpus so historical reports are not silently excluded.
- Questions that fall outside the scope of the corpus (e.g. general knowledge questions, requests for personal advice) are refused by the guardrail policy. A refusal returns `200` with `answer: ""` — it is not an error.
- If no documents score above `answer_threshold`, `answer` is returned as an empty string and `references` still contains the top retrieved documents.

**Error responses**

| Status | Condition |
|---|---|
| `401` | Missing or invalid API key (when auth is enabled) |
| `422` | Empty or missing `q` parameter |
| `429` | Rate limit exceeded (when `STATSCHAT_RATE_LIMIT_PER_MINUTE` is set) |
| `503` | Local API model not yet loaded (local variant only) |

---

### `POST /feedback`

Record user feedback on a previous answer.

**Authentication**: required if `STATSCHAT_API_KEY` is set.

**Request body** (JSON)

| Field | Type | Required | Description |
|---|---|---|---|
| `rating` | string or int | yes | `"1"` / `1` for positive, `"0"` / `0` for negative |
| `rating_comment` | string | no | Free-text comment |
| `question` | string | no | The question that was asked |
| `content_type` | string | no | The content type used |
| `answer` | string | no | The answer that was rated |

**Example request**

```bash
curl -X POST "http://127.0.0.1:8000/feedback" \
     -H "Content-Type: application/json" \
     -d '{"rating": "1", "question": "what was inflation in december 2023", "rating_comment": "Correct and well sourced"}'
```

**Response** `202 Accepted` — empty body.

---

## Cloud vs Local Differences

| Aspect | Cloud API | Local API |
|---|---|---|
| Generator | Configured cloud LLM (default: `openai/gpt-5.4-mini`) | Mistral-7B loaded via Hugging Face (`~16 GB RAM`) |
| Startup time | Fast | Slow — model downloads and loads on first start |
| `references` field | List of reference objects with metadata | Single URL string (legacy shape) |
| Guardrail | Applied | Applied |
| Retrieval | Shared architecture (identical) | Shared architecture (identical) |
| `response_time_seconds` | Seconds (network-dependent) | Minutes for first query; faster once warm |

---

## Rate Limiting

Set `STATSCHAT_RATE_LIMIT_PER_MINUTE` to an integer to enable per-client in-process rate limiting. Requests exceeding the limit return `429 Too Many Requests`.

---

## CORS

Allowed browser origins default to `localhost:3000`, `localhost:5000`, and their `127.0.0.1` equivalents for local development.

For deployed instances, set `STATSCHAT_CORS_ORIGINS` to a comma-separated list of allowed origins:

```shell
export STATSCHAT_CORS_ORIGINS=https://your-frontend.example,https://other-origin.example
```

---

## Related Documentation

- [guides/OPERATING_MANUAL.md](../guides/OPERATING_MANUAL.md) — starting the API, running queries from the command line
- [guides/server_deployment.md](../guides/server_deployment.md) — Docker and production deployment
- [guides/flask_demo_frontend.md](../guides/flask_demo_frontend.md) — browser demo frontend
- [reference/config_guide.md](./config_guide.md) — all `main.toml` configuration options
