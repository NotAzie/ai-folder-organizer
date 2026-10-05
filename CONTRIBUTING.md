# Contributing

Thank you for your interest in contributing to AI Folder Organizer! This document provides guidelines for contributing to the project.

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Setup](#development-setup)
- [How to Contribute](#how-to-contribute)
  - [Reporting Bugs](#reporting-bugs)
  - [Suggesting Features](#suggesting-features)
  - [Submitting Pull Requests](#submitting-pull-requests)
- [Development Guidelines](#development-guidelines)
- [Testing](#testing)
- [Code Style](#code-style)
- [Architecture](#architecture)

## Code of Conduct

This project follows a [Code of Conduct](CODE_OF_CONDUCT.md). Please review and adhere to it in all interactions.

## Getting Started

1. Fork the repository
2. Clone your fork locally
3. Create a feature branch from `main`
4. Make your changes
5. Test thoroughly
6. Submit a pull request

## Development Setup

### Prerequisites

- Python 3.8 or higher
- pip (Python package installer)
- Git

### Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/NotAzie/ai-folder-organizer.git
   cd ai-folder-organizer
   ```

2. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   pip install -r requirements-dev.txt  # For development
   ```

4. Install in development mode:
   ```bash
   pip install -e .
   ```

5. Configure API key (for testing AI features):
   ```bash
   export AI_FOLDER_ORG_API_KEY="your-test-key"
   ```

## How to Contribute

### Reporting Bugs

Before reporting a bug, please:

1. Check if the bug has already been reported in the [Issues](https://github.com/NotAzie/ai-folder-organizer/issues)
2. Gather relevant information:
   - Python version
   - Operating system
   - Steps to reproduce
   - Expected vs actual behavior
   - Error messages or logs

When submitting a bug report, include as much detail as possible.

### Suggesting Features

Feature suggestions are welcome! When proposing a feature:

1. Check if a similar feature has already been requested
2. Describe the use case and expected behavior
3. Consider whether the feature aligns with the project's scope

### Submitting Pull Requests

1. **Create an issue** first for significant changes to discuss the approach
2. **Branch from `main`**: `git checkout -b feature/your-feature-name`
3. **Make your changes** following the code style guidelines
4. **Write or update tests** to cover your changes
5. **Test your changes** locally
6. **Update documentation** if needed
7. **Submit a pull request** with a clear description

#### Pull Request Checklist

- [ ] Code follows project style guidelines
- [ ] Tests pass (`pytest`)
- [ ] New tests added for new functionality
- [ ] Documentation updated if applicable
- [ ] No API keys or secrets committed
- [ ] Commit messages are clear and descriptive

## Development Guidelines

### Project Structure

```
organiser/
├── config.py          # Configuration management
├── scanner.py         # Folder scanning logic
├── llm_client.py      # LLM API client
├── proposal.py        # Proposal parsing
├── executor.py        # Action execution
└── ui/
    ├── cli.py         # Command-line interface
    └── gui.py         # Graphical interface
```

### Adding a New Feature

1. Identify the appropriate module for your feature
2. Implement the feature with proper error handling
3. Add type hints to function signatures
4. Write docstrings for public functions/classes
5. Add tests for the new functionality
6. Update relevant documentation

### LLM Client Architecture

The LLM client is designed to be extensible. To add support for a new provider:

1. Create a new client class in `llm_client.py` that inherits from `LLMClient`
2. Implement the `generate_response` method
3. Add the client to the `create_client` factory function
4. Add configuration options as needed

### UI Development

The UI is separated into CLI and GUI modules:

- **CLI** (`ui/cli.py`): Terminal-based interface
- **GUI** (`ui/gui.py`): Tkinter-based graphical interface

Both interfaces use the same underlying business logic from the parent modules.

## Testing

Run the test suite:

```bash
pytest
```

Run with coverage:

```bash
pytest --cov=organiser
```

Run specific test file:

```bash
pytest tests/test_scanner.py -v
```

All new features should include tests. Bug fixes should include tests that demonstrate the fix.

## Code Style

This project uses [ruff](https://github.com/astral-sh/ruff) for linting and [black](https://github.com/psf/black) for formatting.

### Formatting

Format code:

```bash
ruff format .
black .
```

Lint code:

```bash
ruff check .
```

### Python Conventions

- Use type hints for function signatures
- Follow PEP 8 style guidelines
- Use docstrings for public functions and classes
- Keep functions focused and reasonably sized
- Use clear, descriptive variable names

### Import Order

1. Standard library imports
2. Third-party imports
3. Local imports

## Architecture

### Key Components

1. **Config** (`config.py`): Manages application configuration from multiple sources
2. **Scanner** (`scanner.py`): Scans folders and builds inventory
3. **LLM Client** (`llm_client.py`): Interfaces with LLM APIs
4. **Proposal** (`proposal.py`): Parses and manages organization proposals
5. **Executor** (`executor.py`): Executes file operations with safety features
6. **UI** (`ui/`): User interfaces (CLI and GUI)

### Data Flow

1. User selects folder
2. Scanner scans folder and builds structure
3. Summary is sent to LLM client
4. LLM returns organization proposal
5. Proposal is parsed and displayed to user
6. User reviews and approves actions
7. Executor runs approved actions (with dry-run option)
8. Logs and rollback manifest are saved

## Questions?

If you have questions about contributing, open an issue with your question. We're happy to help!
