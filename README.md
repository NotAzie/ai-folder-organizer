# AI Folder Organizer

[![Python Version](https://img.shields.io/pypi/pyversions/ai-folder-organizer.svg)](https://pypi.org/project/ai-folder-organizer/)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](https://opensource.org/licenses/MIT)
[![Code style: ruff](https://img.shields.io/badge/code%20style-ruff-000000.svg)](https://github.com/astral-sh/ruff)

AI-powered folder organization tool with interactive GUI and CLI. Scans directories, uses LLM to suggest reorganization plans, and safely executes file moves with rollback support.

## Features

- 🔍 **Smart Scanning** - Comprehensive folder inventory with project detection
- 🤖 **AI-Powered Suggestions** - Leverages LLM to propose intelligent reorganization plans
- 🖥️ **Dual Interface** - Choose between CLI or full-featured GUI
- ✅ **Interactive Approval** - Review and approve changes before execution
- 🔄 **Dry-Run Mode** - Preview changes without modifying files
- ↩️ **Rollback Support** - Undo operations with manifest-based rollback
- 🎤 **Speech Input** (optional) - Voice commands for folder naming
- 😊 **Emoji Assistance** - Automatic emoji suggestions for folder names

## Quick Start

### Installation

```bash
# Clone the repository
git clone https://github.com/NotAzie/ai-folder-organizer.git
cd ai-folder-organizer

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Install in development mode
pip install -e .
```

### Configuration

**IMPORTANT**: You must configure an API key before using AI features.

#### Option 1: Environment Variable (Recommended)

```bash
export AI_FOLDER_ORG_API_KEY="your-api-key-here"
export AI_FOLDER_ORG_API_URL="https://apifreellm.com/api/v1/chat"  # Optional
export AI_FOLDER_ORG_MODEL="apifreellm"  # Optional
```

#### Option 2: Configuration File

Create a `config.json` file:

```json
{
  "api_key": "your-api-key-here",
  "api_url": "https://apifreellm.com/api/v1/chat",
  "model": "apifreellm",
  "max_retries": 3,
  "timeout_seconds": 120,
  "rate_limit_seconds": 6
}
```

### Usage

#### Command Line Interface

```bash
# Run the organizer
python cli.py

# Or use the installed command
ai-folder-organizer

# Headless mode (no GUI dialogs)
python cli.py --headless
```

#### Graphical Interface

```bash
# Run the GUI
python -m organiser.ui.gui
```

### Workflow

1. **Select Folder** - Choose the directory to organize
2. **Scan** - Tool scans and inventories all files
3. **Generate Suggestions** - AI analyzes structure and proposes reorganization
4. **Review** - Examine proposed changes in CLI or GUI
5. **Approve** - Select which actions to execute
6. **Dry Run** - Preview changes without applying them
7. **Execute** - Apply the organization changes
8. **Rollback** (if needed) - Revert changes using the manifest

## Project Structure

```
ai-folder-organizer/
├── cli.py                    # Backward-compatible CLI entry point
├── pyproject.toml           # Project metadata and dependencies
├── requirements.txt         # Runtime dependencies
├── requirements-dev.txt     # Development dependencies
├── README.md               # This file
├── LICENSE                 # MIT license
├── .gitignore             # Git ignore rules
├── organiser/             # Main package
│   ├── __init__.py        # Package exports
│   ├── config.py          # Configuration management
│   ├── scanner.py         # Folder scanning and inventory
│   ├── llm_client.py      # LLM API client (supports multiple providers)
│   ├── proposal.py        # Proposal parsing and management
│   ├── executor.py        # Action execution and rollback
│   └── ui/               # User interface modules
│       ├── __init__.py
│       ├── cli.py         # Command-line interface
│       └── gui.py         # Graphical interface
├── tests/                # Test suite
│   ├── __init__.py
│   ├── test_config.py
│   ├── test_scanner.py
│   ├── test_proposal.py
│   └── test_executor.py
└── docs/                 # Documentation
    └── ARCHITECTURE.md
```

## Configuration Reference

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `AI_FOLDER_ORG_API_KEY` | API key for LLM service | None (required) |
| `AI_FOLDER_ORG_API_URL` | API endpoint URL | `https://apifreellm.com/api/v1/chat` |
| `AI_FOLDER_ORG_MODEL` | Model name to use | `apifreellm` |
| `AI_FOLDER_ORG_MAX_RETRIES` | Maximum retry attempts | `3` |
| `AI_FOLDER_ORG_TIMEOUT` | Request timeout in seconds | `120` |
| `AI_FOLDER_ORG_RATE_LIMIT` | Delay between requests (seconds) | `6` |
| `AI_FOLDER_ORG_LOG_FILE` | Log file name | `organizer_log.json` |
| `AI_FOLDER_ORG_ROLLBACK_MANIFEST` | Rollback manifest name | `organizer_rollback_manifest.json` |

### Exclusion Patterns

By default, the following patterns are excluded from scanning:

- `appdata`, `isolatedstorage`, `temp`, `tmp`, `cache`
- `.git`, `.vscode`, `__pycache__`, `node_modules`, `.env`
- `venv`, `env`, `.pytest_cache`, `dist`, `build`, `.next`
- `launchdarkly`, `system volume information`, `$recycle.bin`

Customize via `config.exclude_patterns` or configuration file.

## Security

### API Key Security

**Never commit API keys to version control.** The project includes:

- `.gitignore` rules to exclude config files with secrets
- Environment variable support for secure key management
- Configuration validation that warns if hardcoded keys are detected

### File Operations Safety

- All operations are previewable via dry-run mode
- Rollback manifest is generated for every execution
- Conflicts are automatically resolved (duplicate filenames get `_1`, `_2` suffixes)
- Original folder structure is preserved when possible

## Development

### Setup

```bash
# Install development dependencies
pip install -r requirements-dev.txt

# Run tests
pytest

# Run with coverage
pytest --cov=organiser

# Lint code
ruff check .

# Format code
black .
ruff format .
```

### Testing

The test suite covers:

- Configuration loading and validation
- Folder scanning logic
- Proposal parsing
- Action execution and rollback

Run specific test modules:

```bash
pytest tests/test_scanner.py -v
pytest tests/test_executor.py -v
```

### Architecture

See [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) for detailed architecture documentation.

## Contributing

Contributions are welcome! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## License

MIT License - see [LICENSE](LICENSE) for details.

## Acknowledgments

- Built with Python and Tkinter
- Uses [ApiFreeLLM](https://apifreellm.com) for AI suggestions (configurable for other providers)
- Inspired by the need for intelligent, safe file organization tools

## Future Enhancements

- [ ] Support for additional LLM providers (OpenAI, Anthropic, local models)
- [ ] Plugin architecture for custom organization rules
- [ ] Batch processing for multiple folders
- [ ] Scheduling and automation
- [ ] Integration with cloud storage services
- [ ] Advanced conflict resolution strategies
- [ ] Undo/redo history (beyond single rollback)
- [ ] File type identification and intelligent categorization

---

**Note**: This is a personal/research tool. Always review AI suggestions carefully before executing file operations. The tool makes best-effort suggestions based on folder structure analysis, but human judgment is essential for important decisions.
