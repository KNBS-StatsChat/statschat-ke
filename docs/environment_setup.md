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

## Security Notes

- **Never commit** your `.env` file to version control
- **Never share** your API keys publicly
- **Rotate keys** regularly for security
- **Use environment-specific** `.env` files for development and production
