# Configuration

This section describes how to configure `django-simple-dms`.

## Required Configuration

### Database Configuration

`django-simple-dms` requires PostgreSQL as it uses PostgreSQL-specific features:

```python
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'your_database_name',
        'USER': 'your_database_user',
        'PASSWORD': 'your_database_password',
        'HOST': 'localhost',
        'PORT': '5432',
    }
}
```

### INSTALLED_APPS

Add `django_simple_dms` to your `INSTALLED_APPS`:

```python
INSTALLED_APPS = [
    ...
    'django_simple_dms',
    ...
]
```

## File Storage Configuration

### Storage Backend

By default, the `document` FileField on the `Document` model uses Django's default storage backend. You can configure a custom storage backend by setting `DMS_DOCUMENT_STORAGE` in your Django settings:

```python
# settings.py

# Option 1: Dotted path to a storage class (will be instantiated automatically)
DMS_DOCUMENT_STORAGE = 'storages.backends.s3boto3.S3Boto3Storage'

# Option 2: Callable that returns a storage instance (for custom configuration)
DMS_DOCUMENT_STORAGE = lambda: S3Boto3Storage(bucket_name='my-documents')

# Option 3: Pre-configured storage instance
from storages.backends.s3boto3 import S3Boto3Storage
DMS_DOCUMENT_STORAGE = S3Boto3Storage(bucket_name='my-documents')
```

If `DMS_DOCUMENT_STORAGE` is not set, Django's default storage will be used (typically `FileSystemStorage` saving to `MEDIA_ROOT`).

### Upload Path

By default, documents are uploaded to `documents/%Y/%m/%d` (e.g., `documents/2024/03/15/`). This is configured in the `Document` model's FileField:

```python
document = models.FileField(upload_to='documents/%Y/%m/%d')
```

### Customizing Upload Path

To customize the upload path, you can override the `Document` model or configure Django's media settings:

```python
# settings.py
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')
MEDIA_URL = '/media/'
```

### Custom Upload Path Function

If you need more control over file upload paths, you can extend the `Document` model and provide a custom `upload_to` callable:

```python
from django_simple_dms.models import Document as BaseDocument

def custom_upload_to(instance, filename):
    # Custom logic here
    # Example: organize by admin user
    if instance.admin:
        return f'documents/{instance.admin.username}/{filename}'
    return f'documents/unassigned/{filename}'

class Document(BaseDocument):
    document = models.FileField(upload_to=custom_upload_to)

    class Meta:
        proxy = True  # Use proxy model if you don't want to alter DB schema
```

## User Model Configuration

`django-simple-dms` uses Django's configurable user model system via `get_user_model()`. If you're using a custom user model, ensure it's properly configured:

```python
# settings.py
AUTH_USER_MODEL = 'myapp.CustomUser'
```

## Admin Configuration

The Django admin integration is automatically registered when you add `django_simple_dms` to `INSTALLED_APPS`. No additional configuration is needed.

### Customizing Admin

To customize the admin interface, you can unregister the default admin and register your own:

```python
# admin.py
from django.contrib import admin
from django_simple_dms.models import Document, DocumentTag
from django_simple_dms.admin import DocumentAdmin, DocumentTagAdmin

# Unregister default
admin.site.unregister(Document)

# Register custom
@admin.register(Document)
class CustomDocumentAdmin(DocumentAdmin):
    list_display = ('document', 'admin', 'upload_date', 'reference_period', 'custom_field')
    # Add your customizations
```

## Security Considerations

### Permission Validation

The permission system is enforced at the model level. When using `Document.add()`, permission checks are automatically performed. However, if you're creating documents directly via the ORM, you should manually check permissions:

```python
from django_simple_dms.models import Document, TagGrant
from django_simple_dms.exceptions import ForbiddenException

# Check if user can create with tags
check_result = TagGrant.objects.check_create(user, tags=['sensitive.data'])
if isinstance(check_result, CreationCheckFail):
    raise ForbiddenException(f"Cannot create with tags: {check_result.tags}")
```

### Superuser Bypass

Superusers automatically bypass all permission checks. Be mindful when granting superuser status:

```python
# Superusers always pass permission checks
if user.is_superuser:
    # No TagGrant checks performed
    doc = Document.add(document=file, actor=user, tags=any_tags)
```

## PostgreSQL Version Considerations

### Django 5.0+ with PostgreSQL 15+

With Django 5.0+ and PostgreSQL 15+, unique constraints use `nulls_distinct=False`, meaning NULL values are treated as equal for uniqueness:

```python
# Django 5.0+
constraints = [
    UniqueConstraint(
        name='unique_doc_grant',
        fields=['grantor', 'user', 'group', 'document'],
        nulls_distinct=False
    )
]
```

### Earlier Versions

For Django < 5.0 or PostgreSQL < 15, uniqueness with NULL values is enforced programmatically in the model's `save()` method.

## Development Settings Example

Here's a complete example for development:

```python
# settings.py

DEBUG = True

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django_simple_dms',
]

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'dms_dev',
        'USER': 'postgres',
        'PASSWORD': 'postgres',
        'HOST': 'localhost',
        'PORT': '5432',
    }
}

MEDIA_ROOT = os.path.join(BASE_DIR, 'media')
MEDIA_URL = '/media/'

# Use default settings or customize as needed
```
