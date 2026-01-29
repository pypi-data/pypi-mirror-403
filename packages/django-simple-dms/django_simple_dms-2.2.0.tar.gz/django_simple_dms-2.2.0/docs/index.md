# Welcome to django-simple-dms

`django-simple-dms` is a Django library for simple document management with granular permission control.

It provides a simple way to manage documents with a flexible metadata system based on hierarchical tags and comprehensive permission management.

## Compatibility

- **Python**: 3.10, 3.11, 3.12, 3.13, 3.14
- **Django**: 3.2, 4.2, 5.2
- **Database**: PostgreSQL (required for ArrayField and DateRangeField support)

## Features

* **Document Management**: Store and manage documents with automatic file handling
* **Hierarchical Tags**: Flexible document classification using dot-separated hierarchical tags (e.g., `invoices.2024.january`)
* **Permission System**: Granular permission control with Read, Update, Delete, and Share (RUDS) permissions
* **Tag Grants**: Control document creation permissions based on tags
* **Document Grants**: Fine-grained permissions for individual documents assigned to users or groups
* **Reference Period**: Associate documents with date ranges for time-based organization
* **Import/Export**: Abstract `Importer` class for batch document imports with atomic transactions
* **Admin Interface**: Ready-to-use Django admin integration with inline grant management
* **Multiple File Types**: Support for various file input types (path strings, Path objects, file handles, uploaded files)

## Installation

To install `django-simple-dms`, run the following command:

```bash
pip install django-simple-dms
```

## Requirements

This package requires PostgreSQL as it uses PostgreSQL-specific fields:
- `ArrayField` for storing permission lists
- `DateRangeField` for reference periods

## Quick Start

1. Add `django_simple_dms` to your `INSTALLED_APPS` setting like this:

```python
INSTALLED_APPS = [
    ...
    'django_simple_dms',
]
```

2. Ensure you have PostgreSQL configured in your `DATABASES` setting:

```python
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        ...
    }
}
```

3. Run `python manage.py migrate` to create the `django-simple-dms` models.

4. Start the development server and visit http://127.0.0.1:8000/admin/ to create documents and configure permissions.

## Demo

A demo Django application is provided in the `tests/demo` folder.

To set it up run once `python manage.py demo`

To run the demo server: `python manage.py runserver` and go to http://127.0.0.1:8000/

You can test the API with [httpie](https://httpie.io/) (provided by the development dependencies).

## Basic Usage

### Creating a Document

```python
from django_simple_dms.models import Document

# Simple document creation (requires superuser or appropriate tag grants)
doc = Document.add(
    document='/path/to/file.pdf',
    actor=request.user,
    admin=request.user,
    tags=['invoices.2024']
)
```

### Managing Tags

```python
from django_simple_dms.models import DocumentTag

# Create hierarchical tags
tag = DocumentTag.objects.create(title='projects.client-a.2024')
```

### Setting Permissions

```python
from django_simple_dms.models import DocumentGrant, TagGrant

# Grant read and update permissions to a user
DocumentGrant.objects.create(
    document=doc,
    user=user,
    granted_permissions=['R', 'U'],
    grantor=admin_user
)

# Allow a group to create documents with a specific tag
TagGrant.objects.create(
    tag=tag,
    group=group,
    create=True,
    defaults=['R', 'U'],
    grantor=admin_user
)
```
