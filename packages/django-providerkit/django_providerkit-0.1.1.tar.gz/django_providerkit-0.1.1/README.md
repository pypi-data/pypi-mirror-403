# django-providerkit

Django integration for ProviderKit. Provides Django admin integration and utilities for managing providers in Django applications.

## Purpose

Integrate ProviderKit providers into Django applications with Django admin interface and virtual models.

## Installation

```bash
pip install django-providerkit
```

## Quick Start

```python
INSTALLED_APPS = [
    ...
    'djproviderkit',
]
```

## Features

- **Django admin integration**: Display and manage providers in Django admin
- **Virtual models**: Represent providers without database tables using VirtualQuerySet
- **ProviderKit integration**: Use ProviderKit's provider discovery and management
- **Field mapping**: Automatic mapping of ProviderKit fields to Django model fields

## Development

```bash
./service.py dev install-dev
./service.py dev test
```

## License

MIT
