# DDDify

A code generator for Domain-Driven Design (DDD) project structures in Python with Clean Architecture principles.

## Installation

Install globally using `uv`:

```bash
uv tool install dddify
```

Or install from source:

```bash
git clone https://github.com/yourusername/dddify.git
cd dddify
pip install -e .
```

## Quick Start

Generate a new domain structure:

```bash
dddify generate "Order Management" "Order"
```

Short form:

```bash
dddify g "Order Management" "Order"
```

For help:

```bash
dddify --help
```

## Configuration

Create a `dddify.toml` file in your project root:

```toml
[dddify]
output_dir = "backend/domains"
```

Or add to your `pyproject.toml`:

```toml
[tool.dddify]
output_dir = "backend/domains"
```

### Configuration Options

- `output_dir`: Target directory for generated domains (default: `"."`)

## Usage

### Basic Command

```bash
dddify generate <domain_name> [entity_name] [options]
```

**Arguments:**
- `domain_name`: Name of the domain (e.g., "Order Management")
- `entity_name`: Name of the entity (optional, defaults to domain name)

**Options:**
- `-o, --output`: Output directory (overrides config file)

### Examples

Generate with default config:

```bash
dddify g "User Management" "User"
```

Generate with custom output directory:

```bash
dddify g "Product Catalog" "Product" -o ./src/domains
```

## Generated Structure

DDDify generates a complete DDD structure following Clean Architecture:

```
order_management/
├── domain/
│   ├── aggregate.py          # Aggregate root with domain events
│   ├── events.py              # Domain event base class
│   ├── value_objects.py       # Value object definitions
│   ├── exceptions.py          # Domain-specific exceptions
│   ├── repo.py                # Repository interface (ABC)
│   ├── ports.py               # External system interfaces
│   ├── __init__.py            # Domain exports
│   └── entities/
│       └── __init__.py
├── application/
│   ├── commands/
│   │   └── __init__.py
│   ├── queries/
│   │   └── __init__.py
│   └── __init__.py
├── infrastructure/
│   ├── persistence/
│   │   ├── orm.py             # SQLAlchemy ORM model
│   │   ├── repository.py      # Repository implementation
│   │   └── __init__.py
│   ├── adapters/
│   │   └── __init__.py
│   └── di/
│       ├── container.py       # Dishka DI container
│       └── __init__.py
└── presentation/
    ├── router.py              # FastAPI router
    ├── schemas.py             # Pydantic schemas
    ├── exception_handlers.py  # FastAPI exception handlers
    └── __init__.py
```

## Features

- **Clean Architecture**: Strict separation of concerns across layers
- **Domain-Driven Design**: Aggregates, entities, value objects, domain events
- **Async-First**: AsyncSession for SQLAlchemy, async repository pattern
- **Modern Python**: Type hints, `|` union syntax, UUID primary keys
- **Dependency Injection**: Dishka container with REQUEST scope
- **FastAPI Ready**: Router, schemas, and exception handlers included
- **Absolute Imports**: Automatically calculated based on output directory

## Architecture Layers

### Domain Layer
- **Aggregate**: Entity with identity, domain events, and business logic
- **Events**: Immutable domain events for event sourcing
- **Repository Interface**: Abstract contract for data access
- **Exceptions**: Domain-specific error hierarchy
- **Ports**: Interfaces for external systems

### Application Layer
- **Commands**: Write operations (CQRS pattern)
- **Queries**: Read operations (CQRS pattern)

### Infrastructure Layer
- **Persistence**: SQLAlchemy ORM models and repository implementation
- **Adapters**: External service adapters
- **DI Container**: Dishka provider for dependency injection

### Presentation Layer
- **Router**: FastAPI endpoints with UUID parameters
- **Schemas**: Pydantic models for request/response
- **Exception Handlers**: HTTP exception mapping

## Technology Stack

- **FastAPI**: Web framework
- **SQLAlchemy**: ORM with async support
- **Pydantic**: Data validation
- **Dishka**: Dependency injection
- **UUID**: Unique identifiers
- **Python 3.11+**: Modern type hints

## License

MIT
