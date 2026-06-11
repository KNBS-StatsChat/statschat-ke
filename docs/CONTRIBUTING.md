# Contributing to KNBS StatsChat

Thank you for your interest in contributing to KNBS StatsChat! This document provides guidelines and setup instructions for developers.

## Table of Contents
- [Prerequisites](#prerequisites)
- [Development Setup](#development-setup)
- [Installation Troubleshooting](#installation-troubleshooting)
- [Running the Application](#running-the-application)
- [Code Quality](#code-quality)
- [Making Changes](#making-changes)

## Prerequisites

- **Python 3.11** (recommended) or Python 3.10+
- **pip 25.2** or later
- **Git**
- **pyenv** (recommended for Mac users) - see [pyenv Installation Guide](./guides/setup_guide.md)

## Development Setup

### 1. Fork and Clone

```bash
# Fork the repository on GitHub, then clone your fork
git clone https://github.com/YOUR_USERNAME/statschat-ke.git
cd statschat-ke
```

### 2. Create a Virtual Environment

```bash
# Using venv (built-in)
python3.11 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# OR using conda
conda create --name statschat_dev python=3.11
conda activate statschat_dev
```

### 3. Install Development Dependencies

```bash
# Upgrade pip first
pip install --upgrade pip

# Install the package in editable mode with all dev dependencies
pip install -e ".[dev]"
```

This installs:
- All core dependencies
- Testing tools (`pytest`)
- Backend tools (`fastapi`, `uvicorn`)
- Frontend tools (`Flask`, `gunicorn`)
- Development tools (`ipykernel`, `pre-commit`)

### 4. Configure Environment Variables

Before running the application, you must set up your API credentials:

**See the [Environment Setup Guide](./guides/environment_setup.md) for detailed instructions** on:
- Creating the `.env` file
- Getting API keys (OpenRouter, OpenAI, or HuggingFace)
- Configuring your chosen LLM provider

### 5. Set Up Pre-commit Hooks

```bash
# Pre-commit hooks help maintain code quality
pre-commit install
```

This will automatically run security checks (password/API key detection) before each commit.

## Installation Troubleshooting

### SSL Certificate Errors

If you encounter SSL certificate errors during installation:

```bash
# Create pip config directory
mkdir -p ~/.config/pip  # On Mac/Linux
# mkdir %APPDATA%\pip  # On Windows

# Configure pip to trust PyPI domains (Mac/Linux)
cat > ~/.config/pip/pip.conf << 'EOF'
[global]
trusted-host = pypi.org
               pypi.python.org
               files.pythonhosted.org
EOF
```


### setuptools Build Errors

If you see errors related to `setuptools` or `distutils`:

```bash
pip install "setuptools>=62,<75"
```

This issue is already fixed in `pyproject.toml`, but you may need to manually install if using an older version.

### Python Version Management

For Mac users using pyenv, see the [Setup Guide](./guides/setup_guide.md) which covers:
- Installing Python with proper SSL support
- Switching between Python versions
- Virtual environment management

### Additional Resources

- [Setup Guide](./guides/setup_guide.md) - Detailed installation for Mac and Windows
- [Environment Setup Guide](./guides/environment_setup.md) - Configure API credentials and `.env` file

## Running the Application

### 1. Set Up the Vector Store (First Time Only)

Before running the application, ensure you have:
- Created and activated your virtual environment
- Installed all dependencies
- **[Set up your `.env` file with API credentials](./guides/environment_setup.md)**

Then create the vector store:

```bash
python statschat/pdf_runner.py
```

Make sure `mode` in `statschat/config/main.toml` (under `[preprocess]`) is set to `"SETUP"` for initial setup.

### 2. Run Tests

```bash
# Run all tests
pytest

# Run specific test file
pytest tests/test_filename.py

# Run with verbose output
pytest -v
```

### 3. Run the Backend API

```bash
# For local development
uvicorn fast-api.main_api_local:app --reload
```

The API will be available at `http://127.0.0.1:8000`.

### 4. Run Sample Questions

```bash
# Using cloud LLM (uses the provider/model configured in main.toml)
python statschat/generative/cloud_llm.py
```

## Code Quality

### Pre-commit Hooks

Pre-commit hooks run automatically before each commit and enforce:
- **Security**: detect passwords, API keys, and secrets
- **File hygiene**: file size limits, trailing whitespace, end-of-file newlines
- **Python formatting**: `isort` (import ordering), `black` (code style)
- **Python linting**: `flake8`
- **Notebook outputs**: `nbstripout` strips cell outputs before committing

```bash
# Run manually on all files
pre-commit run --all-files
```

### Code Style

- Follow PEP 8 guidelines
- Use meaningful variable and function names
- Add docstrings to functions and classes
- Keep functions focused and concise

## Making Changes

### Branch Naming

```bash
git checkout -b feature/your-feature-name   # new functionality
git checkout -b fix/bug-description         # bug fixes
git checkout -b docs/what-you-are-updating  # documentation only
```

### Commit Messages

Use a short prefix that describes the type of change:

```
feat: add reranker model configuration option
fix: handle missing url_dict.json gracefully in UPDATE mode
docs: update OPERATING_MANUAL with API startup instructions
test: add unit tests for query_policy guardrail
refactor: extract PDF download retry logic into helper
```

### Definition of Done

Before opening a PR, confirm:

- [ ] `pre-commit run --all-files` passes with no failures
- [ ] `pytest` passes (relevant tests for the change)
- [ ] If changing retrieval, model config, or the FAISS index: run the accuracy evaluator and compare against the baseline — see [tests/accuracy/README.md](../tests/accuracy/README.md)
- [ ] Documentation updated if behaviour has changed
- [ ] No secrets, credentials, or large data files committed

### Pull Request Process

1. Push your branch and open a PR against `main` (or the relevant feature branch)
2. Describe *what* the change does and *why* — link any related issue
3. If accuracy metrics are affected, include before/after benchmark numbers
4. A reviewer should approve before merging; the author should not self-merge
5. Squash or rebase to keep history clean — avoid merge commits within a feature branch

## Project Structure

See [docs/reference/repo_structure.md](./reference/repo_structure.md) for a full annotated directory tree.

```
statschat-ke/
├── statschat/          # Core Python package
│   ├── config/         # main.toml and configuration helpers
│   ├── embedding/      # FAISS index building and latest-flag helpers
│   ├── generative/     # Cloud and local LLM integration, prompts, guardrails
│   ├── model_evaluation/  # Answer scoring helpers
│   └── pdf_processing/ # PDF scraping, conversion, auditing
├── fast-api/           # FastAPI backend entrypoints (cloud and local)
├── flask-app/          # Lightweight browser demo frontend
├── docs/               # Documentation
├── tests/              # Unit, integration, e2e, and accuracy tests
├── data/               # Local build artifacts — not in git
│   ├── pdf_downloads/       # Downloaded PDFs and url_dict.json
│   └── db_langchain_rebuild_v1/  # FAISS vector index (April 2026 rebuild)
└── pyproject.toml      # Package metadata and dependencies
```

## Getting Help

- **Documentation:** Check the [docs/README.md](./README.md) for a full index
- **Issues:** Search or create [GitHub Issues](https://github.com/KNBS-StatsChat/statschat-ke/issues)
- **Setup Problems:** See [Setup Guide](./guides/setup_guide.md)

## License

By contributing, you agree that your contributions will be licensed under the MIT License.

---

Thank you for contributing to KNBS StatsChat! 🎉
