# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

### Development Setup
```bash
# Install all dependencies
poetry install

# Install with specific LLM provider extras
poetry install --extras "anthropic aws gemini vertex ollama litellm mongo"

# Install development dependencies
poetry install --with dev
```

### Code Quality
```bash
# Run both linting and type checking
python scripts/lint.py --ruff --mypy

# Format code
ruff format

# Check linting issues
ruff check

# Type checking
mypy
```

### Testing
```bash
# Run all tests
pytest

# Run tests with coverage
pytest --cov

# Run tests in parallel
pytest -n auto

# Run specific test file
pytest tests/path/to/test_file.py

# Run with timing analysis
pytest --timing
```

### Running the Application
```bash
# Start the server
parlant-server

# CLI commands
parlant [command]

# Database migrations
parlant-prepare-migration
```

## Architecture Overview

Parlant is an AI agent framework for building customer-facing conversational agents with guaranteed rule compliance. It uses an "Agentic Behavior Modeling Engine" approach that ensures agents follow behavioral guidelines through structured rule matching rather than relying solely on prompts.

### Core Architecture Pattern
The codebase follows a modular, engine-based architecture with clear separation of concerns:

- **Engine System**: The `AlphaEngine` (`src/parlant/core/engines/alpha/`) is the central processing unit that handles all conversation logic, guideline matching, and tool execution.

- **Domain Modules**: Each business domain (agents, customers, guidelines, sessions, journeys) has its own application module with dependency injection configuration, located in `src/parlant/app_modules/`.

- **Adapter Pattern**: External integrations (LLM providers, databases, vector stores) use adapters in `src/parlant/adapters/` for clean abstraction.

- **SDK Layer**: The main entry point is `src/parlant/sdk.py` which provides a high-level API for all operations.

### Key Architectural Components

1. **Behavioral Guidelines System**: Natural language rules in `core/guidelines/` that agents follow contextually, with matching algorithms and traceability.

2. **Journey-Based Interactions**: Structured customer interaction flows managed through the journey system.

3. **Tool Integration**: External API/service integrations with specific behavioral guidelines, managed through the tools system.

4. **Event System**: Event emission throughout the conversation processing for observability and debugging.

5. **Persistence Layer**: Repository pattern with `*Store` classes for business logic and `*DocumentStore` classes for data persistence.

### Code Organization Patterns

- **Async-First**: All I/O operations use `async/await`. Custom async utilities are in `core/async_utils.py`.

- **Dependency Injection**: Uses Lagom container. Each domain module defines its DI configuration.

- **Strongly Typed IDs**: Domain entities use typed IDs like `AgentId`, `CustomerId`, `GuidelineId`.

- **Testing**: BDD tests using pytest-bdd. Test features are in `tests/` directory with comprehensive async test support.

### Important Conventions

- **File Naming**: Use snake_case for Python files and modules
- **Class Naming**: Domain entities use singular nouns (Agent, Customer, Guideline)
- **Store Classes**: `*Store` for business logic, `*DocumentStore` for persistence, `*VectorStore` for embeddings
- **Module Naming**: Application modules use singular form (AgentModule, not AgentsModule)
- **Line Length**: Maximum 100 characters (configured in ruff.toml)
- **Type Hints**: Strict typing enforced via mypy with namespace packages enabled

### Configuration Files

- `ruff.toml`: Linting configuration with Python 3.12 target
- `mypy.ini`: Type checking with strict mode enabled
- `pytest.ini`: Test configuration with async mode and BDD features
- `pyproject.toml`: Poetry project configuration and dependencies