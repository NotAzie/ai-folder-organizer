# TODO

This document tracks ongoing work and future improvements for AI Folder Organizer.

## High Priority

### Security & Configuration
- [ ] Add configuration validation with clear error messages
- [ ] Add warnings for common misconfigurations
- [ ] Improve API key security documentation
- [ ] Add config file template with examples

### Testing
- [ ] Add integration tests for full workflow
- [ ] Add tests for GUI components
- [ ] Add tests for different LLM provider responses
- [ ] Add performance tests for large directories

### User Experience
- [ ] Better error messages for common failures
- [ ] Progress indicator for long operations
- [ ] Undo last operation (beyond rollback manifest)
- [ ] Confirmation dialogs for destructive operations

## Medium Priority

### LLM Provider Support
- [ ] OpenAI API client
- [ ] Anthropic API client
- [ ] Local model support (Ollama)
- [ ] Provider abstraction and fallback
- [ ] Model capability detection

### Organization Features
- [ ] Custom organization rule plugins
- [ ] File type categorization improvements
- [ ] Date-based organization (by year/month)
- [ ] Size-based organization
- [ ] Duplicate file detection
- [ ] Empty folder cleanup suggestions

### GUI Improvements
- [ ] Better preview of proposed structure
- [ ] Drag-and-drop action reordering
- [ ] Action filtering and search
- [ ] Batch approve/reject by pattern
- [ ] Dark mode support

### CLI Improvements
- [ ] Command-line arguments for non-interactive use
- [ ] Output formats (JSON, CSV) for automation
- [ ] Command aliases and shortcuts
- [ ] Better progress reporting

## Low Priority

### Advanced Features
- [ ] Scheduled organization runs
- [ ] Folder watching for automatic organization
- [ ] Cloud storage integration
- [ ] Archive file handling
- [ ] Media file organization (photos by date, etc.)
- [ ] Storage analysis and reports

### Developer Experience
- [ ] Pre-commit hooks
- [ ] CI/CD pipeline (GitHub Actions)
- [ ] Code coverage reporting
- [ ] API documentation (if exposing as library)
- [ ] Example configurations
- [ ] Sample organization templates

### Documentation
- [ ] Video tutorials
- [ ] Troubleshooting guide
- [ ] Best practices guide
- [ ] Migration guide for different providers
- [ ] Performance optimization guide

## Completed

- [x] Initial project structure
- [x] Folder scanner
- [x] LLM client (ApiFreeLLM)
- [x] Proposal parsing
- [x] Action executor with rollback
- [x] CLI interface
- [x] GUI interface
- [x] Configuration management
- [x] Basic test suite
- [x] README documentation
- [x] CONTRIBUTING guide
- [x] Code of Conduct
- [x] Security policy
- [x] Changelog
- [x] Roadmap
- [x] Type hints
- [x] Docstrings

---

**Note**: This TODO is not exhaustive. Community contributions and feature requests may add additional items.
