# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2025-06-05

### Added

- Initial release of AI Folder Organizer
- Folder scanning with project detection
- AI-powered reorganization suggestions via LLM
- Command-line interface (CLI) with interactive approval
- Graphical user interface (GUI) with visual tree preview
- Dry-run mode for safe preview of changes
- Rollback manifest for undoing operations
- Configuration management (environment variables + config file)
- Automatic conflict resolution for duplicate filenames
- Comprehensive logging of all operations
- Exclusion patterns for system folders
- Speech recognition support (optional)
- Emoji assistance for folder naming

### Core Features

- **Scanner**: Scans directories and builds file inventory
- **LLM Client**: Interfaces with ApiFreeLLM (extensible for other providers)
- **Proposal Parser**: Parses LLM responses into structured actions
- **Executor**: Executes file operations with safety features
- **CLI**: Terminal-based interactive interface
- **GUI**: Full-featured graphical interface with tabs

### Documentation

- Comprehensive README with usage examples
- Contributing guide
- Code of Conduct
- Security policy
- Architecture documentation

### Configuration

- Environment variable support for all settings
- Configuration file support (JSON)
- Defaults for all settings
- API key management (never hardcoded)

### Testing

- Unit tests for core functionality
- Test suite with pytest
- Code coverage support

### Code Quality

- Type hints throughout
- Comprehensive docstrings
- Ruff linting configuration
- Black formatting support

---

## [Unreleased]

### Planned Features

- Support for additional LLM providers (OpenAI, Anthropic, local models)
- Plugin architecture for custom organization rules
- Batch processing for multiple folders
- Scheduling and automation
- Integration with cloud storage services
- Advanced conflict resolution strategies
- Undo/redo history (beyond single rollback)

### Improvements

- Enhanced project detection algorithms
- Better handling of edge cases in file operations
- Performance improvements for large directories
- More granular exclusion patterns
- Configuration validation and error messages

---

**Note**: This is the initial release. The changelog will be maintained going forward as the project evolves.
