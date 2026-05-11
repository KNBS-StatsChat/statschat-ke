# Environment Setup Guide

## Creating the `.env` File

The application requires API credentials to access language models. These credentials are stored in a `.env` file in the project root directory.

### Steps

1. **Create the `.env` file** in the project root:
   ```bash
   touch .env
   ```

2. **Add the required environment variables** based on your chosen provider:

   #### For OpenRouter (Default)
   ```
   OPENROUTER_API_KEY=your_openrouter_api_key_here
   OPENROUTER_BASE_URL=https://openrouter.ai/api/v1
   ```

   #### Optional: Override the default model locally
   ```
   STATSCHAT_GENERATIVE_MODEL=mistralai/mistral-nemo
   ```

   If you want to use the repository default model instead, leave `STATSCHAT_GENERATIVE_MODEL` unset (or remove it from `.env`).

   #### For OpenAI
   ```
   OPENAI_API_KEY=your_openai_api_key_here
   ```

   #### For HuggingFace Inference
   ```
   HF_TOKEN=your_huggingface_token_here
   ```

3. **Replace the placeholder values** with your actual API keys

4. **Verify the file is in `.gitignore`** to prevent committing secrets

## Getting an OpenRouter API Key

OpenRouter provides access to multiple language models through a single API.

1. **Visit** [https://openrouter.ai/](https://openrouter.ai/)

2. **Sign up** or **log in** to your account

3. **Navigate to the Keys section** in your dashboard

4. **Create a new API key**

5. **Copy the key** and paste it into your `.env` file as the value for `OPENROUTER_API_KEY`

6. You might need to **Add credits** to your OpenRouter account to use the API

## Configuring the Provider

The provider is configured in `statschat/config/main.toml`:

```toml
[search]
provider = "openrouter"  # Options: "openrouter", "openai", "huggingface_inference"
```

Change the `provider` value to match your chosen LLM provider and ensure the corresponding API key is set in your `.env` file.

When using OpenRouter, choose a model that is currently routable through the API. A model page can still exist on the OpenRouter site even when no live API endpoints are available for it. Also note that model availability is not the same as model reliability for structured-output tasks. The historical April 2026 benchmark used `mistralai/mistral-small-3.1-24b-instruct`, but replication probes in May 2026 showed that the same OpenRouter route had become unstable for StatsChat's structured JSON responses. For current Mistral-family comparisons, prefer `mistralai/mistral-small-24b-instruct-2501` or `mistralai/mistral-small-3.2-24b-instruct`. When you move to paid usage, `mistralai/mistral-nemo` is also a reasonable low-cost option to evaluate.

If you want to keep the repository default on the free model but use a paid model locally, set `STATSCHAT_GENERATIVE_MODEL` in your `.env` file. This overrides the model from `statschat/config/main.toml` without changing shared project config. If `STATSCHAT_GENERATIVE_MODEL` is not set, StatsChat uses the repository default from `statschat/config/main.toml`.

## Security Notes

- **Never commit** your `.env` file to version control
- **Never share** your API keys publicly
- **Rotate keys** regularly for security
- **Use environment-specific** `.env` files for development and production
