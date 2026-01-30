# django-virtualqueryset

Django library for creating QuerySet-like objects that are not backed by a database.

This is a minimal Django library ready for migration of existing tools.

## Purpose

Create virtual QuerySets for:
- Data from external APIs
- In-memory computed data
- Configuration/settings as models
- Read-only models without database tables

## Installation

```bash
pip install django-virtualqueryset
```

## Quick Start

```python
INSTALLED_APPS = [
    ...
    'virtualqueryset',
]
```

## Development

```bash
python dev.py venv
python dev.py install-dev
python dev.py migrate
python dev.py test
```

## License

MIT

