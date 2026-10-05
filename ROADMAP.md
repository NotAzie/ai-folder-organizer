# Roadmap

This document outlines the planned direction for AI Folder Organizer.

## Vision

AI Folder Organizer is a tool that uses artificial intelligence to help users organize their file systems safely and efficiently. The goal is to provide intelligent, safe, and user-controlled file organization that respects user intent while leveraging AI capabilities.

## Guiding Principles

1. **Safety First**: All operations are previewable and reversible
2. **User Control**: Users approve every action before execution
3. **Extensibility**: Architecture supports multiple LLM providers and customization
4. **Transparency**: Clear logs and explanations for all operations
5. **Cross-Platform**: Works on Windows, macOS, and Linux

## Phase 1: Foundation (Current - Version 1.0)

**Status**: Released

- [x] Core folder scanning and inventory
- [x] AI-powered suggestion generation
- [x] CLI interface with interactive approval
- [x] GUI interface with visual preview
- [x] Dry-run mode
- [x] Rollback support
- [x] Configuration management
- [x] Basic test suite
- [x] Documentation

**Goals**:
- Stable, usable tool for personal file organization
- Clean, maintainable codebase
- Good documentation for users and contributors

## Phase 2: Provider Expansion

**Target**: Version 1.1 - 1.2

### Multiple LLM Providers
- [ ] OpenAI GPT integration
- [ ] Anthropic Claude integration
- [ ] Local model support (Ollama, LM Studio)
- [ ] Provider abstraction layer
- [ ] Provider comparison/feature detection

### Enhanced Organization
- [ ] Custom organization rules/plugins
- [ ] File type-based categorization
- [ ] Date-based organization options
- [ ] Size-based organization options
- [ ] User-defined category templates

### User Experience
- [ ] Batch processing for multiple folders
- [ ] Organization presets/templates
- [ ] Undo/redo history (beyond single rollback)
- [ ] Progress tracking for large operations
- [ ] Better conflict resolution options

## Phase 3: Automation & Integration

**Target**: Version 2.0

### Automation
- [ ] Scheduled organization runs
- [ ] Watch folders for automatic organization
- [ ] Command-line automation-friendly mode
- [ ] Integration with file managers

### Integration
- [ ] Cloud storage integration (Google Drive, Dropbox, OneDrive)
- [ ] Network drive support
- [ ] Archive handling (ZIP, RAR, TAR)
- [ ] Media file organization (photos, videos, music)

### Advanced Features
- [ ] Machine learning for personalized organization
- [ ] Learning from user corrections
- [ ] Intelligent duplicate detection
- [ ] File cleanup suggestions (temporary files, duplicates)
- [ ] Storage analysis and recommendations

## Phase 4: Enterprise & Collaboration

**Target**: Future releases

### Collaboration
- [ ] Shared organization rules
- [ ] Team-based templates
- [ ] Organization policy enforcement
- [ ] Audit logs for compliance

### Enterprise Features
- [ ] Centralized configuration management
- [ ] Integration with enterprise auth systems
- [ ] Bulk operations API
- [ ] Reporting and analytics
- [ ] Compliance features (data retention, PII detection)

## Contributing to the Roadmap

This roadmap represents the maintainers' vision for the project. Community input is welcome!

To suggest changes or additions:
1. Open an issue with the "enhancement" label
2. Describe the feature and its use case
3. Explain how it aligns with project goals
4. Be open to discussion and refinement

**Note**: This roadmap is a living document and may change based on community needs, technical feasibility, and maintenance capacity.

---

**Current Version**: 1.0.0  
**Next Target**: Multiple LLM provider support and enhanced organization options
