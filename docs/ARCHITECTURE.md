# Architecture

This document describes the architecture of AI Folder Organizer.

## Overview

AI Folder Organizer is a Python application that helps users organize their file systems using AI-powered suggestions. The application follows a modular architecture with clear separation of concerns.

```
┌─────────────────────────────────────────────────────────────────┐
│                        User Interface Layer                      │
│  ┌─────────────────┐  ┌─────────────────┐                      │
│  │   CLI (cli.py)  │  │   GUI (gui.py)  │                      │
│  └────────┬────────┘  └────────┬────────┘                      │
└───────────┼─────────────────────┼────────────────────────────────┘
            │                     │
            ▼                     ▼
┌─────────────────────────────────────────────────────────────────┐
│                      Business Logic Layer                        │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐            │
│  │   Scanner   │  │   LLM       │  │  Executor   │            │
│  │  (scanner)  │  │  Client     │  │ (executor)  │            │
│  └─────────────┘  └─────────────┘  └─────────────┘            │
│  ┌─────────────┐  ┌─────────────┐                              │
│  │  Proposal   │  │   Config    │                              │
│  │ (proposal)  │  │  (config)   │                              │
│  └─────────────┘  └─────────────┘                              │
└─────────────────────────────────────────────────────────────────┘
            │
            ▼
┌─────────────────────────────────────────────────────────────────┐
│                        Data Layer                                │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐   │
│  │   File      │  │   LLM       │  │   Logs &            │   │
│  │   System    │  │   APIs      │  │   Manifests         │   │
│  └─────────────┘  └─────────────┘  └─────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
```

## Core Modules

### 1. Configuration (`organiser/config.py`)

**Purpose**: Manages application configuration from multiple sources.

**Responsibilities**:
- Load configuration from environment variables
- Load configuration from JSON files
- Provide defaults for all settings
- Validate configuration values

**Key Classes**:
- `Config`: Dataclass holding all configuration options
- `load_config()`: Factory function for loading configuration

**Design Decisions**:
- Environment variables take priority over config files
- No hardcoded secrets (API keys must come from env or config file)
- Immutable configuration after loading

### 2. Scanner (`organiser/scanner.py`)

**Purpose**: Scans directories and builds comprehensive file inventories.

**Responsibilities**:
- Recursively scan directory trees
- Detect project structures
- Build file statistics and counts
- Identify loose files in root directories
- Exclude system/cached folders

**Key Classes**:
- `FileInfo`: Data class for file metadata
- `FolderStructure`: Complete scan results
- `FolderScanner`: Main scanning class

**Design Decisions**:
- Generator-based scanning for memory efficiency
- Configurable exclusion patterns
- Project detection based on common indicator files
- Handles permission errors gracefully

### 3. LLM Client (`organiser/llm_client.py`)

**Purpose**: Interfaces with LLM APIs to generate organization suggestions.

**Responsibilities**:
- Abstract interface for different LLM providers
- Request construction and sending
- Response parsing
- Retry logic with rate limiting
- Error handling and reporting

**Key Classes**:
- `LLMClient`: Abstract base class
- `ApiFreeLLMClient`: Implementation for ApiFreeLLM
- `MockLLMClient`: Test implementation
- `LLMClientError`: Exception type for client errors

**Design Decisions**:
- Abstract base class for extensibility
- Retry logic with exponential backoff (configurable)
- Rate limiting between requests
- Support for mock client in testing

### 4. Proposal (`organiser/proposal.py`)

**Purpose**: Parses and manages organization proposals from LLMs.

**Responsibilities**:
- Build prompts for LLMs
- Extract JSON from LLM responses
- Parse proposal data into structured format
- Provide access to action metadata (confidence, explanations)

**Key Classes**:
- `Action`: Single organization action
- `Proposal`: Complete organization proposal

**Design Decisions**:
- Supports multiple JSON formats from LLM responses
- Flexible metadata structure (dict or list)
- Action IDs for tracking and referencing

### 5. Executor (`organiser/executor.py`)

**Purpose**: Executes file operations with safety features.

**Responsibilities**:
- Execute actions (create folder, move, rename)
- Dry-run mode (simulation)
- Conflict resolution for duplicate files
- Rollback manifest generation
- Comprehensive logging

**Key Classes**:
- `ActionExecutor`: Main execution engine
- `ExecutionLog`: Log entry for actions
- `RollbackEntry`: Entry for rollback manifest

**Design Decisions**:
- Dry-run mode for safe preview
- Automatic conflict resolution (counter suffixes)
- Rollback manifest for reversibility
- Comprehensive error handling and logging

### 6. User Interface

#### CLI (`organiser/ui/cli.py`)

**Purpose**: Terminal-based interactive interface.

**Features**:
- Interactive folder selection (GUI dialog or CLI input)
- Text-based proposal display
- Multiple approval modes (all, individual, GUI)
- Dry-run and execution workflow

**Design Decisions**:
- Uses tqdm for progress indication
- Supports headless mode for automation
- Flow control for interactive approval

#### GUI (`organiser/ui/gui.py`)

**Purpose**: Full-featured graphical interface.

**Features**:
- Tabbed interface for workflow steps
- Visual tree preview
- Action list with approval controls
- Speech recognition input (optional)
- Emoji assistance for naming
- Execution logs and status

**Design Decisions**:
- Tkinter for cross-platform compatibility
- Tab-based workflow matching CLI flow
- Optional features (speech) gracefully degrade

## Data Flow

### Typical Workflow

1. **Initialization**
   ```
   User → CLI/GUI → load_config() → Config object
   ```

2. **Scanning**
   ```
   User selects folder → FolderScanner.scan() → FolderStructure
   ```

3. **Summary Building**
   ```
   FolderStructure → summary dict → LLM prompt
   ```

4. **AI Suggestion**
   ```
   Prompt → LLMClient.generate_response() → Raw text
   Raw text → parseproposal() → Proposal
   ```

5. **Review & Approval**
   ```
   Proposal → UI display → User approval → Approved actions
   ```

6. **Execution**
   ```
   Approved actions → ActionExecutor → File operations
   File operations → Logs + Rollback manifest
   ```

7. **Rollback** (if needed)
   ```
   Rollback manifest → rollback() → File system restore
   ```

## Extension Points

### Adding a New LLM Provider

1. Create new class inheriting from `LLMClient`
2. Implement `generate_response()` method
3. Add to `create_client()` factory
4. Add configuration options as needed

Example:
```python
class OpenAIClient(LLMClient):
    def generate_response(self, prompt: str) -> str:
        # Implementation
        pass

# In create_client():
clients = {
    "apifreellm": ApiFreeLLMClient,
    "openai": OpenAIClient,
    "mock": MockLLMClient,
}
```

### Adding Custom Organization Rules

The proposal system is designed to be extensible. Custom rules could:

1. Analyze folder structure
2. Generate custom action proposals
3. Integrate with the existing approval/execution flow

### Plugins

Future plugin architecture could allow:
- Custom scanners
- Custom proposal generators
- Custom action types
- Custom UI components

## Performance Considerations

### Scanning
- Uses `os.walk()` for efficient directory traversal
- Excludes unwanted folders early to reduce work
- File metadata is lazy-loaded where possible

### LLM Calls
- Rate limiting to respect API constraints
- Retry logic with backoff for reliability
- Timeout handling to prevent hangs

### File Operations
- Batch operations where possible
- Conflict resolution is O(n) where n is number of conflicts
- Rollback manifest is written incrementally

## Error Handling

### Strategy
- Fail fast with clear error messages
- Graceful degradation where possible
- Comprehensive logging for debugging
- User-friendly error messages in UI

### Error Categories
1. **Configuration errors**: Missing API key, invalid settings
2. **Scan errors**: Permission denied, missing folders
3. **API errors**: Network issues, rate limits, invalid responses
4. **Parse errors**: Invalid JSON from LLM
5. **Execution errors**: File not found, permission denied, conflicts

Each category is handled appropriately at the right layer.

## Testing Strategy

### Unit Tests
- Test individual functions and classes in isolation
- Mock external dependencies (LLM APIs, file system)
- Focus on business logic

### Integration Tests
- Test complete workflows
- Use temporary directories for file operations
- Test with mock LLM responses

### Test Categories
- `test_config.py`: Configuration loading and validation
- `test_scanner.py`: Folder scanning logic
- `test_proposal.py`: Proposal parsing
- `test_executor.py`: Action execution and rollback

## Security Architecture

### API Key Management
- Never stored in source code
- Loaded from environment or config file
- Config files with secrets should be gitignored

### File Operation Safety
- All operations are previewable
- Rollback manifest created for every execution
- Conflicts resolved safely
- Original paths preserved in manifest

### Data Privacy
- Folder structure sent to LLM APIs (be aware of what's included)
- Logs stored locally
- No telemetry or data collection

## Future Architecture Considerations

### Plugin System
- Define plugin interfaces
- Plugin discovery and loading
- Plugin configuration and management

### Async Operations
- Consider asyncio for I/O-bound operations
- Concurrent file operations (with care)
- Async LLM client support

### Distribution
- Package as installable Python package
- Consider standalone executable (PyInstaller)
- Consider web interface option
