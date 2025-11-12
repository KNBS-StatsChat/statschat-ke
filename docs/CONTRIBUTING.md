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
- **pyenv** (recommended for Mac users) - see [pyenv Installation Guide](./docs/pyenv_python_installation_guide.md)

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

**See the [Environment Setup Guide](./environment_setup.md) for detailed instructions** on:
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

For more details, see [SSL Fix Report](./docs/ssl_fix_report.md).

### setuptools Build Errors

If you see errors related to `setuptools` or `distutils`:

```bash
pip install "setuptools>=62,<75"
```

This issue is already fixed in `pyproject.toml`, but you may need to manually install if using an older version.

### Python Version Management

For Mac users using pyenv, see the comprehensive [pyenv Installation Guide](./docs/pyenv_python_installation_guide.md) which covers:
- Installing Python with proper SSL support
- Switching between Python versions
- Virtual environment management

### Additional Resources

- [Setup Guide](./setup_guide.md) - Detailed installation for Mac and Windows
- [Environment Setup Guide](./environment_setup.md) - Configure API credentials and `.env` file
- [SSL Fix Report](./ssl_fix_report.md) - Complete SSL troubleshooting documentation

## Running the Application

### 1. Set Up the Vector Store (First Time Only)

Before running the application, ensure you have:
- Created and activated your virtual environment
- Installed all dependencies
- **[Set up your `.env` file with API credentials](./environment_setup.md)**

Then create the vector store:

```bash
python statschat/pdf_runner.py
```

Make sure `PDF_FILES_MODE` in `statschat/config/main.toml` is set to `"SETUP"` for initial setup.

### 2. Run Tests

```bash
# Run all tests
pytest

# Run specific test file
pytest tests/test_filename.py

# Run with coverage
pytest --cov=statschat
```

### 3. Run the Backend API

```bash
# For local development
uvicorn fast-api.main_api_local:app --reload
```

The API will be available at `http://127.0.0.1:8000`.

### 4. Run Sample Questions

```bash
# Using local LLM
python statschat/generative/local_llm.py

# Using cloud LLM (requires HuggingFace API token)
python statschat/generative/cloud_llm.py
```

## Code Quality

### Pre-commit Hooks

Pre-commit hooks automatically run before each commit:
- Security checks (detect passwords, API keys)
- File size checks
- YAML/JSON validation

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

### 1. Create a Feature Branch

```bash
git checkout -b feature/your-feature-name
# OR
git checkout -b fix/bug-description
```

### 2. Make Your Changes

- Write clear, concise commit messages
- Keep commits focused on a single change
- Add tests for new features
- Update documentation as needed

### 3. Test Your Changes

```bash
# Run tests
pytest

# Run pre-commit checks
pre-commit run --all-files

# Test the application manually
python statschat/generative/local_llm.py
```

### 4. Push and Create a Pull Request

```bash
git push origin feature/your-feature-name
```

Then create a Pull Request on GitHub.

## Project Structure

```
statschat-ke/
├── statschat/              # Main package
│   ├── config/            # Configuration files (TOML)
│   ├── embedding/         # Document embedding and preprocessing
│   ├── generative/        # LLM integration (local and cloud)
│   ├── model_evaluation/  # Model evaluation tools
│   └── pdf_processing/    # PDF scraping and processing
├── fast-api/              # FastAPI backend
├── docs/                  # Documentation
├── data/                  # Data storage (gitignored)
│   ├── pdf_downloads/    # Downloaded PDF files
│   └── db_langchain/     # Vector store databases
├── tests/                 # Test files
└── pyproject.toml        # Project dependencies and configuration
```

## Getting Help

- **Documentation:** Check the [docs/](./docs/) folder
- **Issues:** Search or create [GitHub Issues](https://github.com/KNBS-StatsChat/statschat-ke/issues)
- **Setup Problems:** See [Setup Guide](./docs/setup_guide.md)

## License

By contributing, you agree that your contributions will be licensed under the MIT License.

---

Thank you for contributing to KNBS StatsChat! 🎉
