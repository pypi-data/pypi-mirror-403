# Framework M

A modern, metadata-driven business application framework in Python 3.12+.

[![Python 3.12+](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/downloads/)
[![PyPI version](https://badge.fury.io/py/framework-m.svg)](https://badge.fury.io/py/framework-m)
[![GitLab Pipeline Status](https://gitlab.com/castlecraft/framework-m/badges/main/pipeline.svg)](https://gitlab.com/castlecraft/framework-m/-/pipelines)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Code style: ruff](https://img.shields.io/badge/code%20style-ruff-000000.svg)](https://github.com/astral-sh/ruff)
[![Type checked: mypy](https://img.shields.io/badge/type%20checked-mypy-blue.svg)](https://mypy-lang.org/)

## Overview

Framework M is inspired by [Frappe Framework](https://frappeframework.com/) but built from scratch with modern Python practices:

- **Hexagonal Architecture**: Clean separation via Ports & Adapters
- **Async-First**: Native asyncio with Litestar and SQLAlchemy
- **Type-Safe**: 100% type hints, mypy strict compatible
- **Stateless**: JWT/Token auth, no server-side sessions
- **Metadata-Driven**: Define DocTypes as Pydantic models

## Installation

```bash
pip install framework-m
```

Or with `uv`:

```bash
uv add framework-m
```

## Quick Start

### 1. Define a DocType

```python
from framework_m import DocType, Field

class Todo(DocType):
    """A simple task document."""

    title: str = Field(description="Task title")
    description: str | None = Field(default=None, description="Task details")
    is_completed: bool = Field(default=False, description="Completion status")
    priority: int = Field(default=1, ge=1, le=5, description="Priority (1-5)")
```

### 2. Use the CLI

```bash
# Show version
m --version

# Show framework info
m info

# Start development server (coming soon)
m start
```

## Features

### Metadata-Driven DocTypes

DocTypes are Pydantic models with automatic:
- Database table generation
- REST API endpoints
- JSON Schema for frontends
- Validation and serialization

### Hexagonal Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     Primary Adapters                        │
│         (HTTP API, CLI, WebSocket, Background Jobs)         │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                      Core Domain                            │
│              (DocTypes, Controllers, Business Logic)        │
│                                                             │
│  ┌─────────────┐  ┌───────────────┐  ┌──────────────┐       │
│  │ BaseDocType │  │ BaseController│  │ MetaRegistry │       │
│  └─────────────┘  └───────────────┘  └──────────────┘       │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                    Ports (Interfaces)                       │
│  RepositoryProtocol │ EventBusProtocol │ PermissionProtocol │
│  StorageProtocol    │ JobQueueProtocol │ CacheProtocol      │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                   Secondary Adapters                        │
│     (PostgreSQL, Redis, S3, SMTP, External APIs)            │
└─────────────────────────────────────────────────────────────┘
```

### Built-in Protocols

| Protocol | Purpose |
|----------|---------|
| `RepositoryProtocol` | CRUD operations for documents |
| `EventBusProtocol` | Publish/subscribe events |
| `PermissionProtocol` | Authorization with RLS |
| `StorageProtocol` | File storage abstraction |
| `JobQueueProtocol` | Background job processing |
| `CacheProtocol` | Caching layer |
| `NotificationProtocol` | Email/SMS notifications |
| `SearchProtocol` | Full-text search |
| `PrintProtocol` | PDF generation |
| `I18nProtocol` | Internationalization |

### Extensibility

Override any adapter via Python entrypoints:

```toml
# pyproject.toml
[project.entry-points."framework_m.overrides"]
repository = "my_app.adapters:CustomRepository"
```

## Technology Stack

- **Web Framework**: [Litestar](https://litestar.dev/) 2.0+
- **ORM**: [SQLAlchemy](https://www.sqlalchemy.org/) 2.0 (Async)
- **Validation**: [Pydantic](https://docs.pydantic.dev/) V2
- **Task Queue**: [Taskiq](https://taskiq-python.github.io/) + NATS JetStream
- **DI Container**: [dependency-injector](https://python-dependency-injector.ets-labs.org/)
- **Database**: PostgreSQL (default), SQLite (testing)
- **Cache/Events**: Redis

## Project Structure

```
libs/framework-m/
├── src/framework_m/
│   ├── core/
│   │   ├── domain/         # DocType, Controller, Mixins
│   │   └── interfaces/     # Protocol definitions (Ports)
│   ├── adapters/           # Infrastructure implementations
│   ├── cli/                # CLI commands
│   └── public/             # Built-in DocTypes
└── tests/
```

## Development

```bash
# Clone and setup
git clone https://gitlab.com/castlecraft/framework-m.git
cd framework-m

# Install dependencies
uv sync --all-extras

# Run tests
uv run pytest

# Type checking
uv run mypy src/framework_m --strict

# Linting
uv run ruff check .
uv run ruff format .
```

## Documentation

- [Architecture Overview](https://gitlab.com/castlecraft/framework-m/blob/main/ARCHITECTURE.md)
- [Contributing Guide](https://gitlab.com/castlecraft/framework-m/blob/main/CONTRIBUTING.md)
- [Phase Checklists](https://gitlab.com/castlecraft/framework-m/tree/main/checklists)

## License

MIT License - see [LICENSE](https://gitlab.com/castlecraft/framework-m/blob/main/LICENSE) for details.

## Acknowledgments

Inspired by [Frappe Framework](https://frappeframework.com/), reimagined with:
- Modern Python (3.12+, async/await, type hints)
- Clean architecture (Hexagonal/Ports & Adapters)
- No global state (Dependency Injection)
- Code-first schemas (Pydantic, not database JSON)
